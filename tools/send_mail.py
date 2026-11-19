#!/usr/bin/env python3
"""E-Mail-Versand und Antwortprüfung für den Bewerbungshelfer (nur Python-Standardbibliothek).

Regel `send.batch` in references/applications.md: gesendet wird nur stapelweise, nach ausdrücklicher
Freigabe des Nutzers für genau diesen Stapel. Das Skript enthält keine persönlichen Daten. Absender ist
`person.email` aus dem Profil; Zugangsdaten liegen außerhalb des Repos unter
~/.config/bewerbungs-helfer/ (mail.json und mail.password, nur für den Nutzer lesbar).

Befehle:
  setup --user <apple-id-adresse> --password-file <datei>
      Speichert Benutzername und App-spezifisches Passwort (Datei wird gelesen, nicht verschoben).
  check
      Meldet sich bei SMTP und IMAP an, sendet nichts.
  preview <stellenordner>…
      Zeigt je Stelle Empfänger, Betreff, Anhang und Prüfergebnis. Sendet nichts.
  test <stellenordner> [--to <adresse>]
      Sendet die E-Mail dieser Stelle an den Absender selbst (oder --to), Betreff mit „[TEST]“.
      Kein Ledger-Eintrag.
  send <stellenordner>… --yes [--delay SEKUNDEN] [--again] [--to <adresse>]
      Sendet den freigegebenen Stapel. Ohne --yes nur Vorschau. Je Stelle: Senden, Kopie in „Gesendet“
      (falls der Server sie nicht selbst ablegt), application/sent.json schreiben, dann
      build_mappe.py mark-sent --channel email. --again sendet eine gesendete Bewerbung erneut (Rückläufer, oder die
      Firma nennt eine Portal-Adresse für E-Mail-Bewerbungen) und hängt den Versand an sent.json an; --to ersetzt den
      Empfänger des Entwurfs (nur mit einem Ordner).
  replies [--days N]
      Listet Nachrichten im Posteingang, die zu gesendeten Bewerbungen passen (Domain oder Ref.-Nr.; nur lesen).
  withdraw <stellenordner>… [--to <adresse>] [--anrede "…"] [--yes]
      Rückzug per E-Mail nach der Vorlage assets/templates/rueckzug.md (Regel send.withdraw). Empfänger: --to, sonst
      der Empfänger aus sent.json, sonst application.email oder contact.email aus job.json. Anrede: --anrede, sonst
      die Anrede des E-Mail-Entwurfs, sonst contact.salutation, sonst „Sehr geehrte Damen und Herren,“. Danach
      Status withdrawn. Ohne --yes nur Vorschau.
  reply <uid> --body-file <datei> [--from <ordner>] [--to <adresse>] [--yes]
      Antwort auf eine Nachricht im selben Verlauf (Betreff mit „Re:“, In-Reply-To), Text aus der Datei. --to: anderer
      Empfänger, etwa für eine Korrektur zur eigenen Mail aus „Sent Messages“.
      Ohne --yes nur Vorschau.
  compose --to <adresse> --subject "…" --body-file <datei> [--yes]
      Freie Nachricht an eine Firma (etwa eine Rückfrage), Text aus der Datei. Ohne --yes nur Vorschau.
  inbox [--days N]
      Listet den Posteingang mit UID, Datum, Absender und Betreff (nur lesen).
  move <uid>… --to <ordner> [--from <ordner>]
      Verschiebt Nachrichten aus dem Posteingang (oder --from) in einen Ordner (legt ihn an; Ablage nach Regel mail.sort).
"""
import functools
import argparse, datetime as dt, email.header, email.utils, imaplib, json, mimetypes, os, pathlib, re, smtplib, ssl
import subprocess, sys, time
from email.message import EmailMessage

