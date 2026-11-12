#!/usr/bin/env python3
"""Bewerbungsmappe bauen, prüfen und verwalten (nur Python-Standardbibliothek).

Das Skript enthält keine persönlichen Daten. Es liest das Profil, die Stelle und die
Texte aus dem gitignorierten Ordner profile/<vorname.nachname>/ und setzt sie in die
Basisvorlage .agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html ein.
CSS und SVG-Bibliothek kommen unverändert aus der Vorlage; das Markup der Seiten
folgt dem Datenvertrag der Vorlage (references/template.md).

Befehle:
  profile-template <profil-ordner> [--qa] [--pdf]
      Baut assets/profile/<name>_template.html aus <name>_profile.json und den Assets.
      --pdf schreibt die A4-Vorschau <name>_template.pdf daneben.
  application <stellen-ordner> [--qa] [--pdf]
      Baut application/bewerbungsmappe - <name>.html aus der Profilvorlage,
      text_generation/anschreiben.md, text_generation/motivationsschreiben.md und
      job_information/job.json. Aktualisiert application-manifest.json und ledger.json.
      --pdf exportiert das finale A4-PDF, aber nur bei Status html_approved oder später.
  qa <html>                      Überlauf-, Platzhalter-, Seiten- und Breitenprüfung (1440/390/375 px,
                                 Headless-Chromium); bei Bewerbungsweg „email“ auch der E-Mail-Entwurf.
  preview <html> <ausgabe-ordner> A4-Vorschau als PDF und PNG-Seiten (PNG nur mit pdftoppm).
  validate <profil-|stellen-ordner>  JSON-Schemaprüfung (benötigt das Paket jsonschema), Asset-Pfade und
      bei Bewerbungsweg „email“ der E-Mail-Entwurf application/email.md.
  check-duplicate <stellen-ordner>   Ledger auf gleiche Referenznummer oder Firma+Titel prüfen.
  status <stellen-ordner> <status>   Status in Manifest und Ledger setzen (nicht „sent“: dafür mark-sent).
  mark-sent <stellen-ordner> --channel email|post|portal [--date JJJJ-MM-TT]
      Ordner nach applications/sent/<typ>/… verschieben und Ledger aktualisieren.
  stats <profil-ordner>          Kennzahlen aus dem Ledger (Status, Typ, Monat).

Chromium wird über $CHROME oder chromium/chromium-browser/google-chrome gesucht.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents' / 'skills' / 'bewerbungshelfer'
TEMPLATE = SKILL / 'assets' / 'bewerbungsmappe.html'
SCHEMAS = SKILL / 'assets' / 'schemas'
PROFILE_ROOT = ROOT / 'profile'

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']
SCALE_LABEL = {1: 'Lernwunsch', 2: 'Grundkenntnisse', 3: 'sicher', 4: 'routiniert', 5: 'sehr sicher'}
KIND_LABEL = {'internship': 'Praktikum', 'employment': 'Anstellung', 'volunteer': 'Ehrenamt', 'other': 'Sonstiges'}
ORIGINAL_LABEL = {'scan': 'Original-Scan', 'copy': 'Kopie', 'digital_original': 'Digitales Original',
                  'unknown': 'Nachweis'}
SECTIONS = ['deckblatt', 'anschreiben', 'lebenslauf', 'motivationsschreiben', 'zertifikate', 'zeugnisse']
SECTION_META = {  # section -> (data-section, id prefix, Titel, Navigationslabel)
    'deckblatt': (1, 'cover', 'Deckblatt', 'Deckblatt'),
    'anschreiben': (2, 'letter', 'Anschreiben', 'Anschreiben'),
    'lebenslauf': (3, 'cv', 'Lebenslauf', 'Lebenslauf'),
    'motivationsschreiben': (4, 'motivation', 'Motivationsschreiben', 'Motivation'),
    'zertifikate': (5, 'cert', 'Zertifikate', 'Zertifikate'),
    'zeugnisse': (6, 'reference', 'Zeugnisse', 'Zeugnisse'),
}
TYPES = ['apprenticeships', 'jobs', 'internships']
STATUSES = ['draft', 'html_approved', 'pdf_exported', 'sent', 'interview', 'offer', 'rejected', 'withdrawn']
SUBJECT_KICKER = {
    'apprenticeships': 'Bewerbung um einen Ausbildungsplatz als',
    'jobs': 'Bewerbung als',
    'internships': 'Bewerbung um einen Praktikumsplatz als',
}
LETTER_WORDS = {'normal': 250, 'dicht': 350}
MOTIVATION_WORDS = {'normal': 300, 'dicht': 370}
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
# Bildschirmbreiten der QA: Desktop (Überlauf, Füllgrad) und zwei Mobilbreiten; Schlüssel -> Fenstergröße
QA_VIEWPORTS = (('desktop', '1440,900'), ('mobile', '390,844'), ('mobile_375', '375,812'))


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------- Hilfen

def esc(text) -> str:
    return html.escape(str(text), quote=True)


def icon(name: str) -> str:
    return f'<svg class="icon"><use href="#{esc(name)}"/></svg>'


def logo(name: str) -> str:
    return f'<svg class="logo"><use href="#{esc(name)}"/></svg>'


def bars(scale: int, future: bool = False, label: str | None = None, aria: bool = True) -> str:
    cls = f'bars s{scale}' + (' is-future' if future else '')
    attr = f' role="img" aria-label="{scale} von 5: {esc(label or SCALE_LABEL[scale])}"' if aria else ''
    return f'<span class="{cls}"{attr}>' + '<span></span>' * 5 + '</span>'


def email_html(addr: str) -> str:
    """Lange Adressen bekommen <wbr> nach @ und vor Punkten (Regel der Vorlage)."""
    if len(addr) <= 24:
        return esc(addr)
    local, _, domain = addr.partition('@')
    domain = '<wbr>.'.join(esc(p) for p in domain.split('.'))
    return f'{esc(local)}@<wbr>{domain}'


def slugify(text: str) -> str:
    t = text.lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        t = t.replace(a, b)
    t = re.sub(r'[^a-z0-9]+', '-', t)
    return t.strip('-')


def german_date(value: str) -> str:
    """2026-11-11 -> 11. November 2026; andere Werte bleiben unverändert."""
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', value.strip())
    if not m:
        return value.strip()
    y, mo, d = (int(x) for x in m.groups())
    return f'{d}. {MONTHS[mo - 1]} {y}'


def short_date(value: str) -> str:
    """2026-07-10 -> 10.07.2026, 2026-07 -> 07/2026, 2026 -> 2026."""
    parts = value.split('-')
    if len(parts) == 3:
        return f'{parts[2]}.{parts[1]}.{parts[0]}'
    if len(parts) == 2:
        return f'{parts[1]}/{parts[0]}'
    return value


def month_year(value: str) -> str:
    parts = value.split('-')
    if len(parts) >= 2:
        return f'{MONTHS[int(parts[1]) - 1]} {parts[0]}'
    return value


def fmt_point(value, precision: str) -> str:
    if not value:
        return ''
    if precision == 'year' or len(value) == 4:
        return value[:4]
    if precision == 'day':
        return short_date(value)
    return f'{value[5:7]}/{value[:4]}'


def fmt_range(dr: dict) -> str:
    prec = dr.get('precision', 'month')
    if prec == 'unknown':
        return ''
    a, b = fmt_point(dr.get('start'), prec), fmt_point(dr.get('end'), prec)
    if dr.get('is_current'):
        text = f'seit {a}'
    elif not b or a == b:
        text = a
    else:
        text = f'{a} – {b}'
    return ('ca. ' + text) if dr.get('approx') else text


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise BuildError(f'Datei fehlt: {rel(path)}')
    except json.JSONDecodeError as e:
        raise BuildError(f'Kein gültiges JSON: {rel(path)} ({e})')


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def today() -> str:
    return dt.date.today().isoformat()


# --------------------------------------------------------------------------- Pfade

def profile_dir_of(path: Path) -> Path:
    path = path.resolve()
    for p in [path, *path.parents]:
        if p.parent == PROFILE_ROOT.resolve():
            return p
    raise BuildError(f'{path} liegt nicht unter profile/<vorname.nachname>/')


def profile_json_path(pdir: Path) -> Path:
    return pdir / 'assets' / 'profile' / f'{pdir.name}_profile.json'


def profile_template_path(pdir: Path) -> Path:
    return pdir / 'assets' / 'profile' / f'{pdir.name}_template.html'


def ledger_path(pdir: Path) -> Path:
    return pdir / 'applications' / 'ledger.json'


def resolve_asset(pdir: Path, file: str, field: str = 'Asset') -> Path:
    """Asset-Pfade im Profil sind repo-relativ (profile/<name>/…) oder relativ zum Profilordner.

    Der aufgelöste Pfad (nach `..` und Symlinks) muss unter profile/<name>/assets/ liegen, sonst BuildError
    mit dem Profilfeld `field`."""
    p = Path(file)
    if p.is_absolute():
        path = p
    elif p.parts and p.parts[0] == 'profile':
        path = ROOT / p
    else:
        path = pdir / p
    resolved = path.resolve()
    allowed = (pdir / 'assets').resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise BuildError(f'{field}: „{file}“ liegt nicht unter {rel(allowed)}/ (aufgelöst: {resolved}). '
                         'Absolute Pfade außerhalb des Profils, „..“ und Symlinks aus dem Profil heraus sind nicht erlaubt.')
    return resolved


def profile_asset_fields(profile: dict) -> list[tuple[str, str]]:
    """(Profilfeld, Dateipfad) aller Asset-Verweise im Profil."""
    person = profile.get('person') or {}
    out = []
    for key in ('photo', 'signature'):
        if (person.get(key) or {}).get('file'):
            out.append((f'person.{key}.file', person[key]['file']))
    for i, ev in enumerate(profile.get('evidence') or []):
        if ev.get('file'):
            out.append((f'evidence[{ev.get("id", i)}].file', ev['file']))
    for i, pr in enumerate(profile.get('projects') or []):
        for j, img in enumerate(pr.get('images') or []):
            if img.get('file'):
                out.append((f'projects[{pr.get("id", i)}].images[{j}].file', img['file']))
    return out


def check_profile_assets(profile: dict, pdir: Path) -> None:
    for field, file in profile_asset_fields(profile):
        resolve_asset(pdir, file, field)


def email_draft_state(posting: Path) -> tuple[str, str]:
    """Prüft application/email.md. Zustand: not_required, ok, missing, empty, placeholders; dazu eine Meldung."""
    job_file = posting / 'job_information' / 'job.json'
    if not job_file.is_file():
        return 'not_required', ''
    method = (read_json(job_file).get('application') or {}).get('method')
    if method != 'email':
        return 'not_required', ''
    draft = posting / 'application' / 'email.md'
    where = rel(draft)
    if not draft.is_file():
        return 'missing', (f'E-Mail-Entwurf fehlt: {where}. Der Bewerbungsweg ist „email“; ohne Entwurf keine Freigabe '
                           'und kein PDF (references/writing.md, Abschnitt email.md).')
    text = draft.read_text(encoding='utf-8')
    if not text.strip():
        return 'empty', f'E-Mail-Entwurf ist leer: {where}.'
    left = sorted(set(re.findall(r'\[[^\]\n]{2,120}\](?!\()', re.sub(r'<!--.*?-->', '', text, flags=re.S))))
    if left:
        return 'placeholders', f'E-Mail-Entwurf hat offene Platzhalter in {where}: {", ".join(left)}'
    return 'ok', ''


def posting_info(posting: Path) -> dict:
    pdir = profile_dir_of(posting)
    parts = posting.resolve().relative_to(pdir).parts
    if len(parts) < 5 or parts[0] != 'applications':
        raise BuildError(f'{posting} ist kein Stellenordner '
                         '(applications/<typ>/<beruf>/<suchort>/<NN-ort-firma>/)')
    sent = parts[1] == 'sent'
    typ = parts[2] if sent else parts[1]
    if typ not in TYPES:
        raise BuildError(f'Unbekannter Typ „{typ}“ im Pfad {posting}')
    return {'profile_dir': pdir, 'user': pdir.name, 'type': typ, 'sent': sent,
            'folder': '/'.join(parts)}


def html_name(user: str, ext: str = 'html') -> str:
    return f'bewerbungsmappe - {user}.{ext}'


# --------------------------------------------------------------------------- Vorlage

def template_text() -> str:
    return TEMPLATE.read_text(encoding='utf-8')


def template_head(tpl: str, title: str) -> str:
    head = tpl.split('<div class="screen-bar', 1)[0]
    return re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', head, count=1, flags=re.S)


def qa_snippet(tpl: str) -> str:
    m = re.search(r'\(QA-SNIPPET-START\)(.*?)\(QA-SNIPPET-END\)', tpl, re.S)
    if not m:
        raise BuildError('QA-SNIPPET fehlt in der Vorlage')
    code = m.group(1)
    return code[code.index('[...document'):].strip()


def template_classes(tpl: str) -> set[str]:
    classes = set(re.findall(r'\.([a-zA-Z][\w-]*)', tpl.split('</style>', 1)[0]))
    for attr in re.findall(r'class="([^"]*)"', tpl):
        classes.update(attr.split())
    return classes


# --------------------------------------------------------------------------- Seiten

def section_head(section: str, number: int, continued: bool, n_cont: int = 0) -> str:
    _, prefix, title, _ = SECTION_META[section]
    hid = f'{prefix}{n_cont + 1}-title' if continued else f'{prefix}-title'
    cont = '<span class="continued">Fortsetzung</span>' if continued else ''
    return ('    <header class="section-head">\n'
            f'      <h2 id="{hid}">{title}{cont}</h2>\n'
            f'      <span class="folio" aria-label="Seite {number}">{number}</span>\n'
            '    </header>\n')


def name_class(first: str, last: str) -> str:
    parts = []
    for word in f'{first} {last}'.split():
        segs = word.split('-')
        parts += [s + '-' for s in segs[:-1]] + [segs[-1]]
    longest = max((len(p) for p in parts), default=0)
    if longest >= 14:
        return ' class="is-xlong"'
    if longest >= 11:
        return ' class="is-long"'
    return ''


def screen_chrome(starts: dict) -> str:
    out = ['  <div class="screen-bar glass glass-light" aria-hidden="true">',
           '    <span><strong>Bewerbungsmappe</strong></span>',
           '    <span class="state"><span>HTML-Fassung · PDF im A4-Format</span><span class="viewport-proof mobile">'
           'Mobilansicht</span><span class="viewport-proof desktop">Desktopansicht</span></span>',
           '  </div>', '',
           '  <nav class="screen-nav glass glass-light" aria-label="Seiten">']
    for sec in SECTIONS:
        _, prefix, _, nav = SECTION_META[sec]
        out.append(f'    <a href="#{prefix}-title"><span>{nav}</span><span>{starts[sec]}</span></a>')
    out += ['  </nav>', '']
    return '\n'.join(out) + '\n'


class Ctx:
    """Alle Werte, die eine Seite braucht. src() rechnet Asset-Pfade relativ zur Ausgabedatei."""

    def __init__(self, profile: dict, pdir: Path, out_dir: Path):
        self.p = profile
        self.pdir = pdir
        self.out_dir = out_dir

    def src(self, file: str, field: str = 'Asset') -> str:
        path = resolve_asset(self.pdir, file, field)
        if not path.is_file() or path.stat().st_size == 0:
            raise BuildError(f'Asset fehlt oder ist leer: {file}')
        return Path(os.path.relpath(path, self.out_dir)).as_posix()


def render_cover(ctx: Ctx, starts: dict) -> str:
    p = ctx.p
    person, goal, port = p['person'], p['goal'], p.get('portfolio', {})
    first = person.get('first_name') or person['name'].split()[0]
    last = person.get('last_name') or ' '.join(person['name'].split()[1:])
    role_lines = port.get('cover_role') or [goal['apprenticeship']]
    bio = port.get('cover_bio') or '[KURZPROFIL: Alter, aktueller Bildungsweg, Zugang zum Beruf und Ausbildungsziel]'
    start = port.get('cover_start') or (f'Ausbildung ab {month_year(goal["start"])}' if goal.get('start')
                                         else '[AUSBILDUNGSBEGINN]')
    addr = person['address']
    photo = ''
    ph = person.get('photo', {})
    if ph.get('valid') and ph.get('consent') and ph.get('file'):
        focus = ph.get('focus') or {}
        style = '; '.join(f'--photo-{k}: {focus[k]}' for k in ('x', 'y', 'zoom') if k in focus)
        style = f' style="{esc(style)}"' if style else ''
        photo = (f'        <figure class="cover-photo"{style}><img src="{esc(ctx.src(ph["file"], "person.photo.file"))}" '
                 f'alt="{esc(ph.get("alt") or "Bewerbungsfoto von " + person["name"])}"></figure>\n')
    toc = ''.join(f'            <li class="toc-row"><span>{SECTION_META[s][2]}</span>'
                  f'<span class="toc-page">{starts[s]}</span></li>\n' for s in SECTIONS)
    return (
        '  <!-- Deckblatt -->\n'
        '  <section class="page cover-page" data-section="1" aria-labelledby="cover-title">\n'
        '    <div class="cover-layout">\n'
        '      <div class="cover-stage">\n'
        '      <div class="cover-main">\n'
        f'        <p class="cover-mark">{icon("i-folder")}Bewerbungsmappe</p>\n'
        '        <div class="cover-hero">\n'
        f'          <h1 id="cover-title"{name_class(first, last)}>{esc(first)}<br>{esc(last)}</h1>\n'
        f'          <p class="cover-role">{"<br>".join(esc(x) for x in role_lines)}</p>\n'
        '        </div>\n'
        '      </div>\n\n'
        '      <aside class="cover-panel glass glass-dark" aria-label="Kontakt und Inhalt">\n'
        f'{photo}'
        f'        <p class="label">{icon("i-user")}Kontakt</p>\n'
        '        <div class="contact-list">\n'
        f'          <p class="contact-item">{icon("i-phone")}<span>{esc(person["phone"])}</span></p>\n'
        f'          <p class="contact-item">{icon("i-mail")}<span>{email_html(person["email"])}</span></p>\n'
        f'          <p class="contact-item">{icon("i-pin")}<span>{esc(addr["street"])}<br>'
        f'{esc(addr["postal_code"])} {esc(addr["city"])}</span></p>\n'
        '        </div>\n'
        '        <div class="panel-spacer"></div>\n'
        '        <nav aria-label="Inhalt">\n'
        f'          <p class="label">{icon("i-list")}Inhalt</p>\n'
        '          <ol class="toc-list">\n'
        f'{toc}'
        '          </ol>\n'
        '        </nav>\n'
        '      </aside>\n'
        '      </div>\n\n'
        '      <div class="cover-intro">\n'
        f'        <p class="cover-bio">{esc(bio)}</p>\n'
        f'        <p class="cover-start">{icon("i-calendar")}{esc(start)}</p>\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>\n\n')


def letter_line(icon_name: str | None, text: str, extra: str = '') -> str:
    if not text:
        return '        <span class="letter-line is-empty" aria-hidden="true"></span>\n'
    cls = 'letter-line' + (f' {extra}' if extra else '')
    return f'        <span class="{cls}">{icon(icon_name)}<span>{text}</span></span>\n'


def render_letter(ctx: Ctx, number: int, letter: dict | None, job: dict | None, typ: str) -> str:
    """letter/job None -> Profilvorlage mit Platzhaltern für Empfänger und Text."""
    person = ctx.p['person']
    addr = person['address']
    sig = person.get('signature') or {}
    if job:
        c = job.get('contact', {})
        name = ' '.join(x for x in (c.get('honorific', ''), c.get('name', '')) if x) or c.get('department', '')
        recipient = [
            ('i-building', esc(c.get('company') or job['company']), 'is-org'),
            ('i-user', esc(name), 'is-name'),
            ('i-home', esc(c.get('street', '')), ''),
            ('i-pin', esc(' '.join(x for x in (c.get('postal_code', ''), c.get('city', '')) if x)), ''),
            ('i-phone', esc(c.get('phone', '')), ''),
            ('i-mail', email_html(c['email']) if c.get('email') else '', ''),
        ]
        meta = letter['meta']
        place = meta.get('ort') or addr['city']
        date = german_date(meta.get('datum') or today())
        kicker = meta.get('betreff_einleitung') or SUBJECT_KICKER[typ]
        title = meta.get('betreff') or job.get('occupation') or job.get('apprenticeship', '')
        ref = job.get('reference_number')
        ref_html = (f'      <span class="subject-ref">Ihre Anzeige bei der Bundesagentur für Arbeit, '
                    f'Ref.-Nr. {esc(ref)}</span>\n') if ref else ''
        dense = ' is-dense' if meta.get('dichte', 'normal') in ('dicht', 'dense') else ''
        paras = ''.join(f'      <p>{esc(x)}</p>\n' for x in letter['paragraphs'])
    else:
        recipient = [('i-building', '[EMPFÄNGER_FIRMA]', 'is-org'), ('i-user', '[EMPFÄNGER_ANREDE_NAME]', 'is-name'),
                     ('i-home', '[EMPFÄNGER_STRASSE]', ''), ('i-pin', '[EMPFÄNGER_PLZ_ORT]', ''),
                     ('i-phone', '[EMPFÄNGER_TELEFON]', ''), ('i-mail', '[EMPFÄNGER_EMAIL]', '')]
        place, date = addr['city'], '[DATUM]'
        kicker, title = '[BETREFF-EINLEITUNG]', '[BERUF]'
        ref_html = '      <span class="subject-ref">Ihre Anzeige bei der Bundesagentur für Arbeit, Ref.-Nr. [REFERENZNUMMER]</span>\n'
        dense = ''
        paras = ''.join(f'      <p>{x}</p>\n' for x in (
            '[ANREDE],', '[EINSTIEG MIT BELEGTEM UNTERNEHMENSBEZUG]', '[BELEGTE STÄRKE MIT KURZEM BEISPIEL]',
            '[PASSUNG ZUR STELLE UND ZUM UNTERNEHMEN]', '[AUSBILDUNGSSTAND UND START]',
            '[BITTE UM GESPRÄCH]', 'Mit freundlichen Grüßen'))
    sender_name = ' '.join(x for x in (person.get('salutation', ''), person['name']) if x)
    sender = [None, ('i-user', esc(sender_name), 'is-name'), ('i-home', esc(addr['street']), ''),
              ('i-pin', esc(f'{addr["postal_code"]} {addr["city"]}'), ''), ('i-phone', esc(person['phone']), ''),
              ('i-mail', email_html(person['email']), '')]
    sig_img = ''
    if sig.get('valid') and sig.get('consent') and sig.get('file'):
        sig_img = (f'      <img class="signature-img" src="{esc(ctx.src(sig["file"], "person.signature.file"))}" '
                   f'alt="Unterschrift {esc(person["name"])}">\n')
    return (
        '  <!-- Anschreiben -->\n'
        '  <section class="page letter-page" data-section="2" data-slot="letter" aria-labelledby="letter-title">\n'
        + section_head('anschreiben', number, False) + '\n'
        '    <div class="letter-head">\n'
        '      <address class="letter-party" aria-label="Empfänger">\n'
        + ''.join(letter_line(i, t, e) for i, t, e in recipient) +
        '      </address>\n'
        '      <address class="letter-party" aria-label="Absender">\n'
        + ''.join(letter_line(*s) if s else letter_line(None, '') for s in sender) +
        '      </address>\n'
        '    </div>\n'
        f'    <p class="letter-date">{icon("i-calendar")}{esc(place)}, {esc(date)}</p>\n\n'
        '    <div class="letter-subject">\n'
        f'      <span class="subject-kicker">{esc(kicker)}</span>\n'
        f'      <span class="subject-title">{esc(title)}</span>\n'
        f'{ref_html}'
        '    </div>\n'
        f'    <div class="letter-copy{dense}">\n'
        f'{paras}'
        '    </div>\n'
        '    <div class="signature">\n'
        f'{sig_img}'
        f'      <div class="signature-name"><strong>{esc(person["name"])}</strong>{esc(addr["city"])}</div>\n'
        '    </div>\n'
        '  </section>\n\n')


def render_motivation(ctx: Ctx, number: int, mot: dict | None) -> str:
    person = ctx.p['person']
    if mot:
        lead = esc(mot['lead'])
        dense = ' is-dense' if mot['meta'].get('dichte', 'normal') in ('dicht', 'dense') else ''
        paras = ''.join(f'          <p>{esc(x)}</p>\n' for x in mot['paragraphs'])
        proofs = ''.join(
            f'        <div class="proof-item">{icon(pi)}<div><strong>{esc(t)}</strong><span>{esc(d)}</span></div></div>\n'
            for pi, t, d in mot['proofs'])
    else:
        lead = '[PERSÖNLICHER EINSTIEG IN EINEM SATZ]'
        dense = ''
        paras = ''.join(f'          <p>{x}</p>\n' for x in (
            '[AUSGANGSPUNKT UND PERSÖNLICHER WEG]', '[PRÄGENDE ERFAHRUNG MIT EIGENER ROLLE UND ERGEBNIS]',
            '[WARUM DAS THEMA AUCH AUSSERHALB DER PFLICHT BESCHÄFTIGT]',
            '[BELEGTER BEZUG ZUR STELLE UND ZUM UNTERNEHMEN]', '[AUSBLICK UND RUHIGER ABSCHLUSS]',
            'Mit freundlichen Grüßen'))
        proofs = ''.join(
            f'        <div class="proof-item">{icon(pi)}<div><strong>{t}</strong><span>{d}</span></div></div>\n'
            for pi, t, d in (('i-server', '[PROJEKT 1]', '[BELEGTE TECHNIK UND ERGEBNIS]'),
                             ('i-branch', '[PROJEKT 2]', '[EIGENE ROLLE UND ERGEBNIS]'),
                             ('i-layers', '[LERNPROJEKT]', '[AKTUELLER LERNSTAND]')))
    return (
        '  <!-- Motivationsschreiben -->\n'
        '  <section class="page" data-section="4" data-slot="motivation" aria-labelledby="motivation-title">\n'
        + section_head('motivationsschreiben', number, False) + '\n'
        f'    <p class="motivation-lead">{lead}</p>\n'
        '    <div class="motivation-layout">\n'
        '      <div>\n'
        f'        <div class="motivation-copy{dense}">\n'
        f'{paras}'
        '        </div>\n'
        '        <div class="signature">\n'
        f'          <div class="signature-name"><strong>{esc(person["name"])}</strong>{esc(person["address"]["city"])}</div>\n'
        '        </div>\n'
        '      </div>\n'
        '      <aside class="motivation-aside" aria-label="Belege aus eigenen Projekten">\n'
        f'        <p class="label">{icon("i-badge")}Belege</p>\n'
        f'{proofs}'
        '      </aside>\n'
        '    </div>\n'
        '  </section>\n\n')


def cv_hero(ctx: Ctx) -> str:
    p = ctx.p
    person, addr = p['person'], p['person']['address']
    goal = p.get('portfolio', {}).get('cv_goal') or f'Ausbildungsziel: {p["goal"]["apprenticeship"]}'
    facts = [f'        <li>{icon("i-pin")}<span>{esc(addr["street"])}<br>{esc(addr["postal_code"])} {esc(addr["city"])}</span></li>',
             f'        <li>{icon("i-mail")}<span>{email_html(person["email"])}</span></li>',
             f'        <li>{icon("i-phone")}<span>{esc(person["phone"])}</span></li>']
    if p['presentation'].get('show_birth_data'):
        if person.get('birth_date'):
            facts.append(f'        <li>{icon("i-cake")}<span>{esc(short_date(person["birth_date"]))}</span></li>')
        if person.get('birth_place'):
            facts.append(f'        <li>{icon("i-map")}<span>{esc(person["birth_place"])}</span></li>')
    return ('    <div class="cv-hero">\n'
            '      <div>\n'
            f'        <p class="cv-name">{esc(person["name"])}</p>\n'
            f'        <p class="cv-goal">{esc(goal)}</p>\n'
            '      </div>\n'
            '      <ul class="cv-facts" aria-label="Persönliche Daten">\n'
            + '\n'.join(facts) + '\n'
            '      </ul>\n'
            '    </div>\n\n')


def newest_first(entries: list[dict]) -> list[dict]:
    """Lebenslauf-Reihenfolge: neueste Station zuerst (nach Beginn); ohne Beginn bleibt die Profilreihenfolge."""
    return sorted(entries, key=lambda e: (e.get('date_range') or {}).get('start') or '', reverse=True)


def cv_experience(ctx: Ctx) -> str:
    items = []
    for e in newest_first(ctx.p['experience']):
        kind = KIND_LABEL.get(e['kind'], 'Sonstiges')
        if e.get('employment_type'):
            kind += f' ({e["employment_type"]})'
        role = ' · '.join(x for x in (e.get('role', ''), kind) if x)
        text = '; '.join(e.get('tasks', []))
        text_html = f'<p class="timeline-text">{esc(text)}</p>' if text else ''
        items.append('      <article class="timeline-item">\n'
                     f'        <p class="timeline-date">{esc(fmt_range(e["date_range"]))}</p>\n'
                     f'        <div class="timeline-content"><h4>{esc(e["organization"])}</h4>'
                     f'<p class="timeline-place">{esc(e["city"])}</p><p class="timeline-role">{esc(role)}</p>'
                     f'{text_html}</div>\n'
                     '      </article>\n')
    return ('    <section class="cv-section" aria-labelledby="experience-title">\n'
            f'      <h3 class="cv-section-head" id="experience-title">{icon("i-briefcase")}Praktische Erfahrung</h3>\n'
            + ''.join(items) + '    </section>\n\n')


def cv_education(ctx: Ctx) -> str:
    items = []
    for e in newest_first(ctx.p['education']):
        if e.get('show_in_cv') is False:  # z. B. Grundschulen nach einem weiterführenden Abschluss; bleibt im Profil
            continue
        place = e['city'] + (f' ({e["country"]})' if e.get('country') and e['country'] != 'Deutschland' else '')
        program = e.get('program_short') or e.get('program', '')
        text = ''
        if e.get('qualification'):
            text = f'Abschluss: {e["qualification"]}'
            end = e['date_range'].get('end')
            if e.get('expected') and end:
                text += f', voraussichtlich {fmt_point(end, e["date_range"].get("precision", "month"))}'
        text_html = f'<p class="timeline-text">{esc(text)}</p>' if text else ''
        items.append('      <article class="timeline-item">\n'
                     f'        <p class="timeline-date">{esc(fmt_range(e["date_range"]))}</p>\n'
                     f'        <div class="timeline-content"><h4>{esc(e["institution"])}</h4>'
                     f'<p class="timeline-place">{esc(place)}</p><p class="timeline-role">{esc(program)}</p>'
                     f'{text_html}</div>\n'
                     '      </article>\n')
    return ('    <section class="cv-section" aria-labelledby="education-title">\n'
            f'      <h3 class="cv-section-head" id="education-title">{icon("i-graduation")}Schulbildung</h3>\n'
            + ''.join(items) + '    </section>\n\n')


def address_warnings(profile: dict, job: dict | None = None) -> list[str]:
    """Adressregel: Straße ausgeschrieben („Straße“, nicht „Str.“), Straße und „PLZ Ort“ ohne Punkt und Komma am Ende."""
    streets = [('Profil', profile['person']['address'].get('street', ''))]
    if job:
        streets.append(('Empfänger (job.json)', (job.get('contact') or {}).get('street', '')))
    out = []
    for who, street in streets:
        if re.search(r'(?i)str\.|\bstr\b', street) or street.rstrip() != street.rstrip(' ,.'):
            out.append(f'Warnung: Straße „{street}“ ({who}) ausschreiben („Straße“), ohne Punkt und Komma am Ende.')
    return out


def level_label(item: dict) -> str:
    return 'Muttersprache' if item.get('level') == 'native' else SCALE_LABEL[item['scale']]


def cv_languages(ctx: Ctx) -> str:
    rows = ''.join(
        f'        <div class="language"><span class="language-name">{esc(l["name"])}</span>'
        f'{bars(l["scale"], label=level_label(l))}<span class="language-level">{esc(level_label(l))}</span></div>\n'
        for l in ctx.p['skills']['languages'])
    return ('    <section class="cv-section" aria-labelledby="languages-title">\n'
            f'      <h3 class="cv-section-head" id="languages-title">{icon("i-globe")}Sprachen</h3>\n'
            '      <div class="language-list">\n' + rows + '      </div>\n'
            '    </section>\n')


def chip(c: dict) -> str:
    if c.get('logo'):
        return f'<span class="tech">{logo(c["logo"])}{esc(c["name"])}</span>'
    if c.get('icon'):
        return f'<span class="tech">{icon(c["icon"])}{esc(c["name"])}</span>'
    return f'<span class="tech">{esc(c["name"])}</span>'


def cv_skills(ctx: Ctx) -> str:
    groups = []
    for g in ctx.p['skills']['groups']:
        rows = []
        for it in g['items']:
            chips = it.get('chips') or [{'name': x.strip()} for x in it.get('evidence', '').split(',') if x.strip()]
            # Zusatz unter dem Zeilennamen: Profilwert (auch leer = keiner); ohne Angabe „Lernstand“ bei level learning.
            # Bei future (Lernwunsch) nie ein Zusatz: die Skala zeigt es.
            note_text = it['note'] if 'note' in it else ('Lernstand' if it.get('level') == 'learning' else '')
            note = f'<small>{esc(note_text)}</small>' if note_text else ''
            rows.append(f'        <div class="skill-row"><span class="skill-name">{esc(it.get("label") or it["name"])}{note}</span>'
                        f'<span class="skill-chips">{"".join(chip(c) for c in chips)}</span>'
                        f'{bars(it["scale"], future=it.get("level") == "future")}</div>\n')
        groups.append('      <div class="skill-group">\n'
                      f'        <p class="skill-head">{icon(g["icon"])}{esc(g["name"])}</p>\n'
                      + ''.join(rows) + '      </div>\n')
    legend = ''.join(f'        <span class="scale-item">{bars(s, future=s == 1, aria=False)}{SCALE_LABEL[s]}</span>\n'
                     for s in range(1, 6))
    return ('    <section class="skills-band" aria-labelledby="skills-title">\n'
            f'      <h3 class="cv-section-head" id="skills-title">{icon("i-wrench")}Fähigkeiten</h3>\n'
            + ''.join(groups) +
            '      <div class="skill-legend" aria-label="Skala">\n' + legend + '      </div>\n'
            '    </section>\n')


def cv_projects(ctx: Ctx) -> str:
    """Optionaler Block „Eigene Projekte“ (Homelab): nur Projekte mit show_in_cv: true, Reihenfolge wie im Profil."""
    items = []
    for pr in ctx.p.get('projects', []):
        if not pr.get('show_in_cv'):
            continue
        date = fmt_range(pr['date_range']) if pr.get('date_range') else ''
        if not date and (pr.get('date_range') or {}).get('is_current'):
            date = 'laufend'
        text = pr.get('cv_summary') or pr.get('own_role', '')
        chips = pr.get('chips') or [{'name': x} for x in pr.get('tools', [])]
        text_html = f'<p class="timeline-text">{esc(text)}</p>' if text else ''
        chips_html = (f'<p class="skill-chips timeline-chips">{"".join(chip(c) for c in chips)}</p>' if chips else '')
        items.append('      <article class="timeline-item">\n'
                     f'        <p class="timeline-date">{esc(date)}</p>\n'
                     f'        <div class="timeline-content"><h4>{esc(pr["name"])}</h4>{text_html}{chips_html}</div>\n'
                     '      </article>\n')
    if not items:
        return ''
    conf = ctx.p['presentation'].get('cv_projects') or {}
    title = conf.get('title') or 'Eigene Projekte'
    ico = conf.get('icon') or 'i-layers'
    return ('    <section class="cv-section" aria-labelledby="projects-title">\n'
            f'      <h3 class="cv-section-head" id="projects-title">{icon(ico)}{esc(title)}</h3>\n'
            + ''.join(items) + '    </section>\n\n')


CV_BLOCKS = {'experience': cv_experience, 'education': cv_education, 'projects': cv_projects,
             'skills': cv_skills, 'languages': cv_languages}
# Lesereihenfolge (Runde 5): Erfahrung, Schulbildung, Fähigkeiten, Sprachen. Sprachen nie vor Schulbildung oder
# Fähigkeiten. „projects“ (optional) darf überall nach der Erfahrung stehen, wo es auf die Seiten passt.
CV_ORDER = ['experience', 'education', 'skills', 'languages']


def render_cv_page(ctx: Ctx, number: int, blocks: list[str], index: int, compact: bool) -> str:
    cls = 'page cv-compact' if compact else 'page'
    aria = 'cv-title' if index == 0 else f'cv{index + 1}-title'
    comment = '  <!-- Lebenslauf -->\n' if index == 0 else '  <!-- Lebenslauf, Fortsetzung -->\n'
    body = cv_hero(ctx) if index == 0 else ''
    for b in blocks:
        if b not in CV_BLOCKS:
            raise BuildError(f'Unbekannter Lebenslauf-Block „{b}“ in presentation.cv_layout')
        body += CV_BLOCKS[b](ctx)
    return (comment + f'  <section class="{cls}" data-section="3" aria-labelledby="{aria}">\n'
            + section_head('lebenslauf', number, index > 0, index - 1 if index else 0) + '\n'
            + body + '  </section>\n\n')


def evidence_card(ctx: Ctx, ev: dict | None, section: str) -> str:
    if ev is None:
        title = 'Zertifikat' if section == 'zertifikate' else 'Zeugnis'
        return ('      <article class="evidence-card">\n'
                f'        <div class="evidence-meta"><h3>{title}</h3><p>Liegt noch nicht vor</p></div>\n'
                '        <div class="document-stage"><div class="document-placeholder">Liegt noch nicht vor</div></div>\n'
                '      </article>\n')
    field = f'evidence[{ev["id"]}].file'
    path = resolve_asset(ctx.pdir, ev['file'], field)
    if path.suffix.lower() not in IMAGE_EXT:
        raise BuildError(f'Nachweis {ev["id"]}: {ev["file"]} ist kein Bild. PDF-Nachweise vorher als PNG '
                         'rendern (z. B. pdftoppm -png -r 150) und das Bild als file eintragen.')
    return ('      <article class="evidence-card">\n'
            f'        <div class="evidence-meta"><h3>{esc(ev["title"])}</h3><p>{esc(ev["issuer"])}</p></div>\n'
            f'        <div class="document-stage"><img src="{esc(ctx.src(ev["file"], field))}" alt="{esc(ev["title"])}"></div>\n'
            f'        <div class="document-caption"><span class="caption-note">{icon("i-scan")}'
            f'{ORIGINAL_LABEL.get(ev["original"], "Nachweis")}</span><span class="caption-date">Ausgestellt am '
            f'{esc(short_date(ev["date"]))}</span></div>\n'
            '      </article>\n')


def evidence_groups(profile: dict, section: str) -> list[list]:
    kinds = {'zertifikate': ('certificate',), 'zeugnisse': ('school_report', 'work_reference')}[section]
    items = [e for e in profile.get('evidence', [])
             if e['kind'] in kinds and e.get('show_in_portfolio') and e.get('valid')]
    groups, i = [], 0
    while i < len(items):
        if items[i].get('pair') and i + 1 < len(items) and items[i + 1].get('pair'):
            groups.append(items[i:i + 2])
            i += 2
        else:
            groups.append([items[i]])
            i += 1
    return groups or [[None]]


def render_evidence_page(ctx: Ctx, number: int, section: str, group: list, index: int) -> str:
    sec_no, prefix, title, _ = SECTION_META[section]
    aria = f'{prefix}-title' if index == 0 else f'{prefix}{index + 1}-title'
    grid = 'evidence-grid is-pair' if len(group) == 2 else 'evidence-grid'
    comment = f'  <!-- {title}{", Fortsetzung" if index else ""} -->\n'
    return (comment + f'  <section class="page" data-section="{sec_no}" aria-labelledby="{aria}">\n'
            + section_head(section, number, index > 0, index - 1 if index else 0)
            + f'    <div class="{grid}">\n' + ''.join(evidence_card(ctx, ev, section) for ev in group)
            + '    </div>\n  </section>\n\n')


def plan_pages(profile: dict) -> list[dict]:
    layout = profile['presentation'].get('cv_layout') or {}
    cv_pages = layout.get('pages') or [['experience', 'education', 'skills', 'languages']]
    flat = [b for page in cv_pages for b in page]
    known = [b for b in flat if b in CV_ORDER]
    if known != sorted(known, key=CV_ORDER.index) or (
            'projects' in flat and 'experience' in flat and flat.index('projects') < flat.index('experience')):
        print('Warnung: presentation.cv_layout weicht von der Lesereihenfolge ab '
              f'({", ".join(CV_ORDER)}; projects nach experience); Sprachen gehören hinter Schulbildung und '
              'Fähigkeiten.', file=sys.stderr)
    if 'projects' in flat and not any(p.get('show_in_cv') for p in profile.get('projects', [])):
        print('Hinweis: Block „projects“ in cv_layout, aber kein Projekt mit show_in_cv: true; der Block entfällt.',
              file=sys.stderr)
    plan = [{'section': 'deckblatt'}, {'section': 'anschreiben'}]
    compact = layout.get('compact')  # true/false für alle Seiten oder Liste je Seite (Runde 5)
    per_page = compact if isinstance(compact, list) else [bool(compact)] * len(cv_pages)
    plan += [{'section': 'lebenslauf', 'blocks': b, 'index': i,
              'compact': bool(per_page[i]) if i < len(per_page) else False}
             for i, b in enumerate(cv_pages)]
    plan.append({'section': 'motivationsschreiben'})
    for sec in ('zertifikate', 'zeugnisse'):
        plan += [{'section': sec, 'group': g, 'index': i} for i, g in enumerate(evidence_groups(profile, sec))]
    for n, page in enumerate(plan, 1):
        page['number'] = n
        page['continuation'] = page.get('index', 0) > 0
    return plan


def build_document(ctx: Ctx, letter=None, mot=None, job=None, typ='apprenticeships') -> tuple[str, list[dict]]:
    tpl = template_text()
    plan = plan_pages(ctx.p)
    starts = {}
    for page in plan:
        starts.setdefault(page['section'], page['number'])
    parts = [template_head(tpl, f'Bewerbungsmappe – {ctx.p["person"]["name"]}'), screen_chrome(starts)]
    for page in plan:
        s, n = page['section'], page['number']
        if s == 'deckblatt':
            parts.append(render_cover(ctx, starts))
        elif s == 'anschreiben':
            parts.append(render_letter(ctx, n, letter, job, typ))
        elif s == 'lebenslauf':
            parts.append(render_cv_page(ctx, n, page['blocks'], page['index'], page['compact']))
        elif s == 'motivationsschreiben':
            parts.append(render_motivation(ctx, n, mot))
        else:
            parts.append(render_evidence_page(ctx, n, s, page['group'], page['index']))
    doc = ''.join(parts).rstrip() + '\n</body>\n</html>\n'
    pages = [{'number': p['number'], 'section': p['section'], **({'continuation': True} if p['continuation'] else {})}
             for p in plan]
    return doc, pages


# --------------------------------------------------------------------------- Texte (Markdown)

def parse_front_matter(text: str) -> tuple[dict, str]:
    meta = {}
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ':' in line and not line.strip().startswith('#'):
                    k, v = line.split(':', 1)
                    meta[k.strip().lower()] = v.strip()
            text = text[end + 4:]
    return meta, text


def paragraphs(text: str) -> list[str]:
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    out = []
    for block in re.split(r'\n\s*\n', text):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip() and not l.lstrip().startswith('#')]
        if lines:
            out.append(' '.join(lines))
    return out


def sections_md(text: str) -> dict:
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r'#+\s*(.+?)\s*$', line)
        if m:
            cur = m.group(1).strip().lower()
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: '\n'.join(v) for k, v in out.items()}


def read_letter(path: Path) -> dict:
    if not path.is_file():
        raise BuildError(f'Text fehlt: {rel(path)}')
    meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
    paras = paragraphs(body)
    if not paras:
        raise BuildError(f'{rel(path)} enthält keinen Brieftext')
    return {'meta': meta, 'paragraphs': paras}


def read_motivation(path: Path) -> dict:
    if not path.is_file():
        raise BuildError(f'Text fehlt: {rel(path)}')
    meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
    secs = sections_md(body)
    lead = ' '.join(paragraphs(secs.get('einstieg', '')))
    paras = paragraphs(secs.get('text', ''))
    proofs = []
    for line in secs.get('belege', '').splitlines():
        line = line.strip()
        if line.startswith(('-', '*')):
            cells = [c.strip() for c in line[1:].split('|')]
            if len(cells) == 3:
                proofs.append(tuple(cells))
            elif cells != ['']:
                raise BuildError(f'{rel(path)}: Belegzeile braucht „- i-icon | Titel | Text“: {line}')
    if not lead or not paras:
        raise BuildError(f'{rel(path)} braucht die Abschnitte „## Einstieg“ und „## Text“')
    return {'meta': meta, 'lead': lead, 'paragraphs': paras, 'proofs': proofs}


def word_count(paras: list[str]) -> int:
    return sum(len(re.findall(r'\S+', p)) for p in paras)


# --------------------------------------------------------------------------- Chromium und QA

def chrome() -> str:
    for c in (os.environ.get('CHROME'), 'chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable'):
        if c and shutil.which(c):
            return shutil.which(c)
    raise BuildError('Kein Chromium gefunden. CHROME=/pfad/zu/chromium setzen.')


def chrome_cmd(*args: str) -> list[str]:
    return [chrome(), '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
            '--run-all-compositor-stages-before-draw', '--virtual-time-budget=6000', *args]


def print_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(chrome_cmd('--no-pdf-header-footer', f'--print-to-pdf={pdf_path}', html_path.resolve().as_uri()),
                   check=True, capture_output=True)
    if not pdf_path.is_file():
        raise BuildError(f'PDF-Export fehlgeschlagen: {pdf_path}')


def pdf_pages(pdf_path: Path) -> int | None:
    if shutil.which('pdfinfo'):
        out = subprocess.run(['pdfinfo', str(pdf_path)], capture_output=True, text=True).stdout
        m = re.search(r'^Pages:\s+(\d+)', out, re.M)
        if m:
            return int(m.group(1))
    n = len(re.findall(rb'/Type\s*/Page(?![s\w])', pdf_path.read_bytes()))
    return n or None


# Füllgrad je Seite (nach dem QA-Snippet, Desktop 1440 px): Anteil des Satzspiegels, den der Inhalt belegt.
# Richtwert für Lebenslauf-Seiten 90–98 %; negativer Rest = Überlauf. Grundlage der Regel in references/template.md.
FILL_SNIPPET = '''const mm = 96 / 25.4, fill = [...document.querySelectorAll('.page')].map((p, i) => {
    const r = p.getBoundingClientRect(), cs = getComputedStyle(p);
    const top = r.top + parseFloat(cs.paddingTop), bottom = r.bottom - parseFloat(cs.paddingBottom);
    let low = top;
    for (const e of p.querySelectorAll('*')) {
      if (e.closest('.folio, svg, .section-head')) continue;
      const b = e.getBoundingClientRect();
      if (b.width > 0 && b.height > 0) low = Math.max(low, b.bottom);
    }
    return [i + 1, Math.round(100 * (low - top) / (bottom - top)), Math.round((bottom - low) / mm * 10) / 10];
  });
'''


IFRAME_PROBE = '''<!doctype html><meta charset="utf-8"><style>html,body{{margin:0}}iframe{{display:block;border:0;width:{w}px;height:{h}px}}</style>
<iframe id="f" src="{src}"></iframe>
<script>
document.getElementById("f").addEventListener("load", () => setTimeout(() => {{
  try {{
    const f = document.getElementById("f"), d = f.contentDocument, w = f.contentWindow.innerWidth;
    document.body.setAttribute("data-qa", JSON.stringify({{width: w, hscroll: d.documentElement.scrollWidth - w}}));
  }} catch (e) {{}}
}}, 300));
</script>
'''


def run_qa(html_path: Path, ignore_slots: bool = False) -> dict:
    html_path = html_path.resolve()
    tpl = template_text()
    src = html_path.read_text(encoding='utf-8')
    probe = ('<script>\naddEventListener("load", () => { const r = ' + qa_snippet(tpl) + ';\n' + FILL_SNIPPET +
             'document.body.setAttribute("data-qa", JSON.stringify({hits: r, hscroll: '
             'document.documentElement.scrollWidth - innerWidth, pages: document.querySelectorAll(".page").length, '
             'fill: fill, cv: [...document.querySelectorAll(".page")].flatMap((p, i) => p.dataset.section === "3" ? [i + 1] : [])})); });\n</script>\n</body>')
    qa_file = html_path.with_name(f'.qa-{os.getpid()}-{html_path.name}')
    result = {}
    try:
        qa_file.write_text(src.replace('</body>', probe, 1), encoding='utf-8')
        for key, size in QA_VIEWPORTS:
            width, height = (int(x) for x in size.split(','))
            if width >= 1000:
                dom = subprocess.run(chrome_cmd(f'--window-size={size}', '--dump-dom', qa_file.as_uri()),
                                     capture_output=True, text=True).stdout
            else:
                # Headless-Chromium erzwingt mindestens ca. 500 px Fensterbreite: schmale Breiten über einen iframe
                # exakter Breite messen (Media-Queries gelten für den iframe-Viewport).
                wrap = html_path.with_name(f'.qa-{os.getpid()}-{key}.html')
                wrap.write_text(IFRAME_PROBE.format(src=quote(html_path.name), w=width, h=height), encoding='utf-8')
                try:
                    dom = subprocess.run(chrome_cmd('--allow-file-access-from-files', f'--window-size={max(width, 500)},{height}',
                                                    '--dump-dom', wrap.as_uri()), capture_output=True, text=True).stdout
                finally:
                    wrap.unlink(missing_ok=True)
            m = re.search(r'data-qa="([^"]*)"', dom)
            data = json.loads(html.unescape(m.group(1))) if m else None
            if data is not None and width < 1000 and data.get('width') != width:
                data = None  # Breite nicht wie angefordert: Messung ungültig
            result[key] = data
    finally:
        qa_file.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / 'qa.pdf'
        print_pdf(html_path, pdf)
        a4_pages = pdf_pages(pdf)
    scan = strip_slots(src) if ignore_slots else src
    body = re.sub(r'<!--.*?-->', '', scan.split('<div class="screen-bar', 1)[-1], flags=re.S)
    placeholders = sorted(set(re.findall(r'\[[A-ZÄÖÜ][^\]\n<>]{1,80}\]', body)))
    missing = []
    for s in re.findall(r'<img[^>]+src="([^"]+)"', body):
        if not re.match(r'(data|https?):', s) and not (html_path.parent / html.unescape(s)).is_file():
            missing.append(html.unescape(s))
    contract = template_classes(tpl)
    unknown = sorted({c for attr in re.findall(r'class="([^"]*)"', body) for c in attr.split()} - contract)
    desktop = result.get('desktop') or {}
    hits = desktop.get('hits') if desktop else None
    page_count = desktop.get('pages') if desktop else None
    qa = {
        'overflow': hits if hits is not None else ['QA-Lauf fehlgeschlagen'],
        'overflow_pages': sorted({int(h.split(':')[0]) for h in hits or [] if h.split(':')[0].isdigit()}),
        'fill': desktop.get('fill') or [],
        'cv_pages': desktop.get('cv') or [],
        'html_pages': page_count,
        'a4_pages': a4_pages,
        'hscroll': {'1440': desktop.get('hscroll'), '390': (result.get('mobile') or {}).get('hscroll'),
                    '375': (result.get('mobile_375') or {}).get('hscroll')},
        'placeholders': placeholders,
        'missing_assets': missing,
        'unknown_classes': unknown,
    }
    qa['hscroll_mobile'] = max((v for k, v in qa['hscroll'].items() if k != '1440' and v is not None), default=None)
    # None = Messung fehlgeschlagen: zählt als Fehler
    widths_ok = all(v is not None and v <= 0 for v in qa['hscroll'].values())
    qa['ok'] = hits == [] and a4_pages == page_count and not placeholders and not missing and widths_ok
    return qa


def cv_fill(qa: dict) -> str:
    """Füllgrad der Lebenslauf-Seiten (data-section 3) als Text, leer wenn nicht messbar."""
    rows = [r for r in qa.get('fill') or [] if r[0] in (qa.get('cv_pages') or [])]
    return ' · '.join(f'S{n} {pct} % ({rest:+.1f} mm)' for n, pct, rest in rows)


def print_qa(name: str, qa: dict, extra: list[str] | None = None) -> None:
    print(f'QA {name}: {"OK" if qa["ok"] else "PROBLEME"}')
    print(f'  Seiten: HTML {qa["html_pages"]}, A4-PDF {qa["a4_pages"]}')
    print(f'  Überlauf: {qa["overflow"] or "keiner"}')
    cv = cv_fill(qa)
    if cv:
        print(f'  Füllgrad Lebenslauf: {cv} (Richtwert 90–98 %, Rest in mm bis zum unteren Rand)')
    print('  Horizontaler Überlauf (px): ' + ' · '.join(
        f'{w}: {v if v is not None else "nicht messbar"}' for w, v in qa['hscroll'].items()))
    if qa['placeholders']:
        print(f'  Offene Platzhalter: {", ".join(qa["placeholders"])}')
    if qa['missing_assets']:
        print(f'  Fehlende Bilder: {", ".join(qa["missing_assets"])}')
    if qa['unknown_classes']:
        print(f'  Hinweis: Klassen nicht in der Vorlage: {", ".join(qa["unknown_classes"])}')
    for line in extra or []:
        print(f'  {line}')


# --------------------------------------------------------------------------- Befehle

def load_profile(pdir: Path) -> dict:
    return read_json(profile_json_path(pdir))


def cmd_profile_template(args) -> int:
    pdir = Path(args.dir).resolve()
    if pdir.parent != PROFILE_ROOT.resolve():
        pdir = profile_dir_of(pdir)
    profile = load_profile(pdir)
    check_profile_assets(profile, pdir)
    out = profile_template_path(pdir)
    ctx = Ctx(profile, pdir, out.parent)
    doc, pages = build_document(ctx)
    out.write_text(doc, encoding='utf-8')
    print(f'Profilvorlage: {rel(out)} ({len(pages)} Seiten)')
    hidden = [e['institution'] for e in profile.get('education', []) if e.get('show_in_cv') is False]
    if hidden:
        print(f'  Im Lebenslauf ausgeblendet (show_in_cv: false): {", ".join(hidden)}')
    for w in address_warnings(profile):
        print(f'  {w}')
    if args.qa:
        qa = run_qa(out, ignore_slots=True)
        print_qa(rel(out), qa, ['Platzhalter in Anschreiben und Motivationsschreiben sind in der Profilvorlage gewollt.'])
        if not qa['ok']:
            return 2
    if args.pdf:
        pdf = out.with_suffix('.pdf')
        print_pdf(out, pdf)
        print(f'A4-Vorschau: {rel(pdf)} ({pdf_pages(pdf)} Seiten)')
    return 0


def slot_span(doc: str, slot: str) -> tuple[int, int] | None:
    """Start (inkl. Kommentarzeile davor) und Ende einer <section data-slot="…"> samt folgender Leerzeilen."""
    m = re.search(rf'<section [^>]*data-slot="{slot}"[^>]*>', doc)
    if not m:
        return None
    start = doc.rfind('\n', 0, m.start()) + 1
    prev = doc.rfind('\n', 0, start - 1) + 1
    if doc[prev:start].strip().startswith('<!--') and doc[prev:start].strip().endswith('-->'):
        start = prev
    depth, end = 0, None
    for t in re.finditer(r'<(/?)section\b[^>]*>', doc[m.start():]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            end = m.start() + t.end()
            break
    if end is None:
        raise BuildError(f'Bereich data-slot="{slot}" ist nicht geschlossen')
    while end < len(doc) and doc[end] == '\n':
        end += 1
    return start, end


def replace_slot(doc: str, slot: str, new: str) -> str:
    span = slot_span(doc, slot)
    if not span:
        raise BuildError(f'Profilvorlage hat keinen Bereich data-slot="{slot}". Profilvorlage neu bauen.')
    return doc[:span[0]] + new + doc[span[1]:]


def strip_slots(doc: str) -> str:
    for slot in ('letter', 'motivation'):
        span = slot_span(doc, slot)
        if span:
            doc = doc[:span[0]] + doc[span[1]:]
    return doc


def localize_assets(doc: str, src_dir: Path, app_dir: Path, pdir: Path) -> tuple[str, list[tuple[str, Path]]]:
    """Kopiert alle lokal referenzierten Bilder nach application/assets/ und schreibt die Pfade um.

    Jedes Bild muss (aufgelöst) unter profile/<name>/assets/ liegen. Zwei verschiedene Quelldateien mit
    gleichem Dateinamen sind ein Fehler (kein stilles Überschreiben)."""
    copied = []
    assets = app_dir / 'assets'
    allowed = (pdir / 'assets').resolve()
    names: dict[str, Path] = {}

    def repl(m):
        src = html.unescape(m.group(1))
        if re.match(r'(data|https?):|#', src) or src.startswith('assets/'):
            return m.group(0)
        path = (src_dir / src).resolve()
        if allowed not in path.parents:
            raise BuildError(f'Bild aus der Profilvorlage liegt nicht unter {rel(allowed)}/: {src}. '
                             'Profilvorlage neu bauen; Profilfelder mit Dateipfaden prüfen.')
        if not path.is_file():
            raise BuildError(f'Bild aus der Profilvorlage fehlt: {src}')
        if names.setdefault(path.name, path) != path:
            raise BuildError(f'Namenskollision in application/assets/: „{path.name}“ kommt aus {rel(names[path.name])} '
                             f'und {rel(path)}. Eine der Dateien umbenennen (Profilfelder anpassen), neu bauen.')
        assets.mkdir(parents=True, exist_ok=True)
        target = assets / path.name
        if not target.exists() or target.read_bytes() != path.read_bytes():
            shutil.copy2(path, target)
        copied.append((f'assets/{path.name}', path))
        return f'src="assets/{esc(path.name)}"'

    return re.sub(r'src="([^"]+)"', repl, doc), copied


def asset_entries(profile: dict, pdir: Path, copied: list[tuple[str, Path]]) -> list[dict]:
    by_path = {}
    for ev in profile.get('evidence', []):
        sec = 'zertifikate' if ev['kind'] == 'certificate' else 'zeugnisse'
        by_path[resolve_asset(pdir, ev['file'], f'evidence[{ev["id"]}].file')] = ('evidence', sec, ev)
    sig = profile['person'].get('signature') or {}
    if sig.get('file'):
        by_path[resolve_asset(pdir, sig['file'], 'person.signature.file')] = ('signature', 'anschreiben', None)
    photo = profile['person'].get('photo') or {}
    if photo.get('file'):
        by_path[resolve_asset(pdir, photo['file'], 'person.photo.file')] = ('photo', 'deckblatt', None)
    out, seen = [], set()
    for file, src in copied:
        if file in seen:
            continue
        seen.add(file)
        role, sec, ev = by_path.get(src.resolve(), ('evidence', 'zertifikate', None))
        entry = {'file': file, 'kind': 'image', 'section': sec, 'role': role, 'source': rel(src)}
        if ev:
            entry['evidence_id'] = ev['id']
            entry['caption'] = ev['title']
        out.append(entry)
    return out


@contextmanager
def ledger_lock(pdir: Path):
    """Exklusive Sperre für Lese-Ändern-Schreiben des Ledgers (parallele Builds)."""
    lock = ledger_path(pdir).with_name('.ledger.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, 'w') as fh:
        try:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX)
        except ImportError:  # Windows: ohne Sperre
            pass
        yield


def load_ledger(pdir: Path) -> dict:
    path = ledger_path(pdir)
    if path.is_file():
        return read_json(path)
    return {'schema_version': '1.0', 'profile': pdir.name, 'entries': []}


def find_entry(ledger: dict, folder: str, refnr: str | None) -> dict | None:
    for e in ledger['entries']:
        if e.get('folder') == folder or (refnr and e.get('reference_number') == refnr):
            return e
    return None


def upsert_ledger(info: dict, job: dict, manifest: dict) -> None:
    with ledger_lock(info['profile_dir']):
        _upsert_ledger(info, job, manifest)


def _upsert_ledger(info: dict, job: dict, manifest: dict) -> None:
    pdir = info['profile_dir']
    ledger = load_ledger(pdir)
    refnr = job.get('reference_number')
    entry = find_entry(ledger, info['folder'], refnr)
    if entry is None:
        entry = {'id': refnr or info['folder'].split('/')[-1], 'created_at': manifest.get('created_at', today()),
                 'history': [{'date': today(), 'status': manifest['status'], 'note': 'angelegt'}]}
        ledger['entries'].append(entry)
    c = job.get('contact', {})
    contact = {k: v for k, v in (('name', ' '.join(x for x in (c.get('honorific', ''), c.get('name', '')) if x)),
                                 ('email', c.get('email', '')), ('phone', c.get('phone', ''))) if v}
    search = job.get('search', {})
    entry.update({
        'reference_number': refnr or '',
        'company': job['company'],
        'title': job['title'],
        'occupation': job.get('occupation', ''),
        'type': info['type'],
        'folder': info['folder'],
        'search_city': search.get('city', ''),
        'rank': search.get('rank'),
        'status': manifest['status'],
        'channel': entry.get('channel') or job.get('application', {}).get('method', 'unknown'),
        'contact': contact,
        'application_email': job.get('application', {}).get('email', ''),
        'source_url': job.get('source', {}).get('url', ''),
    })
    order = ['id', 'reference_number', 'company', 'title', 'occupation', 'type', 'folder', 'search_city', 'rank',
             'status', 'created_at', 'html_approved_at', 'pdf_exported_at', 'sent_at', 'channel', 'contact',
             'application_email', 'source_url', 'notes', 'history']
    ordered = {k: entry[k] for k in order if entry.get(k) is not None}
    ordered.update({k: v for k, v in entry.items() if k not in ordered and v is not None})
    entry.clear()
    entry.update(ordered)
    write_json(ledger_path(pdir), ledger)


def cmd_application(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    pdir, user = info['profile_dir'], info['user']
    profile = load_profile(pdir)
    check_profile_assets(profile, pdir)
    tpl_path = profile_template_path(pdir)
    if not tpl_path.is_file():
        raise BuildError(f'Profilvorlage fehlt: {rel(tpl_path)}. Zuerst: build_mappe.py profile-template {rel(pdir)}')
    if tpl_path.stat().st_mtime < profile_json_path(pdir).stat().st_mtime:
        print('Warnung: Das Profil ist neuer als die Profilvorlage. Profilvorlage neu bauen und vom Nutzer prüfen lassen.',
              file=sys.stderr)
    job = read_json(posting / 'job_information' / 'job.json')
    letter = read_letter(posting / 'text_generation' / 'anschreiben.md')
    mot = read_motivation(posting / 'text_generation' / 'motivationsschreiben.md')
    app_dir = posting / 'application'
    app_dir.mkdir(parents=True, exist_ok=True)
    out = app_dir / html_name(user)

    doc = tpl_path.read_text(encoding='utf-8')
    ctx = Ctx(profile, pdir, tpl_path.parent)
    starts = dict(re.findall(r'data-section="(\d)"[^>]*>\s*<header class="section-head">\s*<h2 id="[a-z]+-title">'
                             r'[^<]*</h2>\s*<span class="folio" aria-label="Seite (\d+)"', doc))
    letter_no = int(starts.get('2', 2))
    mot_no = int(starts.get('4', 4))
    doc = replace_slot(doc, 'letter', render_letter(ctx, letter_no, letter, job, info['type']))
    doc = replace_slot(doc, 'motivation', render_motivation(ctx, mot_no, mot))
    doc, copied = localize_assets(doc, tpl_path.parent, app_dir, pdir)
    changed = not out.is_file() or out.read_text(encoding='utf-8') != doc
    out.write_text(doc, encoding='utf-8')

    pages = []
    for m in re.finditer(r'<section class="page[^"]*" data-section="(\d)"[^>]*>\s*<header class="section-head">\s*'
                         r'<h2[^>]*>(.*?)</h2>\s*<span class="folio" aria-label="Seite (\d+)"', doc):
        page = {'number': int(m.group(3)), 'section': SECTIONS[int(m.group(1)) - 1]}
        if 'class="continued"' in m.group(2):
            page['continuation'] = True
        pages.append(page)
    if not doc.count('cover-page"'):
        raise BuildError('Deckblatt fehlt in der Profilvorlage')
    pages.insert(0, {'number': 1, 'section': 'deckblatt'})

    man_path = app_dir / 'application-manifest.json'
    manifest = read_json(man_path) if man_path.is_file() else {'status': 'draft', 'created_at': today()}
    manifest.update({
        'profile': user,
        'type': info['type'],
        'reference_number': job.get('reference_number', ''),
        'company': job['company'],
        'role': job.get('occupation') or job.get('apprenticeship') or job['title'],
        'html': out.name,
        'email_draft': 'email.md',
        'sections': SECTIONS,
        'pages': pages,
        'assets': asset_entries(profile, pdir, copied),
    })
    manifest.setdefault('created_at', today())
    manifest.setdefault('status', 'draft')
    if changed and manifest['status'] in ('html_approved', 'pdf_exported'):
        print('Hinweis: Die Mappe war freigegeben. Nach Änderungen muss der Nutzer sie erneut freigeben; '
              'Status zurück auf draft.', file=sys.stderr)
        manifest['status'] = 'draft'
        for k in ('approved_at', 'pdf', 'pdf_exported_at'):
            manifest.pop(k, None)
    words_letter, words_mot = word_count(letter['paragraphs']), word_count(mot['paragraphs'])
    print(f'Mappe: {rel(out)} ({len(pages)} Seiten)')
    notes = [f'Wörter Anschreiben: {words_letter} (Richtwert normal ≤ {LETTER_WORDS["normal"]}, '
             f'dicht ≤ {LETTER_WORDS["dicht"]})',
             f'Wörter Motivationsschreiben: {words_mot} (Richtwert normal ≤ {MOTIVATION_WORDS["normal"]}, '
             f'dicht ≤ {MOTIVATION_WORDS["dicht"]})']
    notes += address_warnings(profile, job)
    email_state, email_msg = email_draft_state(posting)
    if email_msg:
        notes.append(f'FEHLER: {email_msg} Blockiert Freigabe und PDF, nicht das Bauen.')
    salutation = (job.get('contact') or {}).get('salutation')
    if salutation and not letter['paragraphs'][0].startswith(salutation):
        notes.append(f'Warnung: Anrede im Anschreiben weicht von job.json ab („{salutation}“).')
    rc = 0
    if args.qa:
        qa = run_qa(out)
        qa['ok'] = qa['ok'] and email_state in ('ok', 'not_required')
        print_qa(rel(out), qa, notes)
        manifest['validation'] = {
            'placeholders_remaining': len(qa['placeholders']),
            'overflow': qa['overflow'],
            'overflow_pages': qa['overflow_pages'],
            'html_pages': qa['html_pages'],
            'a4_pages': qa['a4_pages'],
            'hscroll_mobile': qa['hscroll_mobile'],
            'hscroll': qa['hscroll'],
            'email_draft': email_state,
            'cv_fill': cv_fill(qa),
            'missing_assets': qa['missing_assets'],
            'words_letter': words_letter,
            'words_motivation': words_mot,
            'checked_at': now_iso(),
        }
        rc = 0 if qa['ok'] else 2
    else:
        for n in notes:
            print(f'  {n}')
    if args.pdf:
        if manifest['status'] not in ('html_approved', 'pdf_exported', 'sent'):
            write_json(man_path, manifest)
            upsert_ledger(info, job, manifest)
            raise BuildError('Kein PDF: Die HTML-Fassung ist nicht freigegeben. Erst nach dem ausdrücklichen Ja des '
                             f'Nutzers: build_mappe.py status "{rel(posting)}" html_approved')
        if email_msg:
            write_json(man_path, manifest)
            upsert_ledger(info, job, manifest)
            raise BuildError(f'Kein PDF: {email_msg}')
        if rc:
            raise BuildError('Kein PDF: Die QA meldet Probleme.')
        pdf = app_dir / html_name(user, 'pdf')
        print_pdf(out, pdf)
        stamp = now_iso()
        manifest.update({'status': 'pdf_exported', 'pdf': pdf.name, 'pdf_exported_at': stamp})
        print(f'PDF: {rel(pdf)} ({pdf_pages(pdf)} Seiten)')
        write_json(man_path, manifest)
        with ledger_lock(pdir):
            _upsert_ledger(info, job, manifest)
            _status_history(info, job, argparse.Namespace(status='pdf_exported', channel=None, note=None), stamp)
        return rc
    write_json(man_path, manifest)
    upsert_ledger(info, job, manifest)
    return rc


def cmd_qa(args) -> int:
    html_path = Path(args.html)
    qa = run_qa(html_path)
    extra, email_ok = [], True
    if html_path.resolve().parent.name == 'application':
        try:
            state, msg = email_draft_state(html_path.resolve().parent.parent)
        except (BuildError, OSError, ValueError):
            state, msg = 'not_required', ''
        if msg:
            extra.append(f'FEHLER: {msg}')
            email_ok = False
    qa['ok'] = qa['ok'] and email_ok
    print_qa(args.html, qa, extra)
    return 0 if qa['ok'] else 2


def cmd_preview(args) -> int:
    src = Path(args.html).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stem = slugify(src.stem) or 'mappe'
    pdf = out / f'{stem}.pdf'
    print_pdf(src, pdf)
    print(f'Vorschau-PDF: {pdf} ({pdf_pages(pdf)} Seiten)')
    if shutil.which('pdftoppm'):
        subprocess.run(['pdftoppm', '-r', str(args.dpi), '-png', str(pdf), str(out / stem)], check=True)
        print(f'Seitenbilder: {out}/{stem}-*.png')
    else:
        print('pdftoppm nicht gefunden: keine PNG-Seiten (PDF im Browser ansehen).')
    return 0


def cmd_validate(args) -> int:
    try:
        import jsonschema  # optional, nicht Teil der Standardbibliothek
    except ImportError:
        print('Das Paket jsonschema fehlt. Einmalig: python3 -m venv .tmp/venv && .tmp/venv/bin/pip install jsonschema '
              '&& .tmp/venv/bin/python tools/build_mappe.py validate …')
        return 3
    path = Path(args.dir).resolve()
    pdir = profile_dir_of(path)
    checks = []
    if path == pdir:
        checks.append((profile_json_path(pdir), 'profile.schema.json'))
        if ledger_path(pdir).is_file():
            checks.append((ledger_path(pdir), 'ledger.schema.json'))
        for job in sorted((pdir / 'applications').rglob('job_information/job.json')):
            checks.append((job, 'job.schema.json'))
        for man in sorted((pdir / 'applications').rglob('application/application-manifest.json')):
            checks.append((man, 'application-manifest.schema.json'))
    else:
        checks += [(path / 'job_information' / 'job.json', 'job.schema.json'),
                   (path / 'application' / 'application-manifest.json', 'application-manifest.schema.json')]
    bad = 0
    postings = ([job.parent.parent for job in sorted((pdir / 'applications').rglob('job_information/job.json'))]
                if path == pdir else [path])
    if path == pdir and profile_json_path(pdir).is_file():
        try:
            check_profile_assets(load_profile(pdir), pdir)
            print(f'ok      Asset-Pfade unter {rel(pdir / "assets")}/')
        except BuildError as e:
            print(f'FEHLER  {e}')
            bad += 1
    for file, schema in checks:
        if not file.is_file():
            print(f'fehlt   {rel(file)}')
            bad += 1
            continue
        validator = jsonschema.Draft202012Validator(read_json(SCHEMAS / schema),
                                                    format_checker=jsonschema.FormatChecker())
        errors = sorted(validator.iter_errors(read_json(file)), key=lambda e: list(e.path))
        print(f'{"ok    " if not errors else "FEHLER"}  {rel(file)}')
        for e in errors[:20]:
            print(f'        {"/".join(str(x) for x in e.path) or "(root)"}: {e.message}')
        bad += bool(errors)
    for posting in postings:
        state, msg = email_draft_state(posting)
        if state == 'ok':
            print(f'ok      {rel(posting / "application" / "email.md")}')
        elif msg:
            print(f'FEHLER  {msg}')
            bad += 1
    return 1 if bad else 0


def cmd_check_duplicate(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    job = read_json(posting / 'job_information' / 'job.json')
    refnr = job.get('reference_number')
    key = (job['company'].strip().lower(), job['title'].strip().lower())
    dups = []
    for e in load_ledger(info['profile_dir'])['entries']:
        if e.get('folder') == info['folder']:
            continue
        if (refnr and e.get('reference_number') == refnr) or \
                (e.get('company', '').strip().lower(), e.get('title', '').strip().lower()) == key:
            dups.append(e)
    if not dups:
        print('Kein Duplikat im Ledger.')
        return 0
    for e in dups:
        print(f'DUPLIKAT: {e.get("reference_number") or "-"} · {e["company"]} · {e["title"]} · Status {e["status"]} · '
              f'{e["folder"]}')
    return 3


def cmd_status(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if args.status not in STATUSES:
        raise BuildError(f'Status muss einer von {", ".join(STATUSES)} sein')
    if args.status == 'sent' and not getattr(args, 'from_mark_sent', False):
        raise BuildError('Status „sent“ nur über mark-sent: build_mappe.py mark-sent "<stellenordner>" '
                         '--channel email|post|portal (verschiebt den Ordner nach applications/sent/ und '
                         'aktualisiert das Ledger in einem Schritt).')
    if args.status == 'html_approved':
        _, email_msg = email_draft_state(posting)
        if email_msg:
            print(f'Warnung: {email_msg} Das PDF wird erst mit Entwurf erzeugt.', file=sys.stderr)
    man_path = posting / 'application' / 'application-manifest.json'
    manifest = read_json(man_path)
    job = read_json(posting / 'job_information' / 'job.json')
    stamp = (dt.datetime.fromisoformat(args.date).astimezone().replace(microsecond=0).isoformat()
             if args.date else now_iso())
    manifest['status'] = args.status
    if args.status == 'html_approved':
        manifest['approved_at'] = stamp
    if args.status == 'sent':
        manifest['sent_at'] = stamp
    if args.channel:
        manifest['channel'] = args.channel
    write_json(man_path, manifest)
    with ledger_lock(info['profile_dir']):
        _upsert_ledger(info, job, manifest)
        _status_history(info, job, args, stamp)
    print(f'Status {args.status}: {info["folder"]}')
    return 0


def _status_history(info: dict, job: dict, args, stamp: str) -> None:
    ledger = load_ledger(info['profile_dir'])
    entry = find_entry(ledger, info['folder'], job.get('reference_number'))
    date_key = {'html_approved': 'html_approved_at', 'pdf_exported': 'pdf_exported_at', 'sent': 'sent_at'}.get(args.status)
    if date_key:
        entry[date_key] = stamp[:10]
    if args.channel:
        entry['channel'] = args.channel
    entry.setdefault('history', []).append({'date': stamp[:10], 'status': args.status,
                                            **({'note': args.note} if args.note else {})})
    write_json(ledger_path(info['profile_dir']), ledger)


def cmd_mark_sent(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if info['sent']:
        raise BuildError('Diese Bewerbung liegt bereits unter applications/sent/.')
    manifest = read_json(posting / 'application' / 'application-manifest.json')
    if manifest['status'] not in ('pdf_exported', 'html_approved'):
        raise BuildError(f'Status ist {manifest["status"]}: erst freigeben und PDF exportieren.')
    if not (posting / 'application' / html_name(info['user'], 'pdf')).is_file():
        print('Warnung: Kein PDF im Bewerbungsordner gefunden.', file=sys.stderr)
    parts = info['folder'].split('/')
    target = info['profile_dir'] / 'applications' / 'sent' / Path(*parts[1:])
    if target.exists():
        raise BuildError(f'Ziel existiert bereits: {rel(target)}')
    job = read_json(posting / 'job_information' / 'job.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(posting), str(target))
    stop = info['profile_dir'] / 'applications' / info['type']
    for parent in posting.parents:
        if parent == stop or stop not in parent.parents or any(parent.iterdir()):
            break
        parent.rmdir()
    new_folder = '/'.join(['applications', 'sent', *parts[1:]])
    with ledger_lock(info['profile_dir']):
        ledger = load_ledger(info['profile_dir'])
        entry = find_entry(ledger, info['folder'], job.get('reference_number'))
        if entry:
            entry['folder'] = new_folder
            write_json(ledger_path(info['profile_dir']), ledger)
    args.dir, args.status, args.from_mark_sent = str(target), 'sent', True
    cmd_status(args)
    print(f'Verschoben nach {rel(target)}')
    return 0


def cmd_stats(args) -> int:
    pdir = Path(args.dir).resolve()
    if pdir.parent != PROFILE_ROOT.resolve():
        pdir = profile_dir_of(pdir)
    entries = load_ledger(pdir)['entries']
    print(f'Bewerbungen von {pdir.name}: {len(entries)}')
    for title, counter in (('Status', Counter(e['status'] for e in entries)),
                           ('Typ', Counter(e['type'] for e in entries)),
                           ('Angelegt pro Monat', Counter(e.get('created_at', '')[:7] for e in entries)),
                           ('Gesendet pro Monat', Counter(e['sent_at'][:7] for e in entries if e.get('sent_at'))),
                           ('Kanal (gesendet)', Counter(e.get('channel', '') for e in entries if e.get('sent_at')))):
        if counter:
            print(f'{title}: ' + ', '.join(f'{k or "-"} {v}' for k, v in sorted(counter.items())))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('profile-template'); s.add_argument('dir'); s.add_argument('--qa', action='store_true')
    s.add_argument('--pdf', action='store_true'); s.set_defaults(fn=cmd_profile_template)
    s = sub.add_parser('application'); s.add_argument('dir'); s.add_argument('--qa', action='store_true')
    s.add_argument('--pdf', action='store_true'); s.set_defaults(fn=cmd_application)
    s = sub.add_parser('qa'); s.add_argument('html'); s.set_defaults(fn=cmd_qa)
    s = sub.add_parser('preview'); s.add_argument('html'); s.add_argument('out')
    s.add_argument('--dpi', type=int, default=70); s.set_defaults(fn=cmd_preview)
    s = sub.add_parser('validate'); s.add_argument('dir'); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser('check-duplicate'); s.add_argument('dir'); s.set_defaults(fn=cmd_check_duplicate)
    s = sub.add_parser('status'); s.add_argument('dir'); s.add_argument('status')
    s.add_argument('--channel', choices=['email', 'post', 'portal']); s.add_argument('--date')
    s.add_argument('--note'); s.set_defaults(fn=cmd_status)
    s = sub.add_parser('mark-sent'); s.add_argument('dir')
    s.add_argument('--channel', choices=['email', 'post', 'portal'], required=True); s.add_argument('--date')
    s.add_argument('--note'); s.set_defaults(fn=cmd_mark_sent)
    s = sub.add_parser('stats'); s.add_argument('dir'); s.set_defaults(fn=cmd_stats)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except BuildError as e:
        print(f'Fehler: {e}', file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f'Fehler beim Aufruf von {e.cmd[0]}: {e.stderr or e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
