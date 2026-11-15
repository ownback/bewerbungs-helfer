#!/usr/bin/env python3
"""Bewerbungsmappe bauen, prüfen und verwalten (nur Python-Standardbibliothek).

Das Skript enthält keine persönlichen Daten und kein HTML. Es liest das Profil, die Stelle und die Texte aus
dem gitignorierten Ordner profile/<vorname.nachname>/, baut daraus ein View-Model (dict) und rendert es mit den
Quellen der Vorlage unter .agents/skills/bewerbungshelfer/assets/mappe/: Partials (Markup), CSS, Symbole,
Schrift. Jede Ausgabe ist eine eigenständige HTML-Datei. Aufbau und Regeln: references/template.md.

Befehle:
  master [--check]
      Baut die Master-Vorlage assets/bewerbungsmappe.html aus assets/mappe/ und dem Platzhalter-Modell
      master.json. --check vergleicht nur (Exit 2, wenn die Datei nicht aktuell ist).
  profile-template <profil-ordner> [--qa[=fast]] [--pdf]
      Baut assets/profile/<name>_template.html aus <name>_profile.json und den Assets.
      --pdf schreibt die A4-Vorschau <name>_template.pdf daneben.
  application <stellen-ordner> [--qa[=fast]] [--pdf]
      Baut application/bewerbungsmappe - <name>.html aus den Quellen: Profil, job_information/job.json,
      text_generation/anschreiben.md (Kopf mit „datum: JJJJ-MM-TT“ ist Pflicht) und motivationsschreiben.md.
      Aktualisiert application-manifest.json und ledger.json.
      --pdf exportiert das finale A4-PDF: nur mit voller QA, bei Status html_approved oder später, wenn die
      Mappe der Prüfsumme der Freigabe entspricht und das Briefdatum höchstens 7 Tage alt ist.
  qa <html> [--fast]             Überlauf-, Platzhalter-, Seiten- und Breitenprüfung (1440/390/375 px,
                                 Headless-Chromium); bei Bewerbungsweg „email“ auch der E-Mail-Entwurf.
                                 --fast bzw. --qa=fast: ohne A4-PDF, für die Schleife beim Ändern der Vorlage.
  preview <html> <ausgabe-ordner> A4-Vorschau als PDF und PNG-Seiten (PNG nur mit pdftoppm).
  snapshot --save|--compare <html>… [--name N] [--tolerance 0–255]
      Seitenbilder (A4, 50 dpi, Graustufen) unter .tmp/snapshots/ sichern bzw. mit der Sicherung vergleichen:
      Anteil geänderter Fläche und Bereich je Seite. Exit 2, wenn sich eine Seite geändert hat.
  rebuild --check <ziel>…
      Prüft, dass gespeicherte Dateien Byte für Byte dem entsprechen, was ihre Quellen jetzt ergeben. Ziel:
      „master“, ein Profilordner (Profilvorlage und alle gebauten Mappen) oder ein Stellenordner. Exit 2 bei
      Abweichung. Schreibt nichts.
  contract
      Vertrag zwischen View-Model, Partials und CSS, aus den Dateien abgeleitet: je Partial data-part,
      Schlüssel, Klassen, eingebundene Partials; dazu Klassen ohne CSS-Regel. Exit 1 bei einem Verstoß.
  validate <profil-|stellen-ordner>  JSON-Schemaprüfung (tools/schema_lite.py, ohne Installation), Asset-Pfade,
      bei Bewerbungsweg „email“ der E-Mail-Entwurf application/email.md und offene blockierende Fragen
      (job.json open_questions: severity blocking + status open).
  check-duplicate <stellen-ordner>   Stelle gegen alle erfassten Stellenordner prüfen: same_posting (Exit 3),
      same_role_other_site und same_employer_other_role (Hinweis, Exit 0).
  ledger sync <profil-ordner>    Ledger aus den Stellenordnern ableiten (idempotent, stellt es auch neu her).
  status <profil-ordner>         Übersicht: eine Zeile pro Stelle (Status, Frist, Bewerbungsweg, offene
                                 blockierende Fragen, nächster Schritt). Gleicht vorher das Ledger ab.
  status <stellen-ordner> <status>   Status in Manifest und Ledger setzen (nicht „sent“: dafür mark-sent;
                                 nicht „dropped“: dafür drop).
  mark-sent <stellen-ordner> --channel email|post|portal [--date JJJJ-MM-TT]
      Ordner nach applications/sent/<typ>/… verschieben und Ledger aktualisieren.
  drop <stellen-ordner> --reason "…" [--date JJJJ-MM-TT]
      Stelle aussortieren: Ordner nach applications/dropped/<typ>/… verschieben, Grund in DROPPED.txt.
  restore <stellen-ordner>       Aussortierte Stelle zurückholen (Gegenstück zu drop).
  stats <profil-ordner>          Kennzahlen aus dem Ledger (Status, Typ, Monat).

Chromium wird über $CHROME oder chromium/chromium-browser/google-chrome gesucht.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
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

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Schwestermodule, auch bei Import aus einem anderen Ordner
import schema_lite  # noqa: E402
from mustache_lite import TAG, Renderer, RenderError  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents' / 'skills' / 'bewerbungshelfer'
TEMPLATE = SKILL / 'assets' / 'bewerbungsmappe.html'  # Master-Vorlage: gebaut aus MAPPE (Befehl master)
MAPPE = SKILL / 'assets' / 'mappe'          # Quellen der Vorlage: CSS, Symbole, Partials, QA-Sonde
PARTIALS = MAPPE / 'partials'               # Markup, ein Partial pro Datei (Mustache-Teilmenge, mustache_lite.py)
MASTER_MODEL = MAPPE / 'master.json'        # Platzhalter-Modell der Master-Vorlage und der Profilvorlage
CSS_FILES = ('tokens.css', 'mappe.css', 'screen.css')  # in dieser Reihenfolge im <style> (Kaskade)
FONT_DIR = SKILL / 'assets' / 'fonts'
QA_PAGE = MAPPE / 'qa.html'                 # Prüfstand, lädt qa.js
SCHEMAS = SKILL / 'assets' / 'schemas'
PROFILE_ROOT = ROOT / 'profile'

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']
SCALE_LABEL = {1: 'Lernwunsch', 2: 'Grundkenntnisse', 3: 'sicher', 4: 'routiniert', 5: 'sehr sicher'}
KIND_LABEL = {'internship': 'Praktikum', 'employment': 'Anstellung', 'volunteer': 'Ehrenamt', 'other': 'Sonstiges'}
ORIGINAL_LABEL = {'scan': 'Original-Scan', 'copy': 'Kopie', 'digital_original': 'Digitales Original',
                  'unknown': 'Nachweis'}
SECTIONS = ['deckblatt', 'anschreiben', 'lebenslauf', 'motivationsschreiben', 'zertifikate', 'zeugnisse']
SECTION_META = {  # section -> (data-section, id prefix, Titel, Kurzname für Registerreiter und Navigation)
    'deckblatt': (1, 'cover', 'Deckblatt', 'Deckblatt'),
    'anschreiben': (2, 'letter', 'Anschreiben', 'Anschreiben'),
    'lebenslauf': (3, 'cv', 'Lebenslauf', 'Lebenslauf'),
    'motivationsschreiben': (4, 'motivation', 'Motivationsschreiben', 'Motivation'),
    'zertifikate': (5, 'cert', 'Zertifikate', 'Zertifikate'),
    'zeugnisse': (6, 'reference', 'Zeugnisse', 'Zeugnisse'),
}
# Abschnitt -> Partial, das seine Seiten zeichnet (assets/mappe/partials/<name>.html)
PAGE_PARTIAL = {'deckblatt': 'cover', 'anschreiben': 'letter', 'lebenslauf': 'cv',
                'motivationsschreiben': 'motivation', 'zertifikate': 'evidence', 'zeugnisse': 'evidence'}
PAGE_KINDS = ('cover', 'letter', 'cv', 'motivation', 'evidence')
TYPES = ['apprenticeships', 'jobs', 'internships']
# Reihenfolge und Bedeutung: references/applications.md, Abschnitt Status
STATUSES = ['captured', 'draft', 'html_approved', 'pdf_exported', 'sent', 'interview', 'offer', 'rejected',
            'withdrawn', 'dropped']
MANIFEST_STATUSES = STATUSES[1:-1]  # captured und dropped ergeben sich aus dem Ordner, nicht aus dem Manifest
AREAS = ('sent', 'dropped')         # Ablagen unter applications/<ablage>/<typ>/…
DROP_FILE = 'DROPPED.txt'           # Zeile 1: Grund; „Datum: JJJJ-MM-TT“
# Rechtsformen, die beim Firmenvergleich der Duplikatprüfung entfallen (nach slugify)
LEGAL_FORMS = {'gmbh', 'ggmbh', 'mbh', 'ag', 'se', 'kg', 'kgaa', 'co', 'ohg', 'ug', 'eg', 'ev', 'ek', 'gbr', 'aoer'}
SUBJECT_KICKER = {
    'apprenticeships': 'Bewerbung um einen Ausbildungsplatz als',
    'jobs': 'Bewerbung als',
    'internships': 'Bewerbung um einen Praktikumsplatz als',
}
LIMITS_FILE = MAPPE / 'limits.json'         # Zahlen und Grenzen; das Skript enthält keine davon (limit())
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
QA_MODES = ('full', 'fast')  # --qa = full; --qa=fast ohne A4-PDF (Schleife beim Ändern der Vorlage)


class BuildError(Exception):
    pass


_LIMITS: dict = {}


def limit(key: str):
    """Wert aus assets/mappe/limits.json, z. B. limit('letter.words') oder limit('letter.max_age_days')."""
    if not _LIMITS:
        try:
            _LIMITS.update(json.loads(LIMITS_FILE.read_text(encoding='utf-8')))
        except (OSError, ValueError) as e:
            raise BuildError(f'Grenzwerte nicht lesbar: {LIMITS_FILE.relative_to(ROOT)} ({e})')
    node = _LIMITS
    for part_ in key.split('.'):
        if not isinstance(node, dict) or part_ not in node:
            raise BuildError(f'Grenzwert „{key}“ fehlt in {LIMITS_FILE.relative_to(ROOT)}')
        node = node[part_]
    return node


def qa_viewports() -> list[tuple[str, str]]:
    """Bildschirmbreiten der QA als (Schlüssel, „Breite,Höhe“): zuerst Desktop (Überlauf, Füllgrad), dann mobil."""
    return [(key, f'{w},{h}') for key, (w, h) in limit('qa.viewports').items()]


# --------------------------------------------------------------------------- Hilfen

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
    area = parts[1] if len(parts) > 1 and parts[1] in AREAS else ''
    if len(parts) < (6 if area else 5) or parts[0] != 'applications':
        raise BuildError(f'{posting} ist kein Stellenordner '
                         '(applications/[sent/|dropped/]<typ>/<beruf>/<suchort>/<NN-ort-firma>/)')
    typ = parts[2] if area else parts[1]
    if typ not in TYPES:
        raise BuildError(f'Unbekannter Typ „{typ}“ im Pfad {posting}')
    return {'profile_dir': pdir, 'user': pdir.name, 'type': typ, 'sent': area == 'sent',
            'dropped': area == 'dropped', 'folder': '/'.join(parts)}


def html_name(user: str, ext: str = 'html') -> str:
    return f'bewerbungsmappe - {user}.{ext}'


# --------------------------------------------------------------------------- Vorlage (Quellen unter assets/mappe/)

def read_source(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        raise BuildError(f'Quelle der Vorlage fehlt: {rel(path)}')


def partial_sources() -> dict[str, str]:
    return {p.stem: read_source(p) for p in sorted(PARTIALS.glob('*.html'))}


def stylesheet() -> str:
    return ''.join(read_source(MAPPE / name) for name in CSS_FILES)


def font_css() -> str:
    """fonts.css mit den Schriftdateien aus assets/fonts/ als Base64 (Platzhalter = Dateiname ohne Endung)."""
    fonts = {p.stem: base64.b64encode(p.read_bytes()).decode('ascii') for p in sorted(FONT_DIR.glob('*.woff2'))}
    return Renderer({'fonts': read_source(MAPPE / 'fonts.css')}).render('fonts', fonts)


def symbol_table() -> dict[str, str]:
    """id -> Zeile aller Symbole in icons.svg (ein <symbol> pro Zeile), in Dateireihenfolge."""
    table = {}
    for line in read_source(MAPPE / 'icons.svg').splitlines():
        m = re.match(r'<symbol id="([^"]+)"', line)
        if m:
            table[m.group(1)] = line
    return table


def symbol_lines(body: str) -> list[str]:
    """Nur die Symbole, die das Dokument verwendet. Ein Verweis ohne Symbol ist ein Fehler."""
    used = set(re.findall(r'<use href="#([^"]+)"', body))
    table = symbol_table()
    missing = sorted(used - set(table))
    if missing:
        raise BuildError(f'Symbol fehlt in {rel(MAPPE / "icons.svg")}: {", ".join(missing)}. Icon-Ids im Profil und in '
                         'den Texten prüfen (references/template.md, Icons und Logos).')
    return [line for sid, line in table.items() if sid in used]


def render_document(title: str, chrome: dict, pages: list[dict]) -> str:
    """View-Model -> eine eigenständige HTML-Datei: Partials, CSS, Schrift und die verwendeten Symbole."""
    try:
        engine = Renderer(partial_sources())
        body = engine.render('body', {'chrome': chrome, 'pages': pages})
        return engine.render('document', {'title': title, 'css': stylesheet(), 'fonts': font_css(),
                                          'symbols': symbol_lines(body), 'body': body})
    except RenderError as e:
        raise BuildError(f'Vorlage unter {rel(MAPPE)}: {e}')


def css_classes() -> set[str]:
    return set(re.findall(r'\.([a-zA-Z][\w-]*)', re.sub(r'/\*.*?\*/', '', stylesheet(), flags=re.S)))


def partial_classes(source: str) -> set[str]:
    """Klassen, die ein Partial fest nennt (Mustache-Tags entfernt; Werte aus dem View-Model fehlen hier)."""
    classes: set[str] = set()
    for attr in re.findall(r'class="([^"]*)"', source):
        # Abschnitts-Tags fallen weg, ihr Inhalt bleibt; ein Wert ({{x}}) macht sein Wort unvollständig: auslassen
        plain = TAG.sub(lambda m: '' if m.group(2) in ('#', '^', '/', '!') else '\0', attr)
        classes.update(c for c in plain.split() if re.fullmatch(r'[a-zA-Z][\w-]*', c))
    return classes


def known_classes() -> set[str]:
    return css_classes().union(*(partial_classes(s) for s in partial_sources().values()))


# --------------------------------------------------------------------------- View-Model
#
# Jede Funktion baut ein dict für genau ein Partial und kein HTML. Der Renderer bricht ab, wenn ein Partial einen
# Schlüssel nennt, den das dict nicht hat: Jeder Schlüssel ist deshalb immer gesetzt, notfalls mit None.
# origin nennt die Inhaltsquelle (data-origin, siehe references/template.md): profile:<Pfad im Profil-JSON>,
# job:<Pfad in job.json>, text:<Datei>#<Stelle>, master:<Pfad in master.json>, build:<Name im Skript>.

def part(text: str, br: bool = False, wbr: bool = False) -> dict:
    return {'text': text, 'br': br, 'wbr': wbr}


def lines(*texts: str) -> list[dict]:
    """Text aus Zeilen für das Partial text: Zeilenumbruch vor jeder Zeile außer der ersten."""
    return [part(t, br=i > 0) for i, t in enumerate(texts)]


def email_parts(addr: str) -> list[dict]:
    """Lange Adressen bekommen eine Umbruchstelle nach @ und vor jedem Punkt der Domain."""
    if len(addr) <= limit('contact.email_wrap_above_chars'):
        return [part(addr)]
    local, _, domain = addr.partition('@')
    first, *rest = domain.split('.')
    return [part(local + '@'), part(first, wbr=True), *(part('.' + x, wbr=True) for x in rest)]


def two_line_place(text: str) -> list[dict]:
    """„Krakau, Polen“ -> Ort und Land untereinander, ohne Komma (wie die Adresszeile). Ohne Komma unverändert."""
    city, sep, country = text.rpartition(',')
    if not sep or not country.strip():
        return lines(text)
    return lines(city.strip(), country.strip())


def field(text: str, origin: str) -> dict:
    return {'text': text, 'origin': origin}


def bars_view(scale, future: bool = False, label: str | None = None, aria: bool = True) -> dict:
    return {'scale': scale, 'future': future, 'label': (label or SCALE_LABEL[scale]) if aria else None}


def scale_legend() -> list[dict]:
    return [{'bars': bars_view(s, future=s == 1, aria=False), 'label': SCALE_LABEL[s]} for s in range(1, 6)]


def chip_view(c: dict) -> dict:
    """Logo geht vor Icon; ohne beides steht nur der Name."""
    logo = c.get('logo') or None
    return {'name': c['name'], 'logo': logo, 'icon': None if logo else (c.get('icon') or None)}


def name_class(first: str, last: str) -> str:
    """Klasse am Namen auf dem Deckblatt nach dem längsten Namensteil (Doppelnamen brechen nach dem Bindestrich)."""
    pieces = []
    for word in f'{first} {last}'.split():
        segs = word.split('-')
        pieces += [s + '-' for s in segs[:-1]] + [segs[-1]]
    longest = max((len(p) for p in pieces), default=0)
    if longest >= limit('cover.name_xlong_from_chars'):
        return 'is-xlong'
    if longest >= limit('cover.name_long_from_chars'):
        return 'is-long'
    return ''


def page_frame(section: str, number: int, index: int = 0) -> dict:
    """Rahmen jeder Seite: Registerspalte, Überschrift-Id, Kommentar, Kopf mit Titel, Reitername und Seitenzahl."""
    sec_no, prefix, title, tab = SECTION_META[section]
    hid = f'{prefix}-title' if index == 0 else f'{prefix}{index + 1}-title'
    return {'section_no': sec_no, 'aria': hid, 'comment': title + (', Fortsetzung' if index else ''),
            'head': {'id': hid, 'title': title, 'tab': tab, 'continued': index > 0, 'number': number}}


def page_entry(section: str, number: int, index: int, content: dict) -> dict:
    """Eintrag in pages: genau ein Schlüssel aus PAGE_KINDS trägt Rahmen und Inhalt, die anderen sind None."""
    entry = dict.fromkeys(PAGE_KINDS)
    entry[PAGE_PARTIAL[section]] = {**page_frame(section, number, index), **content}
    entry['last'] = False
    return entry


def section_starts(plan: list[dict]) -> dict:
    starts: dict[str, int] = {}
    for page in plan:
        starts.setdefault(page['section'], page['number'])
    return starts


def toc_view(starts: dict) -> list[dict]:
    return [{'title': SECTION_META[s][2], 'page': starts[s]} for s in SECTIONS]


def chrome_view(starts: dict) -> dict:
    return {'nav': [{'target': f'{SECTION_META[s][1]}-title', 'label': SECTION_META[s][3], 'page': starts[s]}
                    for s in SECTIONS]}


class Ctx:
    """Profil und Zielordner einer Ausgabe. src() liefert den Bildpfad relativ zur Ausgabedatei.

    bundle (Bewerbung): Bilder werden nach <out_dir>/assets/ kopiert und von dort eingebunden; copied hält
    (Pfad in der Mappe, Quelldatei) in der Reihenfolge der Verwendung fest. dry: nichts schreiben (Vergleich)."""

    def __init__(self, profile: dict, pdir: Path, out_dir: Path, bundle: bool = False, dry: bool = False):
        self.p = profile
        self.pdir = pdir
        self.out_dir = out_dir
        self.bundle = bundle
        self.dry = dry
        self.copied: list[tuple[str, Path]] = []
        self._names: dict[str, Path] = {}

    def src(self, file: str, field: str = 'Asset') -> str:
        path = resolve_asset(self.pdir, file, field)
        if not path.is_file() or path.stat().st_size == 0:
            raise BuildError(f'Asset fehlt oder ist leer: {file}')
        if not self.bundle:
            return Path(os.path.relpath(path, self.out_dir)).as_posix()
        if self._names.setdefault(path.name, path) != path:
            raise BuildError(f'Namenskollision in application/assets/: „{path.name}“ kommt aus '
                             f'{rel(self._names[path.name])} und {rel(path)}. Eine der Dateien umbenennen '
                             '(Profilfelder anpassen), neu bauen.')
        target = self.out_dir / 'assets' / path.name
        if not self.dry and (not target.exists() or target.read_bytes() != path.read_bytes()):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        self.copied.append((f'assets/{path.name}', path))
        return f'assets/{path.name}'


def master_model() -> dict:
    """assets/mappe/master.json, aufbereitet: parts als Liste von Zeilen wird zu Textteilen, und jedes dict
    bekommt origin = sein Pfad in der Datei."""
    data = read_json(MASTER_MODEL)

    def prepare(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'parts' and isinstance(value, list) and all(isinstance(x, str) for x in value):
                    node[key] = lines(*value)
                else:
                    prepare(value, f'{path}.{key}')
            node.setdefault('origin', f'master:{path}')
        elif isinstance(node, list):
            for i, value in enumerate(node):
                prepare(value, f'{path}[{i}]')

    for key in ('pages', 'slots'):
        prepare(data[key], key)
    return data


def cover_view(ctx: Ctx, starts: dict) -> dict:
    p = ctx.p
    person, goal, port = p['person'], p['goal'], p.get('portfolio', {})
    first = person.get('first_name') or person['name'].split()[0]
    last = person.get('last_name') or ' '.join(person['name'].split()[1:])
    addr = person['address']
    photo = None
    ph = person.get('photo', {})
    if ph.get('valid') and ph.get('consent') and ph.get('file'):
        focus = ph.get('focus') or {}
        photo = {'src': ctx.src(ph['file'], 'person.photo.file'),
                 'alt': ph.get('alt') or 'Bewerbungsfoto von ' + person['name'],
                 'style': '; '.join(f'--photo-{k}: {focus[k]}' for k in ('x', 'y', 'zoom') if k in focus),
                 'origin': 'profile:person.photo'}
    if port.get('cover_start'):
        start = field(port['cover_start'], 'profile:portfolio.cover_start')
    else:
        start = field(f'Ausbildung ab {month_year(goal["start"])}' if goal.get('start') else '[AUSBILDUNGSBEGINN]',
                      'profile:goal.start')
    return {
        'name': {'first': first, 'last': last, 'cls': name_class(first, last), 'origin': 'profile:person.name'},
        'role': {'parts': lines(*(port.get('cover_role') or [goal['apprenticeship']])),
                 'origin': 'profile:portfolio.cover_role' if port.get('cover_role') else 'profile:goal.apprenticeship'},
        'photo': photo,
        'phone': field(person['phone'], 'profile:person.phone'),
        'email': {'parts': email_parts(person['email']), 'origin': 'profile:person.email'},
        'address': {'parts': lines(addr['street'], f'{addr["postal_code"]} {addr["city"]}'),
                    'origin': 'profile:person.address'},
        'toc': toc_view(starts),
        'bio': field(port.get('cover_bio')
                     or '[KURZPROFIL: Alter, aktueller Bildungsweg, Zugang zum Beruf und Ausbildungsziel]',
                     'profile:portfolio.cover_bio'),
        'start': start,
    }


def letter_line(icon_name: str, parts: list[dict], cls: str = '') -> dict:
    """Zeile im Briefkopf. Ohne Text bleibt eine leere Ausgleichszeile stehen; nichts wird erfunden."""
    if not any(p['text'] for p in parts):
        return {'empty': True, 'cls': '', 'icon': '', 'parts': []}
    return {'empty': False, 'cls': cls, 'icon': icon_name, 'parts': parts}


def letter_view(ctx: Ctx, letter: dict | None, job: dict | None, typ: str) -> dict:
    """letter/job None -> Profilvorlage: Empfänger und Text sind die Platzhalter aus master.json (slots.letter)."""
    person = ctx.p['person']
    addr = person['address']
    if job:
        c = job.get('contact', {})
        name = ' '.join(x for x in (c.get('honorific', ''), c.get('name', '')) if x) or c.get('department', '')
        meta = letter['meta']
        ref = job.get('reference_number')
        md = 'text:anschreiben.md'
        view = {
            'recipient': {'origin': 'job:contact', 'lines': [
                letter_line('i-building', lines(c.get('company') or job['company']), 'is-org'),
                letter_line('i-user', lines(name), 'is-name'),
                letter_line('i-home', lines(c.get('street', ''))),
                letter_line('i-pin', lines(' '.join(x for x in (c.get('postal_code', ''), c.get('city', '')) if x))),
                letter_line('i-phone', lines(c.get('phone', ''))),
                letter_line('i-mail', email_parts(c['email']) if c.get('email') else lines('')),
            ]},
            'date': {'place': meta.get('ort') or addr['city'], 'date': german_date(meta['datum']),
                     'origin': f'{md}#datum'},
            'kicker': (field(meta['betreff_einleitung'], f'{md}#betreff_einleitung') if meta.get('betreff_einleitung')
                       else field(SUBJECT_KICKER[typ], 'build:SUBJECT_KICKER')),
            'title': (field(meta['betreff'], f'{md}#betreff') if meta.get('betreff')
                      else field(job.get('occupation') or job.get('apprenticeship', ''), 'job:occupation')),
            'ref': field(ref, 'job:reference_number') if ref else None,
            'dense': meta.get('dichte', 'normal') in ('dicht', 'dense'),
            'paragraphs': [field(x, f'{md}#p{i}') for i, x in enumerate(letter['paragraphs'], 1)],
        }
    else:
        slot = master_model()['slots']['letter']
        view = {
            'recipient': slot['recipient'],
            'date': {'place': addr['city'], 'date': slot['date']['text'], 'origin': slot['date']['origin']},
            'kicker': slot['kicker'], 'title': slot['title'], 'ref': slot['ref'],
            'dense': False,
            'paragraphs': slot['paragraphs'],
        }
    sender_name = ' '.join(x for x in (person.get('salutation', ''), person['name']) if x)
    view['sender'] = {'origin': 'profile:person', 'lines': [
        letter_line('', []),  # der Absender hat keine Firmenzeile
        letter_line('i-user', lines(sender_name), 'is-name'),
        letter_line('i-home', lines(addr['street'])),
        letter_line('i-pin', lines(f'{addr["postal_code"]} {addr["city"]}')),
        letter_line('i-phone', lines(person['phone'])),
        letter_line('i-mail', email_parts(person['email'])),
    ]}
    view['signature'] = signature_view(ctx)
    view['signer'] = {'name': person['name'], 'city': addr['city'], 'origin': 'profile:person.name'}
    return view


def signature_view(ctx: Ctx) -> dict | None:
    """Unterschriftsbild für Anschreiben und Lebenslauf: nur mit gültiger, freigegebener Datei."""
    person = ctx.p['person']
    sig = person.get('signature') or {}
    if not (sig.get('valid') and sig.get('consent') and sig.get('file')):
        return None
    return {'src': ctx.src(sig['file'], 'person.signature.file'), 'alt': f'Unterschrift {person["name"]}',
            'origin': 'profile:person.signature'}


def cv_sign_view(ctx: Ctx, letter: dict | None) -> dict:
    """Abschluss des Lebenslaufs: Ort und Datum wie im Anschreiben (Briefdatum der Stelle), Unterschrift, Name.
    letter None -> Profilvorlage: Das Datum ist der Platzhalter aus master.json (slots.cv_sign)."""
    person = ctx.p['person']
    if letter:
        meta = letter['meta']
        date = {'place': meta.get('ort') or person['address']['city'], 'date': german_date(meta['datum']),
                'origin': 'text:anschreiben.md#datum'}
    else:
        slot = master_model()['slots']['cv_sign']['date']
        date = {'place': person['address']['city'], 'date': slot['text'], 'origin': slot['origin']}
    return {'date': date, 'signature': signature_view(ctx),
            'signer': {'name': person['name'], 'origin': 'profile:person.name'}}


def project_photo(ctx: Ctx, title: str) -> dict | None:
    """Projektfoto zu einem Beleg (feste Regel): Projekt mit gleichem Namen (ohne Groß-/Kleinschreibung),
    erstes Bild mit consent und valid. Fehlt eins davon, entsteht kein Foto und kein Platzhalter."""
    for i, pr in enumerate(ctx.p.get('projects') or []):
        if (pr.get('name') or '').strip().casefold() != title.strip().casefold():
            continue
        for j, img in enumerate(pr.get('images') or []):
            if img.get('consent') and img.get('valid') and img.get('file'):
                where = f'projects[{pr.get("id", i)}].images[{j}]'
                return {'src': ctx.src(img['file'], f'{where}.file'), 'alt': 'Projektfoto: ' + pr['name'],
                        'origin': f'profile:{where}'}
        return None
    return None


def motivation_view(ctx: Ctx, mot: dict | None) -> dict:
    """mot None -> Profilvorlage mit den Platzhaltern aus master.json (slots.motivation)."""
    person = ctx.p['person']
    if mot:
        md = 'text:motivationsschreiben.md'
        view = {
            'lead': field(mot['lead'], f'{md}#einstieg'),
            'dense': mot['meta'].get('dichte', 'normal') in ('dicht', 'dense'),
            'paragraphs': [field(x, f'{md}#p{i}') for i, x in enumerate(mot['paragraphs'], 1)],
            'proofs': [{'icon': ico, 'title': title, 'text': text, 'photo': project_photo(ctx, title),
                        'placeholder': None, 'origin': f'{md}#beleg{i}'}
                       for i, (ico, title, text) in enumerate(mot['proofs'], 1)],
        }
    else:
        slot = master_model()['slots']['motivation']
        view = {'lead': slot['lead'], 'dense': False, 'paragraphs': slot['paragraphs'], 'proofs': slot['proofs']}
    view['signer'] = {'name': person['name'], 'city': person['address']['city'], 'origin': 'profile:person.name'}
    return view


def cv_hero_view(ctx: Ctx) -> dict:
    p = ctx.p
    person, addr, port = p['person'], p['person']['address'], p.get('portfolio', {})

    def fact(icon_name: str, parts: list[dict], origin: str) -> dict:
        return {'icon': icon_name, 'parts': parts, 'origin': origin}

    facts = [fact('i-pin', lines(addr['street'], f'{addr["postal_code"]} {addr["city"]}'), 'profile:person.address'),
             fact('i-mail', email_parts(person['email']), 'profile:person.email'),
             fact('i-phone', lines(person['phone']), 'profile:person.phone')]
    if p['presentation'].get('show_birth_data'):
        # Herkunft steht in der ersten Zeile der rechten Spalte, neben dem Wohnort; Geburtsdatum darunter.
        if person.get('birth_place'):
            facts.append(fact('i-map', two_line_place(person['birth_place']), 'profile:person.birth_place'))
        if person.get('birth_date'):
            facts.append(fact('i-cake', lines(short_date(person['birth_date'])), 'profile:person.birth_date'))
    if person.get('driving_license'):
        facts.append(fact('i-car', lines(f'Führerschein {person["driving_license"]}'),
                          'profile:person.driving_license'))
    goal = (field(port['cv_goal'], 'profile:portfolio.cv_goal') if port.get('cv_goal')
            else field(f'Ausbildungsziel: {p["goal"]["apprenticeship"]}', 'profile:goal.apprenticeship'))
    return {'name': field(person['name'], 'profile:person.name'), 'goal': goal, 'facts': facts}


def newest_first(entries: list[dict]) -> list[tuple[int, dict]]:
    """Lebenslauf-Reihenfolge: neueste Station zuerst (nach Beginn); ohne Beginn bleibt die Profilreihenfolge.
    Liefert (Position im Profil, Eintrag)."""
    return sorted(enumerate(entries), key=lambda x: (x[1].get('date_range') or {}).get('start') or '', reverse=True)


def timeline_item(origin: str, date: str, name: str, place: str, role: str, text: str, chips: list[dict]) -> dict:
    return {'origin': origin, 'date': date, 'name': name, 'place': place or None, 'role': role or None,
            'text': text, 'chipline': {'chips': chips} if chips else None}


def cv_experience_view(ctx: Ctx) -> dict:
    items = []
    for i, e in newest_first(ctx.p['experience']):
        kind = KIND_LABEL.get(e['kind'], 'Sonstiges')
        if e.get('employment_type'):
            kind += f' ({e["employment_type"]})'
        role = ' · '.join(x for x in (e.get('role', ''), kind) if x)
        items.append(timeline_item(f'profile:experience[{e.get("id", i)}]', fmt_range(e['date_range']),
                                   e['organization'], e['city'], role, '; '.join(e.get('tasks', [])), []))
    return {'items': items}


def cv_education_view(ctx: Ctx) -> dict:
    items = []
    for i, e in newest_first(ctx.p['education']):
        if e.get('show_in_cv') is False:  # z. B. Grundschulen nach einem weiterführenden Abschluss; bleibt im Profil
            continue
        place = e['city'] + (f' ({e["country"]})' if e.get('country') and e['country'] != 'Deutschland' else '')
        text = ''
        if e.get('qualification'):
            text = f'Abschluss: {e["qualification"]}'
            end = e['date_range'].get('end')
            if e.get('expected') and end:
                text += f', voraussichtlich {fmt_point(end, e["date_range"].get("precision", "month"))}'
        items.append(timeline_item(f'profile:education[{e.get("id", i)}]', fmt_range(e['date_range']),
                                   e['institution'], place, e.get('program_short') or e.get('program', ''), text, []))
    return {'items': items}


def cv_projects_view(ctx: Ctx) -> dict | None:
    """Optionaler Block „Eigene Projekte“ (Homelab): nur Projekte mit show_in_cv: true, Reihenfolge wie im Profil."""
    items = []
    for i, pr in enumerate(ctx.p.get('projects', [])):
        if not pr.get('show_in_cv'):
            continue
        date = fmt_range(pr['date_range']) if pr.get('date_range') else ''
        if not date and (pr.get('date_range') or {}).get('is_current'):
            date = 'laufend'
        chips = pr.get('chips') or [{'name': x} for x in pr.get('tools', [])]
        items.append(timeline_item(f'profile:projects[{pr.get("id", i)}]', date, pr['name'], '', '',
                                   pr.get('cv_summary') or pr.get('own_role', ''), [chip_view(c) for c in chips]))
    if not items:
        return None
    conf = ctx.p['presentation'].get('cv_projects') or {}
    return {'title': conf.get('title') or 'Eigene Projekte', 'origin': 'profile:presentation.cv_projects',
            'items': items}


def level_label(item: dict) -> str:
    return 'Muttersprache' if item.get('level') == 'native' else SCALE_LABEL[item['scale']]


def cv_languages_view(ctx: Ctx) -> dict:
    return {'items': [{'origin': f'profile:skills.languages[{i}]', 'name': lang['name'],
                       'bars': bars_view(lang['scale'], label=level_label(lang)), 'level': level_label(lang)}
                      for i, lang in enumerate(ctx.p['skills']['languages'])]}


def cv_skills_view(ctx: Ctx) -> dict:
    groups = []
    for gi, g in enumerate(ctx.p['skills']['groups']):
        rows = []
        for ii, it in enumerate(g['items']):
            chips = it.get('chips') or [{'name': x.strip()} for x in it.get('evidence', '').split(',') if x.strip()]
            # Zusatz unter dem Zeilennamen: Profilwert (auch leer = keiner); ohne Angabe „Lernstand“ bei level learning.
            # Bei future (Lernwunsch) nie ein Zusatz: die Skala zeigt es.
            note = it['note'] if 'note' in it else ('Lernstand' if it.get('level') == 'learning' else '')
            rows.append({'origin': f'profile:skills.groups[{gi}].items[{ii}]', 'name': it.get('label') or it['name'],
                         'note': note or None, 'chips': [chip_view(c) for c in chips],
                         'bars': bars_view(it['scale'], future=it.get('level') == 'future')})
        groups.append({'origin': f'profile:skills.groups[{gi}]', 'icon': g['icon'], 'name': g['name'], 'rows': rows})
    return {'legend': scale_legend(), 'groups': groups}


CV_BLOCKS = {'experience': cv_experience_view, 'education': cv_education_view, 'projects': cv_projects_view,
             'skills': cv_skills_view, 'languages': cv_languages_view}
# Lesereihenfolge: Schulbildung, Erfahrung, Fähigkeiten, Sprachen. Sprachen nie vor Schulbildung oder
# Fähigkeiten. „projects“ (optional) darf überall nach der Erfahrung stehen, wo es auf die Seiten passt.
CV_ORDER = ['education', 'experience', 'skills', 'languages']


def cv_block(name: str, view: dict) -> dict:
    """Eintrag in blocks: genau ein Block ist gesetzt."""
    return {**dict.fromkeys(CV_BLOCKS), name: view}


def cv_page_view(ctx: Ctx, blocks: list[str], index: int, compact: bool, sign: dict | None) -> dict:
    """sign: Abschluss mit Ort, Datum und Unterschrift, nur auf der letzten Lebenslauf-Seite gesetzt."""
    views = []
    for b in blocks:
        if b not in CV_BLOCKS:
            raise BuildError(f'Unbekannter Lebenslauf-Block „{b}“ in presentation.cv_layout')
        view = CV_BLOCKS[b](ctx)
        if view is not None:
            views.append(cv_block(b, view))
    return {'compact': compact, 'hero': cv_hero_view(ctx) if index == 0 else None, 'blocks': views, 'sign': sign}


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


def evidence_card_view(ctx: Ctx, ev: dict | None, section: str) -> dict:
    if ev is None:
        return {'origin': 'profile:evidence', 'title': 'Zertifikat' if section == 'zertifikate' else 'Zeugnis',
                'issuer': 'Liegt noch nicht vor', 'image': None,
                'placeholder': {'parts': lines('Liegt noch nicht vor')}, 'caption': None}
    where = f'evidence[{ev["id"]}]'
    path = resolve_asset(ctx.pdir, ev['file'], f'{where}.file')
    if path.suffix.lower() not in IMAGE_EXT:
        raise BuildError(f'Nachweis {ev["id"]}: {ev["file"]} ist kein Bild. PDF-Nachweise vorher als PNG '
                         'rendern (z. B. pdftoppm -png -r 150) und das Bild als file eintragen.')
    return {'origin': f'profile:{where}', 'title': ev['title'], 'issuer': ev['issuer'],
            'image': {'src': ctx.src(ev['file'], f'{where}.file'), 'alt': ev['title']}, 'placeholder': None,
            'caption': {'note': ORIGINAL_LABEL.get(ev['original'], 'Nachweis'), 'date': short_date(ev['date'])}}


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


def evidence_page_view(ctx: Ctx, section: str, group: list) -> dict:
    return {'pair': len(group) == 2, 'cards': [evidence_card_view(ctx, ev, section) for ev in group]}


def plan_pages(profile: dict, warn: bool = True) -> list[dict]:
    layout = profile['presentation'].get('cv_layout') or {}
    cv_pages = layout.get('pages') or [list(CV_ORDER)]
    flat = [b for page in cv_pages for b in page]
    known = [b for b in flat if b in CV_ORDER]
    if warn and (known != sorted(known, key=CV_ORDER.index) or (
            'projects' in flat and 'experience' in flat and flat.index('projects') < flat.index('experience'))):
        print('Warnung: presentation.cv_layout weicht von der Lesereihenfolge ab '
              f'({", ".join(CV_ORDER)}; projects nach experience); Sprachen gehören hinter Schulbildung und '
              'Fähigkeiten.', file=sys.stderr)
    if warn and 'projects' in flat and not any(p.get('show_in_cv') for p in profile.get('projects', [])):
        print('Hinweis: Block „projects“ in cv_layout, aber kein Projekt mit show_in_cv: true; der Block entfällt.',
              file=sys.stderr)
    plan = [{'section': 'deckblatt'}, {'section': 'anschreiben'}]
    compact = layout.get('compact')  # true/false für alle Seiten oder Liste je Seite
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


def build_document(ctx: Ctx, letter=None, mot=None, job=None, typ='apprenticeships',
                   warn: bool = True) -> tuple[str, list[dict]]:
    """Profilvorlage (ohne letter/mot/job) oder Bewerbung aus den Quellen: HTML und Seitenliste fürs Manifest."""
    plan = plan_pages(ctx.p, warn)
    starts = section_starts(plan)
    last_cv = max(p['index'] for p in plan if p['section'] == 'lebenslauf')
    entries = []
    for page in plan:
        s = page['section']
        if s == 'deckblatt':
            content = cover_view(ctx, starts)
        elif s == 'anschreiben':
            content = letter_view(ctx, letter, job, typ)
        elif s == 'lebenslauf':
            content = cv_page_view(ctx, page['blocks'], page['index'], page['compact'],
                                   cv_sign_view(ctx, letter) if page['index'] == last_cv else None)
        elif s == 'motivationsschreiben':
            content = motivation_view(ctx, mot)
        else:
            content = evidence_page_view(ctx, s, page['group'])
        entries.append(page_entry(s, page['number'], page.get('index', 0), content))
    entries[-1]['last'] = True
    doc = render_document(f'Bewerbungsmappe – {ctx.p["person"]["name"]}', chrome_view(starts), entries)
    pages = [{'number': p['number'], 'section': p['section'], **({'continuation': True} if p['continuation'] else {})}
             for p in plan]
    return doc, pages


def build_master() -> str:
    """Master-Vorlage: dieselben Partials mit dem Platzhalter-Modell aus master.json."""
    model = master_model()
    counts: Counter = Counter()
    plan = []
    for number, page in enumerate(model['pages'], 1):
        if page['section'] not in PAGE_PARTIAL:
            raise BuildError(f'{rel(MASTER_MODEL)}: unbekannter Abschnitt „{page["section"]}“')
        plan.append({'section': page['section'], 'number': number, 'index': counts[page['section']]})
        counts[page['section']] += 1
    starts = section_starts(plan)
    missing = [s for s in SECTIONS if s not in starts]
    if missing:
        raise BuildError(f'{rel(MASTER_MODEL)}: Abschnitt fehlt: {", ".join(missing)}')
    entries = []
    for meta, page in zip(plan, model['pages']):
        content = page['content']
        kind = PAGE_PARTIAL[meta['section']]
        if kind == 'cover':
            content['toc'] = toc_view(starts)
        elif kind == 'cv':
            content.setdefault('hero', None)
            content.setdefault('sign', None)
            content['blocks'] = [{name: block.get(name) for name in CV_BLOCKS} for block in content['blocks']]
            for block in content['blocks']:
                if block['skills'] is not None:
                    block['skills'].setdefault('legend', scale_legend())
        entries.append(page_entry(meta['section'], meta['number'], meta['index'], content))
    entries[-1]['last'] = True
    return render_document(model['title'], chrome_view(starts), entries)


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


def letter_date(letter: dict, path: Path) -> dt.date:
    """Briefdatum aus dem Kopf von anschreiben.md. Pflicht: Das Skript setzt kein Tagesdatum ein, damit
    dieselben Quellen immer dieselbe Mappe ergeben."""
    value = letter['meta'].get('datum', '')
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError
        return dt.date.fromisoformat(value)
    except ValueError:
        raise BuildError(f'{rel(path)}: Im Kopf fehlt ein gültiges „datum: JJJJ-MM-TT“ (gefunden: „{value}“). '
                         'Das Briefdatum ist Pflicht und wird nicht automatisch gesetzt.')


def word_count(paras: list[str]) -> int:
    return sum(len(re.findall(r'\S+', p)) for p in paras)


def words_note(label: str, count: int, limits: dict, meta: dict) -> str:
    """Wortzahl neben den Richtwerten; liegt sie über dem Richtwert der gewählten Dichte, steht das dabei."""
    mode = 'dicht' if meta.get('dichte', 'normal') in ('dicht', 'dense') else 'normal'
    over = f'; über dem Richtwert für „{mode}“' if count > limits[mode] else ''
    return f'Wörter {label}: {count} (Richtwert normal ≤ {limits["normal"]}, dicht ≤ {limits["dicht"]}{over})'


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
    """A4-PDF ohne Kopf- und Fußzeile; mit Lesezeichen aus den Überschriften, wo Chromium das kann
    (ältere Versionen ignorieren den Schalter)."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(chrome_cmd('--no-pdf-header-footer', '--generate-pdf-document-outline',
                              f'--print-to-pdf={pdf_path}', html_path.resolve().as_uri()),
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