print = functools.partial(print, flush=True)  # Fortschritt sofort sichtbar, auch umgeleitet

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF_DIR = pathlib.Path(os.environ.get('BEWERBUNG_MAIL_CONF', '~/.config/bewerbungs-helfer')).expanduser()
CONF, PASS = CONF_DIR / 'mail.json', CONF_DIR / 'mail.password'
DEFAULTS = {'smtp_host': 'smtp.mail.me.com', 'smtp_port': 587,
            'imap_host': 'imap.mail.me.com', 'imap_port': 993, 'sent_folder': 'Sent Messages'}
MAX_LETTER_AGE_DAYS = 7  # wie Regel letter.date: ältere Briefdaten erst neu datieren, freigeben, exportieren


def die(msg, code=2):
    print(f'FEHLER: {msg}', file=sys.stderr); sys.exit(code)


def load_conf():
    if not CONF.exists() or not PASS.exists():
        die(f'Keine Zugangsdaten. Erst: send_mail.py setup (Ablage {CONF_DIR})')
    c = {**DEFAULTS, **json.loads(CONF.read_text())}
    c['password'] = PASS.read_text().strip()
    return c


def profile_of(folder):
    parts = folder.resolve().relative_to(ROOT).parts
    if parts[0] != 'profile':
        die(f'{folder}: kein Stellenordner unter profile/')
    name = parts[1]
    p = json.loads((ROOT / 'profile' / name / 'assets/profile' / f'{name}_profile.json').read_text())
    return name, p['person']


def parse_draft(folder):
    """application/email.md: An, Betreff, Text zwischen den beiden ---."""
    s = (folder / 'application/email.md').read_text()
    to = re.search(r'\*\*An:\*\*\s*(\S+@\S+)', s)
    subj = re.search(r'\*\*Betreff:\*\*\s*(.+)', s)
    blocks = s.split('\n---\n')
    if not (to and subj and len(blocks) >= 3):
        die(f'{folder}: email.md unvollständig (An, Betreff, Text zwischen ---)')
    return to.group(1).strip('<>.,;'), subj.group(1).strip(), blocks[1].strip() + '\n'


def letter_date(folder):
    m = re.search(r'^datum:\s*(\d{4}-\d{2}-\d{2})', (folder / 'text_generation/anschreiben.md').read_text(), re.M)
    return dt.date.fromisoformat(m.group(1)) if m else None


def check_folder(folder, again=False, to=None):
    """Gibt (nachricht_daten, probleme) zurück. again: erneut senden (nach Rückläufer oder an eine Portaladresse),
    to: anderer Empfänger als im Entwurf."""
    probs = []
    job = json.loads((folder / 'job_information/job.json').read_text())
    mp = folder / 'application/application-manifest.json'
    if not mp.exists():
        return {'to': '–', 'subject': '–', 'body': '', 'pdf': mp, 'company': folder.name}, ['Mappe nicht gebaut']
    man = json.loads(mp.read_text())
    if (job.get('application') or {}).get('method') != 'email':
        return {'to': '–', 'subject': '–', 'body': '', 'pdf': folder / 'application/email.md',
                'company': man.get('company')}, ['Bewerbungsweg ist nicht „email“']
    if again:
        if man.get('status') not in ('sent', 'interview') or not (folder / 'application/sent.json').exists():
            probs.append(f'--again nur für gesendete Bewerbungen (Status {man.get("status")})')
    else:
        if man.get('status') != 'pdf_exported':
            probs.append(f'Status {man.get("status")} (nötig: pdf_exported)')
        if (folder / 'application/sent.json').exists():
            probs.append('bereits gesendet (application/sent.json); erneut nur mit --again')
    pdf = folder / 'application' / (man.get('pdf') or '')
    if not man.get('pdf') or not pdf.exists():
        probs.append('PDF fehlt')
    elif pdf.stat().st_size > 8 * 1024 * 1024:
        probs.append(f'PDF größer als 8 MB ({pdf.stat().st_size // 1024} KB)')
    d = letter_date(folder)
    if not d or (dt.date.today() - d).days > MAX_LETTER_AGE_DAYS:
        probs.append(f'Briefdatum {d} älter als {MAX_LETTER_AGE_DAYS} Tage: neu datieren, freigeben, exportieren')
    to_draft, subj, body = parse_draft(folder)
    to = to or to_draft
    if '[' in body or '[' in subj:
        probs.append('Platzhalter im Entwurf')
    return {'to': to, 'subject': subj, 'body': body, 'pdf': pdf, 'company': man.get('company')}, probs


