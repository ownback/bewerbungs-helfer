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
  send <stellenordner>… --yes [--delay SEKUNDEN]
      Sendet den freigegebenen Stapel. Ohne --yes nur Vorschau. Je Stelle: Senden, Kopie in „Gesendet“
      (falls der Server sie nicht selbst ablegt), application/sent.json schreiben, dann
      build_mappe.py mark-sent --channel email.
  replies [--days N]
      Listet Nachrichten im Posteingang von den Domains der gesendeten Bewerbungen (nur lesen).
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


def check_folder(folder):
    """Gibt (nachricht_daten, probleme) zurück."""
    probs = []
    job = json.loads((folder / 'job_information/job.json').read_text())
    mp = folder / 'application/application-manifest.json'
    if not mp.exists():
        return {'to': '–', 'subject': '–', 'body': '', 'pdf': mp, 'company': folder.name}, ['Mappe nicht gebaut']
    man = json.loads(mp.read_text())
    if (job.get('application') or {}).get('method') != 'email':
        return {'to': '–', 'subject': '–', 'body': '', 'pdf': folder / 'application/email.md',
                'company': man.get('company')}, ['Bewerbungsweg ist nicht „email“']
    if man.get('status') != 'pdf_exported':
        probs.append(f'Status {man.get("status")} (nötig: pdf_exported)')
    if (folder / 'application/sent.json').exists():
        probs.append('bereits gesendet (application/sent.json)')
    pdf = folder / 'application' / (man.get('pdf') or '')
    if not man.get('pdf') or not pdf.exists():
        probs.append('PDF fehlt')
    elif pdf.stat().st_size > 8 * 1024 * 1024:
        probs.append(f'PDF größer als 8 MB ({pdf.stat().st_size // 1024} KB)')
    d = letter_date(folder)
    if not d or (dt.date.today() - d).days > MAX_LETTER_AGE_DAYS:
        probs.append(f'Briefdatum {d} älter als {MAX_LETTER_AGE_DAYS} Tage: neu datieren, freigeben, exportieren')
    to, subj, body = parse_draft(folder)
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
        data, probs = check_folder(f)
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
    if not cmd_preview(a, folders):
        die('Stapel hat Probleme, nichts gesendet.')
    if not a.yes:
        print('\nNur Vorschau. Senden erst nach Freigabe des Nutzers mit --yes.'); return
    c = load_conf()
    for i, f in enumerate(folders):
        _, person = profile_of(f)
        data, _ = check_folder(f)
        msg, att = build_message(data, person)
        smtp_send(c, msg)
        record = {'sent_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
                  'to': data['to'], 'subject': data['subject'], 'message_id': msg['Message-ID'],
                  'attachment': att, 'sent_copy': 'offen'}
        sent_json = f / 'application/sent.json'
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


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('setup'); s.add_argument('--user', required=True); s.add_argument('--password-file', required=True)
    sp.add_parser('check')
    s = sp.add_parser('preview'); s.add_argument('folders', nargs='+')
    s = sp.add_parser('test'); s.add_argument('folder'); s.add_argument('--to')
    s = sp.add_parser('send'); s.add_argument('folders', nargs='+'); s.add_argument('--yes', action='store_true')
    s.add_argument('--delay', type=int, default=45)
    s = sp.add_parser('replies'); s.add_argument('--days', type=int, default=60)
    return ap


def main():
    a = build_parser().parse_args()
    {'setup': cmd_setup, 'check': cmd_check, 'preview': cmd_preview, 'test': cmd_test,
     'send': cmd_send, 'replies': cmd_replies}[a.cmd](a)


if __name__ == '__main__':
    main()