def probe_views(html_path: Path) -> dict:
    """Ein Chromium-Lauf für alle Bildschirmbreiten: der Prüfstand qa.html lädt die Mappe je Breite in einen
    iframe exakter Größe (Media-Queries gelten für den iframe) und führt die Sonde qa.js aus. Es entsteht
    keine Hilfsdatei. Headless-Chromium erzwingt mindestens ca. 500 px Fensterbreite, deshalb der iframe.
    Stimmt die gemessene Breite nicht mit der angeforderten überein, gilt die Messung als fehlgeschlagen."""
    viewports = qa_viewports()
    views = ','.join(f'{key}:{size.replace(",", "x")}' for key, size in viewports)
    url = f'{QA_PAGE.as_uri()}?doc={quote(html_path.as_uri(), safe="")}&views={views}'
    dom = subprocess.run(chrome_cmd('--allow-file-access-from-files', f'--window-size={viewports[0][1]}',
                                    '--dump-dom', url), capture_output=True, text=True).stdout
    m = re.search(r'data-qa="([^"]*)"', dom)
    data = json.loads(html.unescape(m.group(1))) if m else {}
    return {key: view if (view := data.get(key)) and view.get('width') == int(size.split(',')[0]) else None
            for key, size in viewports}


PLACEHOLDER = re.compile(r'\[[A-ZÄÖÜ][^\]\n<>]{1,80}\]')