def build_message(data, person, to=None, test=False):
    msg = EmailMessage()
    msg['From'] = email.utils.formataddr((person['name'], person['email']))
    msg['To'] = to or data['to']
    msg['Subject'] = ('[TEST] ' if test else '') + data['subject']
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-ID'] = email.utils.make_msgid(domain=person['email'].split('@')[1])
    msg.set_content(data['body'])
    att_name = f'Bewerbungsmappe_{person["first_name"]}_{person["last_name"]}.pdf'.replace(' ', '_')
    msg.add_attachment(data['pdf'].read_bytes(), maintype='application', subtype='pdf', filename=att_name)
    return msg, att_name


def smtp_send(c, msg):
    with smtplib.SMTP(c['smtp_host'], c['smtp_port'], timeout=60) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(c['user'], c['password'])
        s.send_message(msg)


def imap_conn(c):
    m = imaplib.IMAP4_SSL(c['imap_host'], c['imap_port'], ssl_context=ssl.create_default_context())
    m.login(c['user'], c['password'])
    return m


def ensure_in_sent(c, msg):
    """Kopie in „Gesendet“ ablegen, falls der Server sie nach kurzer Zeit nicht selbst abgelegt hat."""
    m = imap_conn(c)
    try:
        folder = '"%s"' % c['sent_folder']
        for _ in range(3):
            m.select(folder, readonly=True)
            typ, data = m.search(None, 'HEADER', 'Message-ID', msg['Message-ID'])
            if typ == 'OK' and data and data[0] and data[0].split():  # iCloud meldet „keine Treffer“ als [None]
                return 'vom Server abgelegt'
            time.sleep(3)
        m.append(folder, r'(\Seen)', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        return 'per IMAP abgelegt'
    finally:
        m.logout()


def cmd_setup(a):
    pw = pathlib.Path(a.password_file).read_text().strip()
    if not pw:
        die('Passwortdatei ist leer')
    CONF_DIR.mkdir(parents=True, exist_ok=True); os.chmod(CONF_DIR, 0o700)
    CONF.write_text(json.dumps({'user': a.user}, indent=2) + '\n'); os.chmod(CONF, 0o600)
    PASS.write_text(pw + '\n'); os.chmod(PASS, 0o600)
    print(f'Gespeichert unter {CONF_DIR} (0600).')


def cmd_check(a):
    c = load_conf()
    with smtplib.SMTP(c['smtp_host'], c['smtp_port'], timeout=30) as s:
        s.starttls(context=ssl.create_default_context()); s.login(c['user'], c['password'])
    print(f'SMTP {c["smtp_host"]}: Anmeldung ok')
    m = imap_conn(c)
    typ, folders = m.list()
    names = [f.decode().rsplit(' "/" ', 1)[-1].strip('"') for f in folders or []]
    m.logout()
    print(f'IMAP {c["imap_host"]}: Anmeldung ok · Ordner „{c["sent_folder"]}“ '
          f'{"vorhanden" if c["sent_folder"] in names else "FEHLT (Ordner: " + ", ".join(names) + ")"}')


def cmd_preview(a, folders=None):
    ok = True
    for f in folders or [pathlib.Path(x) for x in a.folders]:
        _, person = profile_of(f)
        data, probs = check_folder(f, getattr(a, 'again', False), getattr(a, 'to', None))
        ok &= not probs
        size = f'{data["pdf"].stat().st_size // 1024} KB' if data['pdf'].exists() else 'fehlt'
        print(f'{"OK " if not probs else "-- "} {data["company"]}\n    An: {data["to"]}\n    Betreff: {data["subject"]}'
              f'\n    Von: {person["name"]} <{person["email"]}> · Anhang: {size}'
              + ''.join(f'\n    PROBLEM: {p}' for p in probs))
    return ok


def cmd_test(a):
    c = load_conf(); f = pathlib.Path(a.folder)
    _, person = profile_of(f)
    data, probs = check_folder(f)
    for p in probs:
        print(f'Hinweis: {p}')
    msg, att = build_message(data, person, to=a.to or person['email'], test=True)
    smtp_send(c, msg)
    print(f'Testmail an {msg["To"]} gesendet (Anhang {att}). Kein Ledger-Eintrag.')


def cmd_send(a):
    folders = [pathlib.Path(x) for x in a.folders]
    if a.to and len(folders) != 1:
        die('--to nur mit genau einem Stellenordner')
    if not cmd_preview(a, folders):
        die('Stapel hat Probleme, nichts gesendet.')
    if not a.yes:
        print('\nNur Vorschau. Senden erst nach Freigabe des Nutzers mit --yes.'); return
    c = load_conf()
    for i, f in enumerate(folders):
        _, person = profile_of(f)
        data, _ = check_folder(f, a.again, a.to)
        msg, att = build_message(data, person)
        smtp_send(c, msg)
        sent_json = f / 'application/sent.json'
        if a.again:  # erneuter Versand: an sent.json anhängen, Status bleibt
            j = json.loads(sent_json.read_text())
            entry = {'sent_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'), 'to': data['to'],
                     'message_id': msg['Message-ID'], 'sent_copy': 'offen'}
            j.setdefault('resends', []).append(entry)
            sent_json.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
            try:
                entry['sent_copy'] = ensure_in_sent(c, msg)
            except Exception as e:
                entry['sent_copy'] = f'Kopie fehlgeschlagen: {e}'
            sent_json.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
            print(f'ERNEUT GESENDET {data["company"]} → {data["to"]} ({entry["sent_copy"]})')
            if i < len(folders) - 1:
                time.sleep(a.delay)
            continue
        record = {'sent_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
                  'to': data['to'], 'subject': data['subject'], 'message_id': msg['Message-ID'],
                  'attachment': att, 'sent_copy': 'offen'}
        sent_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')  # sofort, vor allem anderen
        try:
            where = ensure_in_sent(c, msg)
        except Exception as e:  # Versand ist erfolgt; fehlende Kopie bricht den Stapel nicht ab
            where = f'Kopie fehlgeschlagen: {e}'
        record['sent_copy'] = where
        sent_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        r = subprocess.run([sys.executable, str(ROOT / 'tools/build_mappe.py'), 'mark-sent', str(f),
                            '--channel', 'email'], capture_output=True, text=True)
        print(f'GESENDET {data["company"]} → {data["to"]} ({where})'
              + ('' if r.returncode == 0 else f'\n    mark-sent FEHLER: {r.stderr.strip()}'))
        if i < len(folders) - 1:
            time.sleep(a.delay)


def cmd_replies(a):
    """Posteingang seit --days: Nachrichten, deren Absender-Domain zu einer gesendeten Bewerbung passt
    oder deren Betreff deren Ref.-Nr. enthält (Antworten kommen oft von einer anderen Domain)."""
    c = load_conf()
    sent = []
    for p in ROOT.glob('profile/*/applications/sent/**/application/sent.json'):
        j = json.loads(p.read_text())
        if 'to' not in j:  # Portal-Bewerbung, nur Rückzug per Mail protokolliert
            continue
        ref = re.search(r'Ref\.-Nr\.\s*([\w-]+)', j.get('subject', ''))
        sent.append((j['to'].split('@')[1].lower(), ref.group(1) if ref else None, p.parent.parent))
    if not sent:
        print('Noch keine gesendeten Bewerbungen.'); return
    dec = lambda v: str(email.header.make_header(email.header.decode_header(v or '')))
    since = (dt.date.today() - dt.timedelta(days=a.days)).strftime('%d-%b-%Y')
    m = imap_conn(c)
    try:
        m.select('INBOX', readonly=True)
        typ, data = m.search(None, 'SINCE', since)
        for num in (data[0].split() if typ == 'OK' and data and data[0] else []):
            typ, hd = m.fetch(num, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
            h = email.message_from_bytes(hd[0][1])
            frm, subj = dec(h['From']), dec(h['Subject'])
            dom = (email.utils.parseaddr(frm)[1].split('@')[-1]).lower()
            hits = [str(fo.relative_to(ROOT)) for d, ref, fo in sent
                    if dom == d or dom.endswith('.' + d) or (ref and ref in subj)]
            if hits:
                print(f'{h["Date"]} · {frm}\n    {subj}\n    Stelle: {", ".join(hits)}')
    finally:
        m.logout()


TEMPLATE_WITHDRAW = ROOT / '.agents/skills/bewerbungshelfer/assets/templates/rueckzug.md'


def withdraw_message(folder, to=None, anrede=None):
    """(empfänger, betreff, text, probleme) für den Rückzug einer Stelle."""
    probs = []
    job = json.loads((folder / 'job_information/job.json').read_text())
    man = json.loads((folder / 'application/application-manifest.json').read_text())
    if man.get('status') not in ('sent', 'interview', 'offer'):
        probs.append(f'Status {man.get("status")}: nur gesendete Bewerbungen lassen sich zurückziehen')
    sj = folder / 'application/sent.json'
    contact = job.get('contact') or {}
    to = to or (json.loads(sj.read_text()).get('to') if sj.exists() else None) \
        or (job.get('application') or {}).get('email') or contact.get('email')
    if not to:
        probs.append('keine E-Mail-Adresse: im Portal zurückziehen, dann build_mappe.py status … withdrawn')
    if not anrede:
        draft = (folder / 'application/email.md')
        first = ''
        if draft.exists() and len(draft.read_text().split('\n---\n')) >= 3:
            first = draft.read_text().split('\n---\n')[1].strip().splitlines()[0]
        anrede = first if first.startswith('Sehr geehrte') else \
            (contact['salutation'].rstrip(',') + ',' if contact.get('salutation') else 'Sehr geehrte Damen und Herren,')
    _, person = profile_of(folder)
    t = TEMPLATE_WITHDRAW.read_text()
    fill = {'anrede': anrede, 'beruf': man.get('role') or job.get('title'), 'ref': man.get('reference_number') or '',
            'jahr': (job.get('start') or '')[:4], 'name': person['name'], 'telefon': person.get('phone', '')}
    for k, v in fill.items():
        t = t.replace('{' + k + '}', v)
    subj, body = t.split('\n', 1)
    return to, subj.removeprefix('Betreff:').strip(), body.strip() + '\n', probs


def cmd_withdraw(a):
    folders = [pathlib.Path(x) for x in a.folders]
    if (a.to or a.anrede) and len(folders) != 1:
        die('--to und --anrede nur mit genau einem Stellenordner')
    plan, bad = [], False
    for f in folders:
        to, subj, body, probs = withdraw_message(f, a.to, a.anrede)
        bad |= bool(probs)
        plan.append((f, to, subj, body))
        print(f'{"OK " if not probs else "-- "} {f.name}\n    An: {to}\n    Betreff: {subj}\n    Anrede: {body.splitlines()[0]}'
              + ''.join(f'\n    PROBLEM: {p}' for p in probs))
    if bad:
        die('Stapel hat Probleme, nichts gesendet.')
    if not a.yes:
        print('\nNur Vorschau. Senden erst nach Freigabe des Nutzers mit --yes.'); return
    c = load_conf()
    for i, (f, to, subj, body) in enumerate(plan):
        _, person = profile_of(f)
        msg = EmailMessage()
        msg['From'] = email.utils.formataddr((person['name'], person['email'])); msg['To'] = to
        msg['Subject'] = subj; msg['Date'] = email.utils.formatdate(localtime=True)
        msg['Message-ID'] = email.utils.make_msgid(domain=person['email'].split('@')[1])
        msg.set_content(body)
        smtp_send(c, msg)
        sj = f / 'application/sent.json'
        j = json.loads(sj.read_text()) if sj.exists() else {}
        j['withdrawn'] = {'sent_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'), 'to': to,
                          'message_id': msg['Message-ID']}
        sj.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
        try:
            ensure_in_sent(c, msg)
        except Exception as e:
            print(f'    Kopie in „Gesendet“ fehlgeschlagen: {e}')
        r = subprocess.run([sys.executable, str(ROOT / 'tools/build_mappe.py'), 'status', str(f), 'withdrawn'],
                           capture_output=True, text=True)
        print(f'ZURÜCKGEZOGEN {f.name} → {to}' + ('' if r.returncode == 0 else f'\n    status FEHLER: {r.stderr.strip()}'))
        if i < len(plan) - 1:
            time.sleep(a.delay)