def slot_placeholders() -> set[str]:
    """Platzhalter, die in der Profilvorlage stehen sollen: die Texte für Anschreiben und Motivationsschreiben
    und das Datum unter dem Lebenslauf aus master.json (slots)."""
    found: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, str):
            found.update(PLACEHOLDER.findall(node))
        elif isinstance(node, (dict, list)):
            for value in (node.values() if isinstance(node, dict) else node):
                walk(value)

    walk(read_json(MASTER_MODEL)['slots'])
    return found


def local_images(doc: str, base: Path) -> list[Path]:
    """Lokale Bilddateien, die eine Mappe einbindet (ohne data: und http:)."""
    return [base / html.unescape(s) for s in re.findall(r'<img\b[^>]*?\ssrc="([^"]+)"', doc)
            if not re.match(r'(data|https?):', s)]


def run_qa(html_path: Path, ignore_slots: bool = False, fast: bool = False) -> dict:
    """ignore_slots (Profilvorlage): Die Platzhalter aus master.json (slots) sind gewollt.
    fast: nur der Bildschirmlauf (Überlauf, Füllgrad, Breiten), kein A4-PDF. Für die Schleife beim Ändern der
    Vorlage; vor Freigabe und PDF immer die volle Prüfung."""
    html_path = html_path.resolve()
    src = html_path.read_text(encoding='utf-8')
    result = probe_views(html_path)
    a4_pages = None
    if not fast:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / 'qa.pdf'
            print_pdf(html_path, pdf)
            a4_pages = pdf_pages(pdf)
    body = re.sub(r'<!--.*?-->', '', src.split('<div class="screen-bar', 1)[-1], flags=re.S)
    placeholders = sorted(set(PLACEHOLDER.findall(body)) - (slot_placeholders() if ignore_slots else set()))
    missing = [p.relative_to(html_path.parent).as_posix() for p in local_images(body, html_path.parent)
               if not p.is_file()]
    unknown = sorted({c for attr in re.findall(r'class="([^"]*)"', body) for c in attr.split()
                      if re.fullmatch(r'[a-zA-Z][\w-]*', c)} - known_classes())
    desktop = result.get('desktop') or {}
    hits = desktop.get('hits') if desktop else None
    page_count = desktop.get('pages') if desktop else None
    qa = {
        'mode': 'fast' if fast else 'full',
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
    qa['ok'] = (hits == [] and (fast or a4_pages == page_count) and not placeholders and not missing
                and widths_ok)
    return qa


def cv_fill(qa: dict) -> str:
    """Füllgrad der Lebenslauf-Seiten (data-section 3) als Text, leer wenn nicht messbar."""
    rows = [r for r in qa.get('fill') or [] if r[0] in (qa.get('cv_pages') or [])]
    return ' · '.join(f'S{n} {pct} % ({rest:+.1f} mm)' for n, pct, rest in rows)


def print_qa(name: str, qa: dict, extra: list[str] | None = None) -> None:
    print(f'QA {name}: {"OK" if qa["ok"] else "PROBLEME"}')
    print(f'  Seiten: HTML {qa["html_pages"]}, A4-PDF '
          + ('nicht geprüft (--qa=fast)' if qa.get('mode') == 'fast' else str(qa['a4_pages'])))
    print(f'  Überlauf: {qa["overflow"] or "keiner"}')
    cv = cv_fill(qa)
    if cv:
        low, high = limit('cv.fill_target_percent')
        print(f'  Füllgrad Lebenslauf: {cv} (Richtwert {low}–{high} %, Rest in mm bis zum unteren Rand)')
    print('  Horizontaler Überlauf (px): ' + ' · '.join(
        f'{w}: {v if v is not None else "nicht messbar"}' for w, v in qa['hscroll'].items()))
    if qa['placeholders']:
        print(f'  Offene Platzhalter: {", ".join(qa["placeholders"])}')
    if qa['missing_assets']:
        print(f'  Fehlende Bilder: {", ".join(qa["missing_assets"])}')
    if qa['unknown_classes']:
        print(f'  Hinweis: Klassen ohne CSS-Regel und ohne Partial (assets/mappe/): {", ".join(qa["unknown_classes"])}')
    for line in extra or []:
        print(f'  {line}')


# --------------------------------------------------------------------------- Seitenbilder (Vorher/Nachher)

SNAPSHOT_DIR = ROOT / '.tmp' / 'snapshots'


def read_pgm(path: Path) -> tuple[int, int, bytes]:
    """Binäres Graustufenbild (PGM, P5, 8 Bit) lesen: Breite, Höhe, Pixel."""
    data = path.read_bytes()
    m = re.match(rb'P5(?:\s+|#[^\n]*\n)+(\d+)(?:\s+|#[^\n]*\n)+(\d+)(?:\s+|#[^\n]*\n)+(\d+)\s', data)
    if not m or int(m.group(3)) != 255:
        raise BuildError(f'Kein 8-Bit-PGM: {path}')
    w, h = int(m.group(1)), int(m.group(2))
    pixels = data[m.end():m.end() + w * h]
    if len(pixels) != w * h:
        raise BuildError(f'PGM unvollständig: {path}')
    return w, h, pixels


def render_pages(html_path: Path, out_dir: Path) -> list[Path]:
    """A4-PDF drucken und jede Seite als Graustufenbild (50 dpi) nach out_dir schreiben."""
    if not shutil.which('pdftoppm'):
        raise BuildError('pdftoppm fehlt (Paket poppler bzw. poppler-utils); ohne es kein Seitenvergleich.')
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('page-*.pgm'):
        old.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / 'snapshot.pdf'
        print_pdf(html_path, pdf)
        subprocess.run(['pdftoppm', '-gray', '-r', str(limit('snapshot.dpi')), str(pdf), str(Path(tmp) / 'p')],
                       check=True, capture_output=True)
        pages = sorted(Path(tmp).glob('p-*.pgm'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        return [Path(shutil.copyfile(p, out_dir / f'page-{i:02d}.pgm')) for i, p in enumerate(pages, 1)]


def snapshot_name(html_path: Path, name: str | None) -> str:
    return slugify(name) if name else slugify(rel(html_path.resolve()).rsplit('.', 1)[0])


def diff_pages(old: tuple[int, int, bytes], new: tuple[int, int, bytes], tolerance: int) -> dict | None:
    """None bei gleichen Seiten, sonst Anteil geänderter Pixel, Bereich (mm) und größte Abweichung."""
    if old == new:
        return None
    if old[:2] != new[:2]:
        return {'share': 1.0, 'note': f'Größe {old[0]}×{old[1]} → {new[0]}×{new[1]} px'}
    w, h = old[:2]
    count = peak = 0
    x0, y0, x1, y1 = w, h, -1, -1
    for i, (a, b) in enumerate(zip(old[2], new[2])):
        if a != b and abs(a - b) > tolerance:
            count += 1
            peak = max(peak, abs(a - b))
            y, x = divmod(i, w)
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    if not count:
        return None
    mm = 25.4 / limit('snapshot.dpi')
    return {'share': count / (w * h), 'peak': peak,
            'box': tuple(round(v * mm) for v in (x0, y0, x1 + 1, y1 + 1))}


def cmd_snapshot(args) -> int:
    """Seitenbilder einer Mappe sichern (--save) oder mit der Sicherung vergleichen (--compare)."""
    if args.name and len(args.html) > 1:
        raise BuildError('--name gilt nur für eine einzelne Datei.')
    rc = 0
    for item in args.html:
        html_path = Path(item).resolve()
        if not html_path.is_file():
            raise BuildError(f'Datei fehlt: {item}')
        base = SNAPSHOT_DIR / snapshot_name(html_path, args.name)
        if args.save:
            pages = render_pages(html_path, base)
            (base / 'source.txt').write_text(rel(html_path) + '\n', encoding='utf-8')
            print(f'Seitenbilder gesichert: {rel(base)} ({len(pages)} Seiten, {limit("snapshot.dpi")} dpi)')
            continue
        saved = sorted(base.glob('page-*.pgm'))
        if not saved:
            raise BuildError(f'Keine Sicherung unter {rel(base)}. Zuerst: build_mappe.py snapshot --save "{item}"')
        with tempfile.TemporaryDirectory() as tmp:
            current = render_pages(html_path, Path(tmp))
            changed = []
            for n in range(1, max(len(saved), len(current)) + 1):
                if n > len(saved) or n > len(current):
                    changed.append(f'  Seite {n}: nur {"neu" if n > len(saved) else "in der Sicherung"} vorhanden')
                    continue
                d = diff_pages(read_pgm(saved[n - 1]), read_pgm(current[n - 1]), args.tolerance)
                if d and 'box' in d:
                    x0, y0, x1, y1 = d['box']
                    changed.append(f'  Seite {n}: {100 * d["share"]:.2f} % der Fläche geändert, Bereich x {x0}–{x1} mm, '
                                   f'y {y0}–{y1} mm, größte Abweichung {d["peak"]}/255')
                elif d:
                    changed.append(f'  Seite {n}: {d["note"]}')
        print(f'Seitenvergleich {rel(html_path)}: {len(changed)} von {max(len(saved), len(current))} Seiten geändert'
              + (f' (Toleranz {args.tolerance}/255)' if args.tolerance else ''))
        for line in changed:
            print(line)
        rc = 2 if changed else rc
    return rc


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
        qa = run_qa(out, ignore_slots=True, fast=args.qa == 'fast')
        print_qa(rel(out), qa, ['Platzhalter in Anschreiben und Motivationsschreiben und das Datum unter dem '
                                'Lebenslauf sind in der Profilvorlage gewollt.'])
        if not qa['ok']:
            return 2
    if args.pdf:
        pdf = out.with_suffix('.pdf')
        print_pdf(out, pdf)
        print(f'A4-Vorschau: {rel(pdf)} ({pdf_pages(pdf)} Seiten)')
    return 0


def document_hash(html_path: Path) -> str:
    """SHA-256 über die HTML-Datei und jede eingebundene Bilddatei (Name und Inhalt). Das ist der Stand, den der
    Nutzer freigibt: Ändert sich danach ein Zeichen oder ein Bild, passt die Prüfsumme nicht mehr."""
    data = html_path.read_bytes()
    h = hashlib.sha256(data)
    for path in sorted(set(local_images(data.decode('utf-8'), html_path.parent))):
        h.update(b'\0' + path.name.encode('utf-8') + b'\0')
        h.update(path.read_bytes() if path.is_file() else b'')
    return h.hexdigest()


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
    for i, pr in enumerate(profile.get('projects') or []):
        for j, img in enumerate(pr.get('images') or []):
            if img.get('file'):
                field = f'projects[{pr.get("id", i)}].images[{j}].file'
                by_path[resolve_asset(pdir, img['file'], field)] = ('project_image', 'motivationsschreiben', None)
    out, seen = [], set()
    for file, src in copied:
        if file in seen:
            continue
        seen.add(file)
        role, sec, ev = by_path.get(src.resolve(), ('evidence', 'zertifikate', None))
        if role == 'project_image':
            sec = 'motivationsschreiben'
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


def iter_postings(pdir: Path) -> list[Path]:
    """Alle Stellenordner eines Profils (aktiv, sent/, dropped/): Ordner mit job_information/job.json."""
    return sorted(p.parent.parent for p in (pdir / 'applications').rglob('job_information/job.json'))


def question_state(job: dict) -> tuple[list[dict], int]:
    """(offene blockierende Fragen, Anzahl beantworteter, noch nicht eingearbeiteter Fragen) einer Stelle."""
    questions = job.get('open_questions') or []
    blocking = [q for q in questions if q.get('severity') == 'blocking' and q.get('status', 'open') == 'open']
    return blocking, sum(1 for q in questions if q.get('status') == 'answered')


def read_drop(posting: Path) -> tuple[str, str] | None:
    """(Grund, Datum) aus DROPPED.txt: erste Textzeile ist der Grund, „Datum: JJJJ-MM-TT“ das Datum."""
    path = posting / DROP_FILE
    if not path.is_file():
        return None
    reason = date = ''
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.fullmatch(r'Datum:\s*(\d{4}-\d{2}-\d{2})', line.strip())
        if m:
            date = m.group(1)
        elif line.strip() and not reason:
            reason = line.strip()
    return reason, date


def add_history(manifest: dict, status: str, stamp: str, note: str | None = None) -> None:
    manifest.setdefault('history', []).append({'date': stamp[:10], 'status': status, **({'note': note} if note else {})})


def ensure_history(manifest: dict, old_entry: dict | None) -> bool:
    """Manifest ohne history (ältere Mappen): Verlauf aus dem Ledger-Eintrag, sonst aus den Zeitstempeln.

    True, wenn das Manifest ergänzt wurde."""
    if isinstance(manifest.get('history'), list):
        return False
    history = [h for h in (old_entry or {}).get('history', []) if h.get('status') in MANIFEST_STATUSES]
    if not history:
        history = [{'date': manifest.get('created_at') or today(), 'status': 'draft', 'note': 'Mappe gebaut'}]
        for key, status in (('approved_at', 'html_approved'), ('pdf_exported_at', 'pdf_exported'), ('sent_at', 'sent')):
            if manifest.get(key):
                history.append({'date': manifest[key][:10], 'status': status})
        if manifest.get('status') in MANIFEST_STATUSES and manifest['status'] not in [h['status'] for h in history]:
            history.append({'date': history[-1]['date'], 'status': manifest['status']})
    manifest['history'] = history
    return True


def ledger_entry(posting: Path, info: dict, job: dict, old: dict | None) -> dict:
    """Ledger-Eintrag einer Stelle, vollständig aus dem Ordner abgeleitet (nur notes kommt aus dem alten Eintrag).

    Status: dropped (Ordner unter applications/dropped/ mit DROPPED.txt), sonst der Status des Manifests,
    ohne Manifest captured."""
    man_path = posting / 'application' / 'application-manifest.json'
    manifest = read_json(man_path) if man_path.is_file() else None
    if manifest is not None and ensure_history(manifest, old):
        write_json(man_path, manifest)
    drop = read_drop(posting)
    if info['dropped'] and drop is None:
        raise BuildError(f'liegt unter applications/dropped/, aber {DROP_FILE} fehlt (Aussortieren nur über '
                         'build_mappe.py drop)')
    if drop is not None and not info['dropped']:
        raise BuildError(f'{DROP_FILE} in einem Ordner außerhalb von applications/dropped/ (build_mappe.py drop '
                         'verschiebt den Ordner; zum Zurückholen: restore)')
    man = manifest or {}
    source, app, search, c = (job.get(k) or {} for k in ('source', 'application', 'search', 'contact'))
    captured = source.get('retrieved_at') or man.get('created_at') or today()
    status = man.get('status', 'captured')
    history = [{'date': captured, 'status': 'captured', 'note': 'Anzeige erfasst'}, *man.get('history', [])]
    dropped_at = drop_reason = None
    if drop is not None:
        status, drop_reason, dropped_at = 'dropped', drop[0] or 'ohne Grund', drop[1] or captured
        history.append({'date': dropped_at, 'status': 'dropped', 'note': drop_reason})
    refnr = job.get('reference_number') or ''
    contact = {k: v for k, v in (('name', ' '.join(x for x in (c.get('honorific', ''), c.get('name', '')) if x)),
                                 ('email', c.get('email', '')), ('phone', c.get('phone', ''))) if v}
    entry = {
        'id': refnr or posting.name,
        'reference_number': refnr,
        'company': job['company'],
        'title': job['title'],
        'occupation': job.get('occupation', ''),
        'type': info['type'],
        'folder': info['folder'],
        'search_city': search.get('city', ''),
        'rank': search.get('rank'),
        'status': status,
        'created_at': man.get('created_at') or captured,
        'deadline': job.get('deadline') or None,
        'html_approved_at': (man.get('approved_at') or '')[:10] or None,
        'pdf_exported_at': (man.get('pdf_exported_at') or '')[:10] or None,
        'sent_at': (man.get('sent_at') or '')[:10] or None,
        'dropped_at': dropped_at,
        'drop_reason': drop_reason,
        'channel': man.get('channel') or app.get('method') or 'unknown',
        'open_blocking': None if drop is not None else len(question_state(job)[0]),
        'contact': contact,
        'application_email': app.get('email', ''),
        'source_url': source.get('url', ''),
        'notes': (old or {}).get('notes'),
        'history': history,
    }
    return {k: v for k, v in entry.items() if v is not None}


def ledger_sort_key(entry: dict) -> str:
    return re.sub(r'^applications/(?:sent/|dropped/)?', '', entry.get('folder', ''))


def sync_ledger(pdir: Path) -> tuple[dict, list[str]]:
    """Ledger aus den Stellenordnern ableiten und schreiben (idempotent). Rückgabe: Ledger, Warnungen.

    Jeder Ordner mit job_information/job.json ergibt genau einen Eintrag. Ein gelöschtes Ledger entsteht so
    vollständig neu; nur das handgepflegte Feld notes ginge dabei verloren."""
    with ledger_lock(pdir):
        old = load_ledger(pdir)
        by_folder = {e.get('folder'): e for e in old['entries']}
        by_ref = {e['reference_number']: e for e in old['entries'] if e.get('reference_number')}
        entries, warnings, used = [], [], set()
        for posting in iter_postings(pdir):
            prev = None
            try:
                info = posting_info(posting)
                job = read_json(posting / 'job_information' / 'job.json')
                prev = by_folder.get(info['folder'])
                if prev is None:  # verschobener Ordner (mark-sent, drop, restore): über die Referenznummer finden
                    cand = by_ref.get(job.get('reference_number') or '')
                    if cand is not None and not (pdir / cand.get('folder', '') / 'job_information' / 'job.json').is_file():
                        prev = cand
                entry = ledger_entry(posting, info, job, prev)
            except (BuildError, KeyError, TypeError, AttributeError) as e:
                warnings.append(f'{rel(posting)}: {e if isinstance(e, BuildError) else repr(e)}')
                entry = prev
            if prev is not None:
                used.add(id(prev))
            if entry is not None:
                entries.append(entry)
        for e in old['entries']:
            if id(e) not in used:
                warnings.append(f'Ledger-Eintrag ohne Stellenordner behalten: {e.get("folder")}')
                entries.append(e)
        entries.sort(key=ledger_sort_key)
        ledger = {'schema_version': '1.0', 'profile': pdir.name, 'entries': entries}
        if ledger != old or (entries and not ledger_path(pdir).is_file()):
            write_json(ledger_path(pdir), ledger)
        return ledger, warnings


def norm_company(name: str) -> str:
    """Firmenname für den Vergleich: ohne Klammerzusätze und Rechtsform, als Slug-Wörter."""
    t = re.sub(r'\([^)]*\)', ' ', name)
    t = re.sub(r'\b([eEaA])\.\s?([VKGvkg])\.', r'\1\2', t)  # e.V., e.K., a.G.
    return ' '.join(w for w in slugify(t).split('-') if w and w not in LEGAL_FORMS)


def dup_key(job: dict) -> dict:
    """Schlüssel der Duplikatprüfung: Firma, Beruf, Arbeitsorte, Startjahr (references/applications.md)."""
    year = ''
    for field in ('start', 'start_text', 'title'):
        m = re.search(r'\b(20\d{2})\b', job.get(field) or '')
        if m:
            year = m.group(1)
            break
    towns = {slugify(re.split(r'[,(]', loc.get('city') or '', maxsplit=1)[0]) for loc in job.get('locations') or []}
    return {'ref': job.get('reference_number') or '', 'company': norm_company(job.get('company') or ''),
            'occupation': slugify(job.get('occupation') or ''), 'towns': towns - {''}, 'year': year}


def dup_class(a: dict, b: dict) -> str | None:
    """same_posting, same_role_other_site, same_employer_other_role oder None für zwei dup_key-Schlüssel."""
    if a['ref'] and a['ref'] == b['ref']:
        return 'same_posting'
    if not a['company'] or a['company'] != b['company']:
        return None
    if a['occupation'] == b['occupation'] and a['year'] == b['year']:
        return 'same_posting' if a['towns'] & b['towns'] else 'same_role_other_site'
    return 'same_employer_other_role'


def dup_decision(job: dict, other: dict) -> str:
    """Text der gespeicherten Nutzerentscheidung (duplicate_decision) für das Paar, sonst ''."""
    for mine, theirs in ((job, other), (other, job)):
        d = mine.get('duplicate_decision') or {}
        if theirs.get('reference_number') and theirs['reference_number'] in (d.get('reference_numbers') or []):
            return f'{d.get("decision", "")} (Nutzer, {d.get("decided_at", "")})'
    return ''


def cmd_application(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if info['dropped']:
        raise BuildError(f'Die Stelle ist aussortiert ({DROP_FILE}). Zurückholen: build_mappe.py restore "{rel(posting)}"')
    pdir, user = info['profile_dir'], info['user']
    profile = load_profile(pdir)
    check_profile_assets(profile, pdir)
    # Die Profilvorlage ist Vorschau und Freigabeobjekt für Deckblatt, Lebenslauf und Nachweise. Die Mappe selbst
    # entsteht aus den Quellen; weicht die gespeicherte Profilvorlage davon ab, hat der Nutzer diesen Stand nie gesehen.
    tpl_path = profile_template_path(pdir)
    if not tpl_path.is_file():
        raise BuildError(f'Profilvorlage fehlt: {rel(tpl_path)}. Zuerst: build_mappe.py profile-template {rel(pdir)}')
    if tpl_path.read_text(encoding='utf-8') != build_document(Ctx(profile, pdir, tpl_path.parent), warn=False)[0]:
        print('Warnung: Die Profilvorlage ist nicht aktuell (Profil oder Vorlage wurden nach ihrem Bau geändert). '
              f'Neu bauen und vom Nutzer prüfen lassen: build_mappe.py profile-template {rel(pdir)} --qa',
              file=sys.stderr)
    job = read_json(posting / 'job_information' / 'job.json')
    letter = read_letter(posting / 'text_generation' / 'anschreiben.md')
    dated = letter_date(letter, posting / 'text_generation' / 'anschreiben.md')
    mot = read_motivation(posting / 'text_generation' / 'motivationsschreiben.md')
    app_dir = posting / 'application'
    app_dir.mkdir(parents=True, exist_ok=True)
    out = app_dir / html_name(user)

    ctx = Ctx(profile, pdir, app_dir, bundle=True)
    doc, pages = build_document(ctx, letter, mot, job, info['type'])
    copied = ctx.copied
    if not out.is_file() or out.read_text(encoding='utf-8') != doc:  # unverändert nicht neu schreiben
        out.write_text(doc, encoding='utf-8')

    man_path = app_dir / 'application-manifest.json'
    if man_path.is_file():
        manifest = read_json(man_path)
        ensure_history(manifest, find_entry(load_ledger(pdir), info['folder'], job.get('reference_number')))
    else:
        manifest = {'status': 'draft', 'created_at': today(),
                    'history': [{'date': today(), 'status': 'draft', 'note': 'Mappe gebaut'}]}
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
    # Freigegeben ist genau der Stand mit der Prüfsumme aus „status … html_approved“ (HTML und Bilder). Ergibt der
    # Bau wieder diesen Stand, bleibt die Freigabe, auch wenn die gespeicherte Datei zwischendurch anders aussah.
    approval_lost = ''
    if manifest['status'] in ('html_approved', 'pdf_exported') and manifest.get('approved_sha256') != document_hash(out):
        approval_lost = ('Die Freigabe hat keine Prüfsumme (ältere Freigabe)' if not manifest.get('approved_sha256')
                         else 'Die Mappe weicht vom freigegebenen Stand ab (Text, Profil, Vorlage oder ein Bild '
                              'wurde geändert)')
        print(f'Hinweis: {approval_lost}. Der Nutzer muss die HTML-Fassung erneut freigeben; Status zurück auf draft.',
              file=sys.stderr)
        manifest['status'] = 'draft'
        add_history(manifest, 'draft', today(), 'nach Änderung zurück auf draft')
        for k in ('approved_at', 'approved_sha256', 'pdf', 'pdf_exported_at'):
            manifest.pop(k, None)
    words_letter, words_mot = word_count(letter['paragraphs']), word_count(mot['paragraphs'])
    print(f'Mappe: {rel(out)} ({len(pages)} Seiten)')
    notes = [words_note('Anschreiben', words_letter, limit('letter.words'), letter['meta']),
             words_note('Motivationsschreiben', words_mot, limit('motivation.words'), mot['meta'])]
    notes += address_warnings(profile, job)
    email_state, email_msg = email_draft_state(posting)
    if email_msg:
        notes.append(f'FEHLER: {email_msg} Blockiert Freigabe und PDF, nicht das Bauen.')
    salutation = (job.get('contact') or {}).get('salutation')
    if salutation and not letter['paragraphs'][0].startswith(salutation):
        notes.append(f'Warnung: Anrede im Anschreiben weicht von job.json ab („{salutation}“).')
    rc = 0
    if args.qa:
        qa = run_qa(out, fast=args.qa == 'fast')
        qa['ok'] = qa['ok'] and email_state in ('ok', 'not_required')
        print_qa(rel(out), qa, notes)
        manifest['validation'] = {
            'mode': qa['mode'],
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
        if args.qa == 'fast':
            write_json(man_path, manifest)
            sync_ledger(pdir)
            raise BuildError('Kein PDF nach --qa=fast: Das finale PDF braucht die volle Prüfung (--qa).')
        if manifest['status'] not in ('html_approved', 'pdf_exported', 'sent'):
            write_json(man_path, manifest)
            sync_ledger(pdir)
            raise BuildError(f'Kein PDF: {approval_lost or "Die HTML-Fassung ist nicht freigegeben"}. Erst nach dem '
                             f'ausdrücklichen Ja des Nutzers: build_mappe.py status "{rel(posting)}" html_approved')
        if email_msg:
            write_json(man_path, manifest)
            sync_ledger(pdir)
            raise BuildError(f'Kein PDF: {email_msg}')
        if rc:
            raise BuildError('Kein PDF: Die QA meldet Probleme.')
        age = (dt.date.today() - dated).days
        if age > limit('letter.max_age_days'):
            raise BuildError(f'Kein PDF: Das Briefdatum {short_date(dated.isoformat())} ist {age} Tage alt (höchstens '
                             f'{limit("letter.max_age_days")}). „datum“ in text_generation/anschreiben.md auf den Versandtag '
                             'setzen, neu bauen und die HTML-Fassung erneut freigeben lassen.')
        pdf = app_dir / html_name(user, 'pdf')
        print_pdf(out, pdf)
        stamp = now_iso()
        if manifest['status'] == 'html_approved':
            add_history(manifest, 'pdf_exported', stamp)
            manifest['status'] = 'pdf_exported'
        manifest.update({'pdf': pdf.name, 'pdf_exported_at': stamp})
        print(f'PDF: {rel(pdf)} ({pdf_pages(pdf)} Seiten)')
        write_json(man_path, manifest)
        sync_ledger(pdir)
        return rc
    write_json(man_path, manifest)
    sync_ledger(pdir)
    return rc


def cmd_qa(args) -> int:
    html_path = Path(args.html)
    qa = run_qa(html_path, fast=args.fast)
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


def cmd_master(args) -> int:
    """Master-Vorlage assets/bewerbungsmappe.html aus assets/mappe/ bauen (--check: nur vergleichen)."""
    doc = build_master()
    same = TEMPLATE.is_file() and TEMPLATE.read_text(encoding='utf-8') == doc
    if args.check:
        print(f'Master-Vorlage {rel(TEMPLATE)}: '
              + ('aktuell' if same else 'NICHT AKTUELL. Neu bauen: python3 tools/build_mappe.py master'))
        return 0 if same else 2
    if not same:  # unverändert nicht neu schreiben: die Vorschau lädt sonst ohne Grund neu
        TEMPLATE.write_text(doc, encoding='utf-8')
    print(f'Master-Vorlage: {rel(TEMPLATE)} ({len(master_model()["pages"])} Seiten, '
          f'{"unverändert" if same else "aktualisiert"})')
    return 0


def first_difference(stored: str, expected: str) -> str:
    a, b = stored.splitlines(), expected.splitlines()
    for n, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            return f'erste Abweichung in Zeile {n}'
    return f'{len(a)} statt {len(b)} Zeilen'


def expected_application(posting: Path) -> tuple[Path, str, list[tuple[str, Path]]]:
    """Gespeicherte HTML-Datei einer Bewerbung, ihr Soll-Inhalt aus den Quellen und die eingebundenen Bilder.
    Schreibt nichts."""
    info = posting_info(posting)
    pdir = info['profile_dir']
    job = read_json(posting / 'job_information' / 'job.json')
    letter = read_letter(posting / 'text_generation' / 'anschreiben.md')
    letter_date(letter, posting / 'text_generation' / 'anschreiben.md')
    mot = read_motivation(posting / 'text_generation' / 'motivationsschreiben.md')
    ctx = Ctx(load_profile(pdir), pdir, posting / 'application', bundle=True, dry=True)
    doc, _ = build_document(ctx, letter, mot, job, info['type'], warn=False)
    return posting / 'application' / html_name(info['user']), doc, ctx.copied


def cmd_rebuild(args) -> int:
    """rebuild --check: Jede gespeicherte Datei muss Byte für Byte dem entsprechen, was ihre Quellen jetzt ergeben.

    Ziele: „master“, ein Profilordner (Profilvorlage und alle gebauten Mappen) oder ein Stellenordner."""
    if not args.check:
        raise BuildError('rebuild vergleicht nur: rebuild --check <ziel>…. Gebaut wird mit master, profile-template '
                         'und application.')
    jobs: list[tuple[Path, object]] = []  # (gespeicherte Datei, Funktion -> (Soll-Inhalt, Bilder))
    for item in args.target:
        if item == 'master':
            jobs.append((TEMPLATE, lambda: (build_master(), [])))
            continue
        path = Path(item).resolve()
        pdir = profile_dir_of(path)
        postings = [path]
        if path == pdir:
            tpl = profile_template_path(pdir)
            jobs.append((tpl, lambda pdir=pdir, tpl=tpl: (
                build_document(Ctx(load_profile(pdir), pdir, tpl.parent), warn=False)[0], [])))
            postings = [p for p in iter_postings(pdir) if (p / 'application' / html_name(pdir.name)).is_file()]
        for posting in postings:
            stored = posting / 'application' / html_name(pdir.name)
            jobs.append((stored, lambda posting=posting: expected_application(posting)[1:]))
    rc = 0
    for stored, build in jobs:
        try:
            expected, copied = build()
        except BuildError as e:
            print(f'FEHLER     {rel(stored)}: {e}')
            rc = 2
            continue
        stale = [href for href, src in copied
                 if not (stored.parent / href).is_file() or (stored.parent / href).read_bytes() != src.read_bytes()]
        if not stored.is_file():
            print(f'fehlt      {rel(stored)}')
        elif stored.read_text(encoding='utf-8') != expected:
            print(f'WEICHT AB  {rel(stored)}: {first_difference(stored.read_text(encoding="utf-8"), expected)}')
        elif stale:
            print(f'WEICHT AB  {rel(stored)}: Bild anders als die Quelle: {", ".join(stale)}')
        else:
            print(f'identisch  {rel(stored)}')
            continue
        rc = 2
    return rc


def cmd_contract(args) -> int:
    """Vertrag zwischen View-Model, Partials und CSS, aus den Dateien abgeleitet (ersetzt jede Liste von Hand)."""
    sources = partial_sources()
    try:
        engine = Renderer(sources)
    except RenderError as e:
        raise BuildError(f'Vorlage unter {rel(MAPPE)}: {e}')
    css, used, problems = css_classes(), set(), []
    print(f'Partials unter {rel(PARTIALS)}/ (Schlüssel: „a[].b“ = b innerhalb des Abschnitts a)')
    for name, source in sources.items():
        outline = engine.outline(name)
        keys = [k for k in outline if '> ' not in k]
        includes = sorted({k.rsplit('> ', 1)[1] for k in outline if '> ' in k})
        classes = partial_classes(source)
        used |= classes
        markup = re.sub(r'<!--.*?-->', '', TAG.sub('', source), flags=re.S)
        parts = set(re.findall(r'data-part="([^"]*)"', source))
        if name != 'document' and re.search(r'<(?!w?br>)[a-z]', markup) and parts != {name}:
            problems.append(f'{name}.html: das Wurzelelement braucht data-part="{name}" (gefunden: '
                            f'{", ".join(sorted(parts)) or "keins"})')
        problems += [f'{name}.html: Partial „{inc}“ fehlt' for inc in includes if inc not in sources]
        print(f'\n{name}.html' + (f'  data-part="{name}"' if parts == {name} else ''))
        print(f'  Schlüssel: {", ".join(keys) or "–"}')
        if includes:
            print(f'  bindet ein: {", ".join(includes)}')
        if classes:
            print(f'  Klassen: {", ".join(sorted(classes))}')
        dynamic = sorted(set(re.findall(r'class="([^"]*\{\{[^"]*)"', source)))
        if dynamic:
            print('  Klassen mit Werten aus dem View-Model: ' + ' | '.join(dynamic))
        origins = sorted(set(re.findall(r'data-origin="([^"{]+)"', source)))
        if origins:
            print(f'  feste data-origin: {", ".join(origins)}')
    print(f'\nSymbole in {rel(MAPPE / "icons.svg")}: {len(symbol_table())}')
    print(f'Klassen in Partials ohne CSS-Regel: {", ".join(sorted(used - css)) or "keine"}')
    print('CSS-Klassen, die kein Partial fest nennt (vom View-Model gesetzt, Variante oder unbenutzt): '
          + (', '.join(sorted(css - used)) or 'keine'))
    for p in problems:
        print(f'FEHLER  {p}')
    return 1 if problems else 0


def schema_errors(data, schema: dict) -> list[str]:
    """Verstöße gegen ein Schema als „Pfad: Meldung“. Maßgeblich ist tools/schema_lite.py (läuft ohne Installation).
    Ist das Paket jsonschema vorhanden, prüft es zusätzlich; was nur es findet, wird mit „(jsonschema)“ gemeldet."""
    try:
        found = schema_lite.errors(data, schema)
    except schema_lite.SchemaError as e:
        raise BuildError(f'Schema {schema.get("$id", "")}: {e}')
    out = [f'{where}: {message}' for where, message in sorted(found)]
    try:
        import jsonschema  # optional, nicht Teil der Standardbibliothek
    except ImportError:
        return out
    seen = {where for where, _ in found}
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for e in sorted(validator.iter_errors(data), key=lambda e: [str(x) for x in e.path]):
        where = '/'.join(str(x) for x in e.path) or '(root)'
        if where not in seen:
            out.append(f'{where}: {e.message} (jsonschema)')
    return out


def cmd_validate(args) -> int:
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
        checks.append((path / 'job_information' / 'job.json', 'job.schema.json'))
        if (path / 'application' / 'application-manifest.json').is_file():  # fehlt bei Status captured
            checks.append((path / 'application' / 'application-manifest.json', 'application-manifest.schema.json'))
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
        errors = schema_errors(read_json(file), read_json(SCHEMAS / schema))
        print(f'{"ok    " if not errors else "FEHLER"}  {rel(file)}')
        for line in errors[:20]:
            print(f'        {line}')
        bad += bool(errors)
    for posting in postings:
        if posting_info(posting)['dropped']:
            continue  # aussortiert: weder E-Mail-Entwurf noch offene Fragen blockieren
        state, msg = email_draft_state(posting)
        built = (posting / 'application' / 'application-manifest.json').is_file()
        if state == 'ok':
            print(f'ok      {rel(posting / "application" / "email.md")}')
        elif msg and built:  # Status captured (noch keine Mappe): der Entwurf ist noch nicht fällig
            print(f'FEHLER  {msg}')
            bad += 1
        job_file = posting / 'job_information' / 'job.json'
        if not job_file.is_file():
            continue
        blocking, answered = question_state(read_json(job_file))
        for q in blocking:
            print(f'FEHLER  {rel(job_file)}: blockierende Frage offen: {q.get("question", "")}')
        bad += bool(blocking)
        if answered:
            print(f'Hinweis {rel(job_file)}: {answered} beantwortete Frage(n) noch nicht eingearbeitet '
                  '(open_questions mit status answered)')
    return 1 if bad else 0


def profile_dir_arg(path: str) -> Path:
    pdir = Path(path).resolve()
    return pdir if pdir.parent == PROFILE_ROOT.resolve() else profile_dir_of(pdir)


def cmd_check_duplicate(args) -> int:
    """Vergleicht eine Stelle mit allen anderen Stellenordnern des Profils (auch sent/ und dropped/).

    Exit 3 nur bei same_posting ohne gespeicherte Entscheidung: gleiche Referenznummer, oder gleicher
    Schlüssel mit einer Stelle, die nicht aussortiert ist."""
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    pdir = info['profile_dir']
    job = read_json(posting / 'job_information' / 'job.json')
    key, blocking, lines, others = dup_key(job), 0, [], 0
    for other in iter_postings(pdir):
        if other == posting:
            continue
        try:
            oinfo, ojob = posting_info(other), read_json(other / 'job_information' / 'job.json')
        except BuildError as e:
            print(f'Warnung: {rel(other)} übersprungen ({e})', file=sys.stderr)
            continue
        others += 1
        okey = dup_key(ojob)
        cls = dup_class(key, okey)
        if not cls:
            continue
        drop = read_drop(other) if oinfo['dropped'] else None
        line = (f'{cls}: {ojob.get("reference_number") or "-"} · {ojob.get("company", "")} · {ojob.get("title", "")} · '
                f'{oinfo["folder"]}')
        if cls == 'same_posting':
            decision = dup_decision(job, ojob)
            if key['ref'] and key['ref'] == okey['ref']:
                line += ' · gleiche Referenznummer'
                blocking += 1
            elif decision:
                line += f' · entschieden: {decision}'
            elif drop is not None:
                line += f' · bereits aussortiert: {drop[0]}'
            else:
                line += ' · ungeklärt'
                blocking += 1
        elif drop is not None:
            line += f' · aussortiert: {drop[0]}'
        lines.append(line)
    if not lines:
        print(f'Kein Duplikat ({others} andere Stellenordner geprüft).')
        return 0
    for line in sorted(lines, key=lambda x: (not x.startswith('same_posting'), x)):
        print(line)
    if blocking:
        print(f'{blocking} ungeklärtes Duplikat (same_posting): Nutzer fragen; Entscheidung in job.json '
              '(duplicate_decision) festhalten oder eine der Stellen mit drop aussortieren.')
        return 3
    print('Kein ungeklärtes Duplikat; die Zeilen oben sind Hinweise.')
    return 0


def next_step(entry: dict, posting: Path, job: dict) -> str:
    """Nächster Schritt einer Stelle für die Übersicht; <ordner> steht für den Stellenordner der Zeile."""
    status = entry['status']
    if status == 'dropped':
        return f'– ({entry.get("drop_reason", "")})'
    blocking, answered = question_state(job)
    if status in ('captured', 'draft', 'html_approved') and blocking:
        return 'blockierende Frage klären (job.json open_questions), Frage dann auf resolved setzen'
    if status in ('captured', 'draft') and answered:
        return 'Antworten in job.json einarbeiten (open_questions: answered → resolved)'
    if status == 'captured':
        return 'Texte schreiben (references/fan-out.md), dann: application <ordner> --qa'
    if status == 'draft':
        man_path = posting / 'application' / 'application-manifest.json'
        val = (read_json(man_path).get('validation') or {}) if man_path.is_file() else {}
        if email_draft_state(posting)[1] or val.get('overflow') or val.get('placeholders_remaining') \
                or val.get('missing_assets'):
            return 'QA-Befunde beheben: application <ordner> --qa'
        return 'Freigabe des Nutzers einholen, dann: status <ordner> html_approved'
    return {
        'html_approved': 'application <ordner> --qa --pdf',
        'pdf_exported': f'Nutzer sendet; nach Bestätigung: mark-sent <ordner> --channel {entry.get("channel", "email")}',
        'sent': 'Rückmeldung abwarten: status <ordner> interview|offer|rejected|withdrawn',
        'interview': 'Ergebnis eintragen: status <ordner> offer|rejected|withdrawn',
    }.get(status, '–')


def status_overview(path: Path) -> int:
    """Eine Zeile pro Stelle aus dem frisch abgeglichenen Ledger, aktive nach Frist, aussortierte am Ende."""
    pdir = profile_dir_arg(str(path))
    ledger, warnings = sync_ledger(pdir)
    only = None if path == pdir else posting_info(path)['folder']
    rows, jobs = [], {}
    for e in ledger['entries']:
        posting = pdir / e['folder']
        try:
            job = read_json(posting / 'job_information' / 'job.json')
        except BuildError:
            job = {}
        jobs[e['folder']] = job
        if only and e['folder'] != only:
            continue
        deadline = e.get('deadline', '')
        iso = re.fullmatch(r'\d{4}-\d{2}-\d{2}', deadline)
        shown = short_date(deadline) if iso else (deadline[:11] + '…' if len(deadline) > 12 else deadline or '–')
        if iso and deadline < today() and e['status'] in STATUSES[:4]:
            shown += ' !'
        rows.append((e['status'] == 'dropped', deadline if iso else '9999', ledger_sort_key(e),
                     e, shown, next_step(e, posting, job)))
    if not rows:
        print(f'Keine Stellen erfasst unter {rel(pdir)}/applications/.')
        return 0
    rows.sort(key=lambda r: r[:3])
    groups ={'/'.join(ledger_sort_key(r[3]).split('/')[:2]) for r in rows}
    cut = len(next(iter(groups))) + 1 if len(groups) == 1 else 0
    names = [ledger_sort_key(r[3])[cut:] for r in rows]
    width = max((len(n) for n in names), default=6)
    print(f'Stellen von {pdir.name} (Stand {today()}); <ordner> = {rel(pdir)}/applications/[sent/|dropped/]'
          f'{next(iter(groups)) + "/" if cut else ""}<ORDNER der Zeile>')
    print(f'{"STATUS":<13} {"FRIST":<12} {"WEG":<7} {"BLK":>3}  {"ORDNER":<{width}}  NÄCHSTER SCHRITT')
    for (_, _, _, e, shown, step), name in zip(rows, names):
        print(f'{e["status"]:<13} {shown:<12} {e.get("channel", "unknown"):<7} {e.get("open_blocking", "–"):>3}  '
              f'{name:<{width}}  {step}')
    if only:
        return 0
    entries = ledger['entries']
    active = [e for e in entries if e['status'] != 'dropped']
    counts = Counter(e['status'] for e in active)
    blocked = [e for e in active if e.get('open_blocking')]
    print(f'Summe: {len(active)} aktiv ('
          + ', '.join(f'{s} {counts[s]}' for s in STATUSES if counts.get(s)) + f') · {len(entries) - len(active)} '
          f'aussortiert (dropped) · blockierend offen: {sum(e["open_blocking"] for e in blocked)} Fragen in '
          f'{len(blocked)} Stellen · BLK = offene blockierende Fragen; „!“ = Frist abgelaufen')
    notes = []
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            ja, jb = jobs.get(a['folder']) or {}, jobs.get(b['folder']) or {}
            cls = dup_class(dup_key(ja), dup_key(jb)) if ja and jb else None
            if not cls:
                continue
            extra = ''
            if cls == 'same_posting':
                extra = dup_decision(ja, jb)
                extra = f' · entschieden: {extra}' if extra else ' · ungeklärt: check-duplicate <ordner>'
            notes.append(f'  {cls:<24} {ledger_sort_key(a)[cut:]} ↔ {ledger_sort_key(b)[cut:]}{extra}')
    if notes:
        print('Hinweise der Duplikatprüfung (references/applications.md, Duplikate):')
        print('\n'.join(sorted(notes)))
    for w in warnings:
        print(f'Warnung: {w}', file=sys.stderr)
    return 0


def cmd_ledger(args) -> int:
    pdir = profile_dir_arg(args.dir)
    before = ledger_path(pdir).read_bytes() if ledger_path(pdir).is_file() else None
    ledger, warnings = sync_ledger(pdir)
    after = ledger_path(pdir).read_bytes() if ledger_path(pdir).is_file() else None
    counts = Counter(e['status'] for e in ledger['entries'])
    print(f'Ledger {rel(ledger_path(pdir))}: {len(ledger["entries"])} Einträge ('
          + ', '.join(f'{s} {counts[s]}' for s in STATUSES if counts.get(s)) + ') · '
          + ('unverändert' if before == after else 'aktualisiert'))
    for w in warnings:
        print(f'Warnung: {w}', file=sys.stderr)
    return 1 if warnings else 0


def cmd_status(args) -> int:
    if args.status is None:
        return status_overview(Path(args.dir).resolve())
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    pdir = info['profile_dir']
    if args.status not in STATUSES:
        raise BuildError(f'Status muss einer von {", ".join(STATUSES)} sein')
    if args.status == 'sent' and not getattr(args, 'from_mark_sent', False):
        raise BuildError('Status „sent“ nur über mark-sent: build_mappe.py mark-sent "<stellenordner>" '
                         '--channel email|post|portal (verschiebt den Ordner nach applications/sent/ und '
                         'aktualisiert das Ledger in einem Schritt).')
    if args.status == 'dropped':
        raise BuildError('Status „dropped“ nur über drop: build_mappe.py drop "<stellenordner>" --reason "…" '
                         '(verschiebt den Ordner nach applications/dropped/ und hält den Grund fest).')
    if args.status == 'captured':
        raise BuildError('Status „captured“ wird nicht gesetzt: Er gilt für jede erfasste Stelle ohne gebaute Mappe.')
    if info['dropped']:
        raise BuildError(f'Die Stelle ist aussortiert. Zurückholen: build_mappe.py restore "{rel(posting)}"')
    if args.status == 'html_approved':
        _, email_msg = email_draft_state(posting)
        if email_msg:
            print(f'Warnung: {email_msg} Das PDF wird erst mit Entwurf erzeugt.', file=sys.stderr)
    man_path = posting / 'application' / 'application-manifest.json'
    if not man_path.is_file():
        raise BuildError(f'Noch keine Mappe gebaut (Status captured): zuerst build_mappe.py application "{rel(posting)}" --qa')
    manifest = read_json(man_path)
    job = read_json(posting / 'job_information' / 'job.json')
    ensure_history(manifest, find_entry(load_ledger(pdir), info['folder'], job.get('reference_number')))
    stamp = (dt.datetime.fromisoformat(args.date).astimezone().replace(microsecond=0).isoformat()
             if args.date else now_iso())
    if args.status == 'html_approved':
        html_file = posting / 'application' / manifest.get('html', html_name(info['user']))
        if not html_file.is_file():
            raise BuildError(f'HTML-Fassung fehlt: {rel(html_file)}. Zuerst: build_mappe.py application '
                             f'"{rel(posting)}" --qa')
        if html_file.read_text(encoding='utf-8') != expected_application(posting)[1]:
            raise BuildError(f'Die gespeicherte Mappe {rel(html_file)} entspricht nicht ihren Quellen (Text, Profil '
                             'oder Vorlage wurden nach dem Bau geändert). Freigeben lässt sich nur, was der Nutzer '
                             f'gesehen hat: zuerst build_mappe.py application "{rel(posting)}" --qa, die Mappe zeigen '
                             'und erneut fragen.')
        manifest['approved_at'] = stamp
        manifest['approved_sha256'] = document_hash(html_file)  # genau dieser Stand ist freigegeben
    manifest['status'] = args.status
    if args.status == 'sent':
        manifest['sent_at'] = stamp
    if args.channel:
        manifest['channel'] = args.channel
    add_history(manifest, args.status, stamp, args.note)
    write_json(man_path, manifest)
    sync_ledger(pdir)
    print(f'Status {args.status}: {info["folder"]}')
    return 0


def move_posting(posting: Path, target: Path, info: dict) -> None:
    """Stellenordner verschieben und leer gewordene Elternordner bis zum Typordner entfernen."""
    if target.exists():
        raise BuildError(f'Ziel existiert bereits: {rel(target)}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(posting), str(target))
    stop = info['profile_dir'] / 'applications'
    for parent in posting.parents:
        if parent == stop or stop not in parent.parents or parent.name in (*TYPES, *AREAS) or any(parent.iterdir()):
            break
        parent.rmdir()


def cmd_mark_sent(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if info['sent']:
        raise BuildError('Diese Bewerbung liegt bereits unter applications/sent/.')
    if info['dropped']:
        raise BuildError(f'Die Stelle ist aussortiert. Zurückholen: build_mappe.py restore "{rel(posting)}"')
    manifest = read_json(posting / 'application' / 'application-manifest.json')
    if manifest['status'] not in ('pdf_exported', 'html_approved'):
        raise BuildError(f'Status ist {manifest["status"]}: erst freigeben und PDF exportieren.')
    if not (posting / 'application' / html_name(info['user'], 'pdf')).is_file():
        print('Warnung: Kein PDF im Bewerbungsordner gefunden.', file=sys.stderr)
    parts = info['folder'].split('/')
    target = info['profile_dir'] / 'applications' / 'sent' / Path(*parts[1:])
    move_posting(posting, target, info)
    args.dir, args.status, args.from_mark_sent = str(target), 'sent', True
    cmd_status(args)
    print(f'Verschoben nach {rel(target)}')
    return 0


def cmd_drop(args) -> int:
    """Stelle aussortieren: einziger Weg zum Status dropped (Ordner, DROPPED.txt und Ledger in einem Schritt)."""
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if info['dropped']:
        raise BuildError('Diese Stelle liegt bereits unter applications/dropped/.')
    if info['sent']:
        raise BuildError('Diese Bewerbung ist gesendet. Rückzug: build_mappe.py status "<stellenordner>" withdrawn')
    if not (posting / 'job_information' / 'job.json').is_file():
        raise BuildError(f'Datei fehlt: {rel(posting / "job_information" / "job.json")}')
    reason = ' '.join(args.reason.split())
    if not reason:
        raise BuildError('Grund fehlt: --reason "…"')
    date = dt.date.fromisoformat(args.date).isoformat() if args.date else today()
    parts = info['folder'].split('/')
    target = info['profile_dir'] / 'applications' / 'dropped' / Path(*parts[1:])
    move_posting(posting, target, info)
    (target / DROP_FILE).write_text(f'{reason}\nDatum: {date}\n', encoding='utf-8')
    sync_ledger(info['profile_dir'])
    print(f'Aussortiert: {rel(target)} ({reason})')
    return 0


def cmd_restore(args) -> int:
    posting = Path(args.dir).resolve()
    info = posting_info(posting)
    if not info['dropped']:
        raise BuildError('Nur Ordner unter applications/dropped/ lassen sich zurückholen.')
    parts = info['folder'].split('/')
    target = info['profile_dir'] / 'applications' / Path(*parts[2:])
    move_posting(posting, target, info)
    (target / DROP_FILE).unlink(missing_ok=True)
    sync_ledger(info['profile_dir'])
    print(f'Zurückgeholt: {rel(target)}')
    return 0


def cmd_stats(args) -> int:
    pdir = profile_dir_arg(args.dir)
    entries = sync_ledger(pdir)[0]['entries']
    dropped = sum(1 for e in entries if e['status'] == 'dropped')
    print(f'Stellen von {pdir.name}: {len(entries)} ({len(entries) - dropped} aktiv, {dropped} aussortiert)')
    for title, counter in (('Status', Counter(e['status'] for e in entries)),
                           ('Typ', Counter(e['type'] for e in entries)),
                           ('Angelegt pro Monat', Counter(e.get('created_at', '')[:7] for e in entries)),
                           ('Gesendet pro Monat', Counter(e['sent_at'][:7] for e in entries if e.get('sent_at'))),
                           ('Kanal (gesendet)', Counter(e.get('channel', '') for e in entries if e.get('sent_at')))):
        if counter:
            print(f'{title}: ' + ', '.join(f'{k or "-"} {v}' for k, v in sorted(counter.items())))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Alle Befehle und Schalter. tools/check_repo.py docs liest sie hier ab und prüft damit die Doku."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('profile-template'); s.add_argument('dir'); s.add_argument('--qa', choices=QA_MODES)
    s.add_argument('--pdf', action='store_true'); s.set_defaults(fn=cmd_profile_template)
    s = sub.add_parser('application'); s.add_argument('dir'); s.add_argument('--qa', choices=QA_MODES)
    s.add_argument('--pdf', action='store_true'); s.set_defaults(fn=cmd_application)
    s = sub.add_parser('qa'); s.add_argument('html'); s.add_argument('--fast', action='store_true')
    s.set_defaults(fn=cmd_qa)
    s = sub.add_parser('preview'); s.add_argument('html'); s.add_argument('out')
    s.add_argument('--dpi', type=int, default=70); s.set_defaults(fn=cmd_preview)
    s = sub.add_parser('snapshot'); s.add_argument('html', nargs='+')
    mode = s.add_mutually_exclusive_group(required=True)
    mode.add_argument('--save', action='store_true'); mode.add_argument('--compare', action='store_true')
    s.add_argument('--name'); s.add_argument('--tolerance', type=int, default=0); s.set_defaults(fn=cmd_snapshot)
    s = sub.add_parser('master'); s.add_argument('--check', action='store_true'); s.set_defaults(fn=cmd_master)
    s = sub.add_parser('rebuild'); s.add_argument('target', nargs='+'); s.add_argument('--check', action='store_true')
    s.set_defaults(fn=cmd_rebuild)
    s = sub.add_parser('contract'); s.set_defaults(fn=cmd_contract)
    s = sub.add_parser('validate'); s.add_argument('dir'); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser('check-duplicate'); s.add_argument('dir'); s.set_defaults(fn=cmd_check_duplicate)
    s = sub.add_parser('ledger'); s.add_argument('action', choices=['sync']); s.add_argument('dir')
    s.set_defaults(fn=cmd_ledger)
    s = sub.add_parser('status'); s.add_argument('dir'); s.add_argument('status', nargs='?')
    s.add_argument('--channel', choices=['email', 'post', 'portal']); s.add_argument('--date')
    s.add_argument('--note'); s.set_defaults(fn=cmd_status)
    s = sub.add_parser('mark-sent'); s.add_argument('dir')
    s.add_argument('--channel', choices=['email', 'post', 'portal'], required=True); s.add_argument('--date')
    s.add_argument('--note'); s.set_defaults(fn=cmd_mark_sent)
    s = sub.add_parser('drop'); s.add_argument('dir'); s.add_argument('--reason', required=True)
    s.add_argument('--date'); s.set_defaults(fn=cmd_drop)
    s = sub.add_parser('restore'); s.add_argument('dir'); s.set_defaults(fn=cmd_restore)
    s = sub.add_parser('stats'); s.add_argument('dir'); s.set_defaults(fn=cmd_stats)
    return ap


def main(argv=None) -> int:
    ap = build_parser()
    # „--qa“ ohne Wert heißt volle Prüfung; so bleibt die Reihenfolge von Schalter und Ordner frei.
    argv = ['--qa=full' if a == '--qa' else a for a in (sys.argv[1:] if argv is None else argv)]
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