def cmd_reply(a):
    c = load_conf()
    body = pathlib.Path(a.body_file).read_text().strip() + '\n'
    if '[' in body:
        die('Platzhalter im Text')
    m = imap_conn(c)
    try:
        m.select('"%s"' % a.source if a.source != 'INBOX' else 'INBOX', readonly=True)
        typ, r = m.uid('FETCH', a.uid, '(BODY.PEEK[HEADER])')
        if typ != 'OK' or not r or not isinstance(r[0], tuple):
            die(f'Nachricht {a.uid} in „{a.source}“ nicht gefunden')
        orig = email.message_from_bytes(r[0][1])
    finally:
        m.logout()
    dec = lambda v: str(email.header.make_header(email.header.decode_header(v or '')))
    to = a.to or email.utils.parseaddr(orig.get('Reply-To') or orig['From'])[1]
    subj = re.sub(r'^\s*((re|aw|antw)\s*:\s*)+', '', dec(orig['Subject']), flags=re.I)
    profile = next(ROOT.glob('profile/*/assets/profile/*_profile.json'))
    person = json.loads(profile.read_text())['person']
    msg = EmailMessage()
    msg['From'] = email.utils.formataddr((person['name'], person['email'])); msg['To'] = to
    msg['Subject'] = f'Re: {subj}'; msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-ID'] = email.utils.make_msgid(domain=person['email'].split('@')[1])
    if orig['Message-ID']:
        oneline = lambda v: ' '.join(str(v).split())  # gefaltete Kopfzeilen auf eine Zeile
        msg['In-Reply-To'] = oneline(orig['Message-ID'])
        msg['References'] = ' '.join(oneline(x) for x in (orig.get('References'), orig['Message-ID']) if x)
    msg.set_content(body)
    print(f'An: {to}\nBetreff: {msg["Subject"]}\n\n{body}')
    if not a.yes:
        print('Nur Vorschau. Senden erst nach Freigabe des Nutzers mit --yes.'); return
    smtp_send(c, msg)
    try:
        where = ensure_in_sent(c, msg)
    except Exception as e:
        where = f'Kopie fehlgeschlagen: {e}'
    print(f'GESENDET → {to} ({where})')


def cmd_compose(a):
    body = pathlib.Path(a.body_file).read_text().strip() + '\n'
    if '[' in body or '[' in a.subject:
        die('Platzhalter im Text')
    person = json.loads(next(ROOT.glob('profile/*/assets/profile/*_profile.json')).read_text())['person']
    msg = EmailMessage()
    msg['From'] = email.utils.formataddr((person['name'], person['email'])); msg['To'] = a.to
    msg['Subject'] = a.subject; msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-ID'] = email.utils.make_msgid(domain=person['email'].split('@')[1])
    msg.set_content(body)
    print(f'An: {a.to}\nBetreff: {a.subject}\n\n{body}')
    if not a.yes:
        print('Nur Vorschau. Senden erst nach Freigabe des Nutzers mit --yes.'); return
    c = load_conf()
    smtp_send(c, msg)
    try:
        where = ensure_in_sent(c, msg)
    except Exception as e:
        where = f'Kopie fehlgeschlagen: {e}'
    print(f'GESENDET → {a.to} ({where})')


def cmd_inbox(a):
    c = load_conf()
    box = '"%s"' % a.source if a.source != 'INBOX' else 'INBOX'
    dec = lambda v: str(email.header.make_header(email.header.decode_header(v or '')))
    since = (dt.date.today() - dt.timedelta(days=a.days)).strftime('%d-%b-%Y')
    m = imap_conn(c)
    try:
        m.select(box, readonly=True)
        typ, data = m.uid('SEARCH', None, 'SINCE', since)
        for uid in (data[0].split() if typ == 'OK' and data and data[0] else []):
            typ, hd = m.uid('FETCH', uid, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
            h = email.message_from_bytes(hd[0][1])
            print(f'{uid.decode()} · {h["Date"]} · {dec(h["From"])}\n    {dec(h["Subject"])}')
    finally:
        m.logout()


def cmd_move(a):
    if not a.to.isascii():
        die('Ordnername nur mit ASCII-Zeichen (IMAP), z. B. „Bewerbungen Automatisch“')
    c = load_conf()
    m = imap_conn(c)
    try:
        folder = '"%s"' % a.to
        m.create(folder)  # existiert er schon, meldet der Server NO; das ist in Ordnung
        m.select('"%s"' % a.source if a.source != 'INBOX' else 'INBOX')
        uids = ','.join(a.uids)
        typ, _ = m.uid('COPY', uids, folder)
        if typ != 'OK':
            die(f'Kopieren nach {a.to} fehlgeschlagen, nichts verschoben')
        m.uid('STORE', uids, '+FLAGS', r'(\Deleted)')
        m.expunge()
        print(f'{len(a.uids)} Nachricht(en) von „{a.source}“ nach „{a.to}“ verschoben.')
    finally:
        m.logout()


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('setup'); s.add_argument('--user', required=True); s.add_argument('--password-file', required=True)
    sp.add_parser('check')
    s = sp.add_parser('preview'); s.add_argument('folders', nargs='+')
    s = sp.add_parser('test'); s.add_argument('folder'); s.add_argument('--to')
    s = sp.add_parser('send'); s.add_argument('folders', nargs='+'); s.add_argument('--yes', action='store_true')
    s.add_argument('--delay', type=int, default=45); s.add_argument('--again', action='store_true'); s.add_argument('--to')
    s = sp.add_parser('replies'); s.add_argument('--days', type=int, default=60)
    s = sp.add_parser('withdraw'); s.add_argument('folders', nargs='+'); s.add_argument('--to'); s.add_argument('--anrede')
    s.add_argument('--yes', action='store_true'); s.add_argument('--delay', type=int, default=45)
    s = sp.add_parser('reply'); s.add_argument('uid'); s.add_argument('--body-file', required=True)
    s.add_argument('--from', dest='source', default='INBOX'); s.add_argument('--yes', action='store_true'); s.add_argument('--to')
    s = sp.add_parser('compose'); s.add_argument('--to', required=True); s.add_argument('--subject', required=True)
    s.add_argument('--body-file', required=True); s.add_argument('--yes', action='store_true')
    s = sp.add_parser('inbox'); s.add_argument('--days', type=int, default=30); s.add_argument('--from', dest='source', default='INBOX')
    s = sp.add_parser('move'); s.add_argument('uids', nargs='+'); s.add_argument('--to', required=True)
    s.add_argument('--from', dest='source', default='INBOX')
    return ap


def main():
    a = build_parser().parse_args()
    {'setup': cmd_setup, 'check': cmd_check, 'preview': cmd_preview, 'test': cmd_test,
     'send': cmd_send, 'replies': cmd_replies, 'inbox': cmd_inbox, 'move': cmd_move,
     'withdraw': cmd_withdraw, 'reply': cmd_reply, 'compose': cmd_compose}[a.cmd](a)


if __name__ == '__main__':
    main()
