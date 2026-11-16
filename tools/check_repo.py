#!/usr/bin/env python3
"""Repository-Prüfungen vor dem Commit (nur Python-Standardbibliothek). Regeln: references/qa-and-export.md.

Befehle:
  privacy   Persönliche Daten in Dateien, die Git aufnimmt (getrackt oder neu und nicht ignoriert), in ihren
            Pfaden und im Staging-Diff. Die Suchmuster entstehen aus jedem Profil unter profile/ (Name, Telefon,
            E-Mail, eigene Domain, Straße, PLZ mit Ort, Geburtsdatum, Geburtsort) und aus der optionalen Datei
            profile/privacy-needles.txt (ein Suchtext pro Zeile). Meldet Datei, Zeile und Art, nie den Wert.
  stray     Dateien außerhalb der Konventionen: unbekannter Ort, leere Datei, Reste wie *.orig, *.bak, EOF.
  schemas   Alle JSON-Dateien lesbar; Schemas in sich stimmig; Vorlagen passen in Feldern und Typen zum Schema.
  template  Die Master-Vorlage assets/bewerbungsmappe.html entspricht Byte für Byte ihren Quellen unter
            assets/mappe/ (build_mappe.py master); jedes Partial hält seinen Vertrag ein (build_mappe.py contract).
  pins      Jede geänderte Datei unter assets/mappe/ ist von einer Anfrage in der Warteschlange gedeckt
            (tools/pin_queue.py, references/tencil.md).
  docs      Die Doku passt zum Repository: jede Regel-Id (<!-- rule: id -->) genau einmal, Verweise treffen ihr
            Zuhause; Pfade, Dateinamen, Befehle, Schalter, Schemafelder und Symbol-Ids existieren; Zahlen passen
            zu assets/mappe/limits.json bzw. zu gezählten Werten; keine Formulierung aus tools/stale-terms.txt.
  all       alle Prüfungen oben. Mehrere Namen hintereinander führen genau diese aus.
  rules     Liste aller Regeln mit Datei und Zeile ihres Zuhauses.
  hook      Für den Claude-Code-Hook PostToolUse (Edit|Write): liest das Hook-JSON von stdin und prüft nur die
            geänderte Datei; je nach Datei zusätzlich template, pins und docs.
            Exit 2 mit Meldung auf stderr bei Befund, sonst still.

Option --quiet: keine Ausgabe ohne Befund. Exit-Codes: 0 ok, 1 Befund (hook: 2).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = '.agents/skills/bewerbungshelfer'

# Vom Nutzer ausdrücklich akzeptierte Fundstellen; sie werden vor der Suche ausgeblendet.
ALLOW = (
    'tencil.dnanu.de',  # Hostname der entfernten Vorlagen-Vorschau in references/tencil.md
)
# Bei diesen Anbietern ist die Domain einer E-Mail-Adresse kein persönliches Merkmal.
PUBLIC_MAIL = {'gmail.com', 'googlemail.com', 'gmx.de', 'gmx.net', 'gmx.at', 'gmx.ch', 'web.de', 'outlook.com',
               'outlook.de', 'hotmail.com', 'hotmail.de', 'live.de', 'live.com', 'yahoo.com', 'yahoo.de',
               'icloud.com', 'me.com', 't-online.de', 'posteo.de', 'mailbox.org', 'proton.me', 'protonmail.com',
               'freenet.de', 'aol.com', 'mail.de', 'email.de', 'online.de', 'arcor.de', 'vodafone.de', 'tuta.io'}
MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober',
          'November', 'Dezember']

# Orte, an denen Git-Dateien liegen dürfen; * steht für einen Namen ohne Schrägstrich.
ALLOWED = (
    '.gitignore', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'LICENSE', 'CHANGELOG.md',
    f'{SKILL}/SKILL.md',
    f'{SKILL}/agents/*.yaml',
    f'{SKILL}/assets/bewerbungsmappe.html',
    f'{SKILL}/assets/mappe/*.css', f'{SKILL}/assets/mappe/icons.svg', f'{SKILL}/assets/mappe/qa.js',
    f'{SKILL}/assets/mappe/qa.html', f'{SKILL}/assets/mappe/master.json', f'{SKILL}/assets/mappe/limits.json',
    f'{SKILL}/assets/mappe/partials/*.html',
    f'{SKILL}/assets/fonts/*.woff2', f'{SKILL}/assets/fonts/OFL.txt', f'{SKILL}/assets/fonts/README.md',
    f'{SKILL}/assets/icons/*.md', f'{SKILL}/assets/icons/sources.json',
    f'{SKILL}/assets/schemas/*.schema.json',
    f'{SKILL}/assets/templates/*.json', f'{SKILL}/assets/templates/*.md',
    f'{SKILL}/references/*.md',
    '.claude/agents/*.md', '.claude/settings.json', '.claude/skills/bewerbungshelfer',
    'profile/README.md', 'profile/import/.gitkeep', 'profile/assets/.gitkeep',
    'tools/*.py', 'tools/hooks/pre-commit', 'tools/stale-terms.txt',
)
LEFTOVER = re.compile(r'(\.(orig|rej|bak|tmp|swp|pyc)|~)$|^(EOF|\.DS_Store|nohup\.out)$')
TEMPLATE_SCHEMA = {'job.json': 'job.schema.json', 'ledger.json': 'ledger.schema.json',
                   'profile.json': 'profile.schema.json',
                   'application-manifest.json': 'application-manifest.schema.json'}
JSON_TYPES = {'string': str, 'object': dict, 'array': list, 'boolean': bool, 'null': type(None)}


def git(*args: str) -> str:
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def git_files() -> list[str]:
    """Getrackte Dateien und neue, nicht ignorierte Dateien (alles, was ein Commit aufnehmen würde)."""
    out = git('ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return sorted({f for f in out.split('\0') if f and ((ROOT / f).is_file() or (ROOT / f).is_symlink())})


def read_text(rel: str) -> str | None:
    """Textinhalt einer regulären Datei; None für Symlinks, Ordner und Binärdateien."""
    path = ROOT / rel
    if path.is_symlink() or not path.is_file():
        return None
    data = path.read_bytes()
    if b'\0' in data[:8192]:
        return None
    return data.decode('utf-8', errors='replace')


# --------------------------------------------------------------------------- privacy

def translit(text: str) -> str:
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss'), ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue')):
        text = text.replace(a, b)
    return text


def word(text: str) -> str:
    """Muster für ein Wort zwischen Nicht-Buchstaben; Leerraum und Bindestriche flexibel, auch ohne Umlaute."""
    forms = {text, translit(text)}
    body = '|'.join(re.sub(r'(\\ |\\-)+', r'[\\s._-]*', re.escape(f)) for f in sorted(forms))
    return rf'(?<![^\W\d_])(?:{body})(?![^\W\d_])'


def profile_needles(profile: dict, folder: str) -> list[tuple[str, str]]:
    person = profile.get('person') or {}
    address = person.get('address') or {}
    out: list[tuple[str, str]] = []
    names = {person.get('first_name') or '', person.get('last_name') or '', *(person.get('name') or '').split(),
             *folder.split('.')}
    out += [('Name', word(n)) for n in sorted(names) if len(n) >= 3]
    digits = re.sub(r'\D', '', person.get('phone') or '')
    digits = re.sub(r'^(00)?49', '', digits) if (person.get('phone') or '').strip().startswith(('+', '00')) \
        else digits.lstrip('0')
    if len(digits) >= 6:
        # ohne Landes- und Ortsnetz-Präfix, damit +49 …, 0049 … und 0… gleichermaßen treffen
        out.append(('Telefon', r'[\s\-/().]*'.join(digits) + r'(?!\d)'))
    email = (person.get('email') or '').strip()
    if '@' in email:
        out.append(('E-Mail', re.escape(email)))
        domain = email.rsplit('@', 1)[1].lower()
        if domain not in PUBLIC_MAIL:
            out.append(('eigene Domain', r'(?<![\w-])' + re.escape(domain) + r'(?![\w-])'))
    street = re.sub(r'\s+\d+\s*[a-zA-Z]?(\s*[-/]\s*\d+\s*[a-zA-Z]?)?$', '', (address.get('street') or '').strip())
    m = re.fullmatch(r'(.{3,}?)[\s-]*(straße|strasse|str\.?)', street, re.I)
    if m:
        stems = '|'.join(sorted({re.escape(m.group(1)), re.escape(translit(m.group(1)))}))
        out.append(('Straße', rf'(?<![^\W\d_])(?:{stems})[\s-]*(?:straße|strasse|str(?![^\W\d_]))'))
    elif len(street) >= 4:
        out.append(('Straße', word(street)))
    if address.get('postal_code') and address.get('city'):
        out.append(('PLZ mit Ort', re.escape(address['postal_code']) + r'\s+' + word(address['city'])))
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', person.get('birth_date') or '')
    if m:
        y, mo, d = m.groups()
        out.append(('Geburtsdatum', rf'(?<!\d)(?:{y}-{mo}-{d}|0?{int(d)}\.\s*(?:0?{int(mo)}\.|{MONTHS[int(mo) - 1]})\s*{y})(?!\d)'))
    place = (person.get('birth_place') or '').split(',')[0].strip()
    if len(place) >= 3:
        out.append(('Geburtsort', word(place)))
    return out


def load_needles() -> list[tuple[str, re.Pattern]]:
    """Suchmuster aus allen Profilen unter profile/ und aus profile/privacy-needles.txt."""
    raw: list[tuple[str, str]] = []
    for path in sorted((ROOT / 'profile').glob('*/assets/profile/*.json')):
        try:
            profile = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(profile, dict) and isinstance(profile.get('person'), dict):
            raw += profile_needles(profile, path.parents[2].name)
    extra = ROOT / 'profile' / 'privacy-needles.txt'
    if extra.is_file():
        raw += [('eigener Suchtext', re.escape(line.strip())) for line in extra.read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.lstrip().startswith('#')]
    return [(label, re.compile(pattern, re.I)) for label, pattern in dict.fromkeys(raw)]


def mask(text: str) -> str:
    """Akzeptierte Fundstellen und lange Base64-Blöcke (eingebettete Schriften, Bilder) ausblenden."""
    for allowed in ALLOW:
        text = re.sub(re.escape(allowed), lambda m: '\0' * len(m.group(0)), text, flags=re.I)
    return re.sub(r'[A-Za-z0-9+/]{200,}={0,2}', lambda m: '\0' * len(m.group(0)), text)


def scan(text: str, needles: list[tuple[str, re.Pattern]]) -> list[tuple[int, str]]:
    text = mask(text)
    hits = {(text.count('\n', 0, m.start()) + 1, label) for label, rx in needles for m in rx.finditer(text)}
    return sorted(hits)


def staged_additions() -> list[tuple[str, int, str]]:
    """(Datei, Zeile, Text) aller im Index hinzugefügten Zeilen."""
    out, file, line = [], '', 0
    # feste Präfixe: diff.mnemonicPrefix oder diff.noprefix des Nutzers würden die Kopfzeilen ändern
    for row in git('diff', '--cached', '-U0', '--no-color', '--no-ext-diff', '--src-prefix=a/',
                   '--dst-prefix=b/').splitlines():
        if row.startswith('+++ '):
            file = row[6:] if row.startswith('+++ b/') else ''
        elif row.startswith('@@'):
            m = re.match(r'@@ -\S+ \+(\d+)', row)
            line = int(m.group(1)) if m else 0
        elif row.startswith('+') and file:
            out.append((file, line, row[1:]))
            line += 1
    return out


def check_privacy(files: list[str] | None = None) -> list[str]:
    needles = load_needles()
    full = files is None
    files = git_files() if full else files
    out = []
    for rel in files:
        if rel.startswith('profile/') and rel not in ('profile/README.md', 'profile/import/.gitkeep',
                                                      'profile/assets/.gitkeep'):
            out.append(f'privacy: {rel}: Datei unter profile/ würde ins Repository gelangen (.gitignore prüfen)')
        if rel.startswith('.tmp/'):
            out.append(f'privacy: {rel}: Datei unter .tmp/ würde ins Repository gelangen (.gitignore prüfen)')
        out += [f'privacy: {rel}: Pfad enthält {label}' for _, label in scan(rel, needles)]
        text = read_text(rel)
        if text is not None:
            out += [f'privacy: {rel}:{line}: {label}' for line, label in scan(text, needles)]
    if full:
        for rel, line, text in staged_additions():
            out += [f'privacy: {rel}:{line} (Staging): {label}' for _, label in scan(text, needles)]
    return list(dict.fromkeys(out))


# --------------------------------------------------------------------------- stray

def allowed_path(rel: str) -> bool:
    return any(re.fullmatch('[^/]*'.join(re.escape(part) for part in pattern.split('*')), rel) for pattern in ALLOWED)


def check_stray(files: list[str] | None = None) -> list[str]:
    out = []
    for rel in git_files() if files is None else files:
        path, name = ROOT / rel, rel.rsplit('/', 1)[-1]
        if LEFTOVER.search(name) or re.search(r'[^\x21-\x7e]', rel):
            out.append(f'stray: {rel}: Rest- oder Zufallsdatei (Name mit Leerzeichen, Sonderzeichen oder Endung wie .orig/.bak)')
        elif not allowed_path(rel):
            out.append(f'stray: {rel}: liegt außerhalb der Konventionen (erlaubte Orte: ALLOWED in tools/check_repo.py)')
        if path.is_file() and not path.is_symlink() and path.stat().st_size == 0 and name != '.gitkeep':
            out.append(f'stray: {rel}: leere Datei')
    return out


# --------------------------------------------------------------------------- schemas

def resolve(schema: dict, root: dict) -> dict:
    while isinstance(schema, dict) and isinstance(schema.get('$ref'), str) and schema['$ref'].startswith('#/'):
        node = root
        for part in schema['$ref'][2:].split('/'):
            node = node[part]
        schema = node
    return schema


def schema_problems(node, root: dict, where: str, out: list[str]) -> None:
    """Innere Stimmigkeit eines Schemas: Verweise, Pflichtfelder, Aufzählungen, Muster, Typen."""
    if isinstance(node, list):
        for i, item in enumerate(node):
            schema_problems(item, root, f'{where}[{i}]', out)
        return
    if not isinstance(node, dict):
        return
    ref = node.get('$ref')
    if isinstance(ref, str) and ref.startswith('#/'):
        try:
            resolve(node, root)
        except (KeyError, TypeError):
            out.append(f'{where}: $ref {ref} zeigt ins Leere')
    props = node.get('properties')
    if isinstance(props, dict) and node.get('additionalProperties') is False:
        out += [f'{where}: Pflichtfeld „{k}“ fehlt in properties' for k in node.get('required', []) if k not in props]
    if 'enum' in node and not (isinstance(node['enum'], list) and node['enum']):
        out.append(f'{where}: enum ist leer')
    if isinstance(node.get('pattern'), str):
        try:
            re.compile(node['pattern'])
        except re.error as e:
            out.append(f'{where}: pattern ungültig ({e})')
    types = node.get('type')
    for t in [types] if isinstance(types, str) else types if isinstance(types, list) else []:
        if t not in (*JSON_TYPES, 'integer', 'number'):
            out.append(f'{where}: unbekannter type „{t}“')
    for key, value in node.items():
        if key in ('enum', 'const', 'required', 'examples', 'default'):
            continue
        if key in ('properties', '$defs', 'patternProperties') and isinstance(value, dict):
            for name, sub in value.items():
                schema_problems(sub, root, f'{where}/{name}', out)
        else:
            schema_problems(value, root, f'{where}/{key}' if isinstance(value, dict) else where, out)


def type_ok(value, t: str) -> bool:
    if t == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if t == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, JSON_TYPES[t])


def shape_problems(value, schema: dict, root: dict, where: str, out: list[str]) -> None:
    """Vorlage gegen Schema: unbekannte und fehlende Felder, Typen, enum und const. Leere Platzhalter ('')
    sind erlaubt; Längen, Formate und Bedingungen (if/then) prüft erst validate an echten Daten."""
    schema = resolve(schema, root)
    if not isinstance(schema, dict):
        return
    types = schema.get('type')
    types = [types] if isinstance(types, str) else types or []
    if types and not any(type_ok(value, t) for t in types):
        out.append(f'{where}: Typ passt nicht (Schema: {"/".join(types)})')
        return
    if value != '' and 'enum' in schema and value not in schema['enum']:
        out.append(f'{where}: Wert {value!r} steht nicht in enum')
    if value != '' and 'const' in schema and value != schema['const']:
        out.append(f'{where}: Wert {value!r} ist nicht {schema["const"]!r}')
    if isinstance(value, dict):
        props = schema.get('properties') or {}
        if schema.get('additionalProperties') is False:
            out += [f'{where}: Feld „{k}“ kennt das Schema nicht' for k in value if k not in props]
        out += [f'{where}: Pflichtfeld „{k}“ fehlt' for k in schema.get('required', []) if k not in value]
        for k, v in value.items():
            if k in props:
                shape_problems(v, props[k], root, f'{where}/{k}', out)
    elif isinstance(value, list) and isinstance(schema.get('items'), dict):
        for i, item in enumerate(value):
            shape_problems(item, schema['items'], root, f'{where}[{i}]', out)


def check_schemas(files: list[str] | None = None) -> list[str]:
    out, parsed = [], {}
    for rel in git_files() if files is None else files:
        if not rel.endswith('.json') or (ROOT / rel).is_symlink() or not (ROOT / rel).is_file():
            continue
        try:
            parsed[rel] = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        except ValueError as e:
            out.append(f'schemas: {rel}: kein gültiges JSON ({e})')
    for rel, data in parsed.items():
        if rel.endswith('.schema.json'):
            problems: list[str] = []
            if not isinstance(data, dict) or '$schema' not in data or not str(data.get('$id', '')).endswith(rel.rsplit('/', 1)[-1]):
                problems.append('(root): $schema fehlt oder $id endet nicht auf den Dateinamen')
            schema_problems(data, data, '(root)', problems)
            out += [f'schemas: {rel}: {p}' for p in problems]
    for rel, data in parsed.items():
        name = rel.rsplit('/', 1)[-1]
        if rel.startswith(f'{SKILL}/assets/templates/') and name in TEMPLATE_SCHEMA:
            schema_path = ROOT / SKILL / 'assets' / 'schemas' / TEMPLATE_SCHEMA[name]
            try:
                schema = json.loads(schema_path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                out.append(f'schemas: {rel}: Schema {TEMPLATE_SCHEMA[name]} fehlt oder ist ungültig')
                continue
            problems = []
            shape_problems(data, schema, schema, '(root)', problems)
            out += [f'schemas: {rel}: {p}' for p in problems]
    return out


# --------------------------------------------------------------------------- template

TEMPLATE_SOURCES = (f'{SKILL}/assets/mappe/', f'{SKILL}/assets/fonts/', f'{SKILL}/assets/bewerbungsmappe.html')


def check_template(files: list[str] | None = None) -> list[str]:
    """Die Master-Vorlage ist ein Bauergebnis: Sie muss Byte für Byte dem entsprechen, was assets/mappe/ ergibt,
    und jedes Partial muss seinen Vertrag einhalten (build_mappe.py contract)."""
    import contextlib
    import io
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_mappe
    master = f'{SKILL}/assets/bewerbungsmappe.html'
    try:
        expected = build_mappe.build_master()
        with contextlib.redirect_stdout(io.StringIO()) as report:
            build_mappe.cmd_contract(None)
    except build_mappe.BuildError as e:
        return [f'template: {e}']
    out = [f'template: {line[8:]}' for line in report.getvalue().splitlines() if line.startswith('FEHLER  ')]
    if not (ROOT / master).is_file() or (ROOT / master).read_text(encoding='utf-8') != expected:
        out.append(f'template: {master} entspricht nicht den Quellen unter {SKILL}/assets/mappe/. Die Datei nie von '
                   'Hand ändern; Quellen ändern und neu bauen: python3 tools/build_mappe.py master')
    return out


# --------------------------------------------------------------------------- pins

PIN_SOURCES = f'{SKILL}/assets/mappe/'


def check_pins(files: list[str] | None = None) -> list[str]:
    """Quellen der Vorlage ändert nur, wer eine Anfrage in der Warteschlange hat (tools/pin_queue.py)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import pin_queue
    return [f'pins: {name}: Quelle der Vorlage geändert ohne Anfrage unter .tmp/pins/. Jede Änderung unter '
            f'{PIN_SOURCES} läuft über tools/pin_queue.py (enqueue, next, done; references/tencil.md)'
            for name in pin_queue.uncovered(files)]


# --------------------------------------------------------------------------- docs

STALE_TERMS = 'tools/stale-terms.txt'
DOC_EXEMPT = ('CHANGELOG.md', STALE_TERMS)  # der Verlauf und die Liste selbst dürfen alte Formulierungen nennen
LIMITS = f'{SKILL}/assets/mappe/limits.json'
ICONS = f'{SKILL}/assets/mappe/icons.svg'
ICON_HOME = f'{SKILL}/references/template.md'  # dort steht die Liste aller Symbol-Ids
ICON_SOURCES = f'{SKILL}/assets/icons/sources.json'  # Quelldatei und Farbe je Logo-Symbol
RULE_ID = r'[a-z0-9-]+(?:\.[a-z0-9-]+)+'
RULE_DEF = re.compile(r'<!--\s*rule:\s*(.*?)\s*-->')
RULE_REF = re.compile(rf'\bRegel `({RULE_ID})`(?: in `([^`\n]+)`)?')
SPAN = re.compile(r'`([^`\n]+)`')
PATH_ROOTS = ('references/', 'assets/', 'tools/', '.claude/', '.agents/')
# Ordner eines Profils (profile/<name>/assets/…), nicht des Skills
PROFILE_ASSETS = re.compile(r'assets/\{?(documents|photos|signature|profile)(/|$)')
FILE_NAME = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]*\.(py|css|svg|js|html|json|md|txt|yaml|woff2)')
# Dateinamen, die erst zur Laufzeit oder außerhalb des Repositorys entstehen
LOCAL_NAMES = {'portal_page.md', 'DROPPED.txt', 'privacy-needles.txt', 'tencil.js', 'mail.json', 'sent.json'}
FIELD = re.compile(r'(?:(profile|job):)?([a-z_][a-z_0-9]*(?:\[[^\]]*\])?(?:\.[a-z_][a-z_0-9]*(?:\[[^\]]*\])?)*)')
ICON_ID = re.compile(r'(?:i|dv|si)-[a-z0-9]+(?:-[a-z0-9]+)*')
TOOL_CALL = re.compile(r'\b(build_mappe|check_repo|pin_queue|send_mail|fresh_clone_test|serve_template|devicon_symbols)\.py'
                       r'"?([^`\n#]*)')
FLAG = re.compile(r'(?<![\w-])--[a-z][a-z-]*')
EXTERNAL_FLAGS = {'--help', '--model', '--user', '--now'}  # Schalter anderer Programme, die die Doku nennt
NUMBER_WORDS = {'ein': 1, 'eine': 1, 'zwei': 2, 'drei': 3, 'vier': 4, 'fünf': 5, 'sechs': 6, 'sieben': 7,
                'acht': 8, 'neun': 9, 'zehn': 10}


def split_fences(text: str) -> tuple[str, str]:
    """Fließtext ohne Codeblöcke und Code ohne Fließtext (Codeblöcke und `…`); Zeilennummern bleiben gleich."""
    prose, code, inside = [], [], False
    for line in text.split('\n'):
        fence = line.lstrip().startswith('```')
        prose.append('' if inside or fence else line)
        code.append(line if inside and not fence else '' if fence else ' '.join(f'`{s}`' for s in SPAN.findall(line)))
        inside ^= fence
    return '\n'.join(prose), '\n'.join(code)


def line_of(text: str, pos: int) -> int:
    return text.count('\n', 0, pos) + 1


def rule_index(docs: dict[str, str]) -> tuple[dict[str, tuple[str, int]], list[str]]:
    """Regel-Id -> (Datei, Zeile) ihres Zuhauses; dazu Befunde zu doppelten und falsch geschriebenen Ids."""
    index: dict[str, tuple[str, int]] = {}
    out = []
    for rel, text in docs.items():
        for m in RULE_DEF.finditer(text):
            rid, line = m.group(1), line_of(text, m.start())
            if rid == '<id>':
                continue  # Beschreibung der Schreibweise
            if not re.fullmatch(RULE_ID, rid):
                out.append(f'docs: {rel}:{line}: Regel-Id „{rid}“ hat nicht die Form bereich.name')
            elif rid in index:
                out.append(f'docs: {rel}:{line}: Regel-Id „{rid}“ ist schon in {index[rid][0]}:{index[rid][1]} '
                           'definiert (ein Zuhause pro Regel; andere Dateien verweisen)')
            else:
                index[rid] = (rel, line)
    return index, out


def expand_braces(token: str) -> list[str]:
    m = re.search(r'\{([^{}]*,[^{}]*)\}', token)
    if not m:
        return [token]
    return [x for alt in m.group(1).split(',') for x in expand_braces(token[:m.start()] + alt + token[m.end():])]


def path_target(token: str) -> str | None:
    """Repo-relativer Pfad, auf den ein Pfad aus der Doku zeigt (vom Repository oder vom Skill-Ordner aus)."""
    token = re.sub(r'(:\d+)+$', '', token)
    for base in ('', f'{SKILL}/'):
        candidates = expand_braces(base + token)
        if all(any(ROOT.glob(c)) if '*' in c else (ROOT / c).exists() for c in candidates):
            return candidates[0].rstrip('/')
    return None


def schema_owners() -> tuple[dict[str, dict], dict[str, list[tuple[dict, dict]]]]:
    """Alle Schemas und, je Feldname, jede Stelle (Schema, Unterschema), an der er definiert ist."""
    roots, owners = {}, {}
    for path in sorted((ROOT / SKILL / 'assets' / 'schemas').glob('*.schema.json')):
        try:
            roots[path.name.split('.')[0]] = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            continue

    def walk(node, root):
        if isinstance(node, list):
            for item in node:
                walk(item, root)
        elif isinstance(node, dict):
            if isinstance(node.get('properties'), dict):
                for name, sub in node['properties'].items():
                    owners.setdefault(name, []).append((root, sub))
            for value in node.values():
                walk(value, root)

    for root in roots.values():
        walk(root, root)
    return roots, owners


def variants(node, root: dict, depth: int = 0):
    """Ein Unterschema mit allem, was für seine Felder gilt: Verweis, Alternativen, Elemente einer Liste."""
    try:
        node = resolve(node, root)
    except (KeyError, TypeError):
        return
    if not isinstance(node, dict) or depth > 8:
        return
    yield node
    for key in ('allOf', 'anyOf', 'oneOf'):
        for sub in node.get(key) or []:
            yield from variants(sub, root, depth + 1)
    for key in ('then', 'else', 'items'):
        if isinstance(node.get(key), dict):
            yield from variants(node[key], root, depth + 1)


def field_resolves(nodes: list, segments: list[str], root: dict) -> bool:
    for segment in segments:
        found = []
        for node in nodes:
            for v in variants(node, root):
                props = v.get('properties') if isinstance(v.get('properties'), dict) else {}
                extra = v.get('additionalProperties')
                if segment in props:
                    found.append(props[segment])
                elif isinstance(extra, dict):
                    found.append(extra)
                elif extra is True or v.get('patternProperties') or (v.get('type') == 'object' and not props
                                                                     and extra is None):
                    return True  # freies Objekt: jeder Name ist erlaubt
        if not found:
            return False
        nodes = found
    return True


def tool_tables() -> tuple[dict[str, dict[str, set[str]]], dict[str, set[str]]]:
    """Befehle mit ihren Schaltern (build_mappe, pin_queue, check_repo) und Schalter der übrigen Werkzeuge."""
    import argparse
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_mappe
    import pin_queue
    import send_mail

    def table(parser) -> dict[str, set[str]]:
        subs = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
        return {name: {o for a in sub._actions for o in a.option_strings} for name, sub in subs.items()}

    commands = {'build_mappe': table(build_mappe.build_parser()), 'pin_queue': table(pin_queue.build_parser()),
                'send_mail': table(send_mail.build_parser()),
                'check_repo': {name: {'--quiet'} for name in (*CHECKS, 'all', 'hook', 'rules')}}
    flags = {tool: set(re.findall(r"'(--[a-z][a-z-]*)'", (ROOT / 'tools' / f'{tool}.py').read_text(encoding='utf-8')))
             for tool in ('fresh_clone_test', 'serve_template', 'devicon_symbols')}
    return commands, flags


def limit_leaves(node, prefix: str = '') -> dict[str, object]:
    """limits.json als flache Tabelle: Pfad -> Zahl oder Liste von Zahlen (auch jeder Zwischenknoten)."""
    out: dict[str, object] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if prefix or key != 'description':
                out.update(limit_leaves(value, f'{prefix}.{key}' if prefix else key))
        if prefix:
            out[prefix] = node
    else:
        out[prefix] = node
    return out


def numbers_of(value) -> list[int] | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [value]
    if isinstance(value, list) and all(isinstance(v, (int, float)) for v in value):
        return list(value)
    return None


def as_number(text: str) -> int:
    return NUMBER_WORDS[text.lower()] if text.lower() in NUMBER_WORDS else int(text)


def check_docs(files: list[str] | None = None, only: str | None = None) -> list[str]:
    """Doku gegen den Rest des Repositorys: Regel-Ids, Pfade, Befehle, Schemafelder, Symbol-Ids, Zahlen und
    veraltete Formulierungen. Mit only nur die Befunde dieser einen Datei."""
    files = git_files() if files is None else files
    texts = {rel: text for rel in files if rel not in DOC_EXEMPT and (text := read_text(rel)) is not None}
    docs = {rel: text for rel, text in texts.items() if rel.endswith('.md')}
    out: list[str] = []
    names = {rel.rsplit('/', 1)[-1] for rel in files} | LOCAL_NAMES

    # 1. Regeln: jede Id genau einmal definiert, jeder Verweis trifft sein Zuhause
    index, out = rule_index(docs)
    for rel, text in docs.items():
        for m in RULE_REF.finditer(text):
            rid, where, line = m.group(1), m.group(2), line_of(text, m.start())
            if rid not in index:
                out.append(f'docs: {rel}:{line}: Verweis auf Regel „{rid}“, die nirgends definiert ist '
                           '(Liste: check_repo.py rules)')
            elif where and path_target(where) != index[rid][0]:
                out.append(f'docs: {rel}:{line}: Regel „{rid}“ steht in {index[rid][0]}, nicht in {where}')

    # 2. Grundlagen für die übrigen Prüfungen
    try:
        limits = limit_leaves(json.loads((ROOT / LIMITS).read_text(encoding='utf-8')))
    except (OSError, ValueError) as e:
        return out + [f'docs: {LIMITS}: nicht lesbar ({e})']
    icons_text = read_text(ICONS) or ''
    symbols = re.findall(r'<symbol id="([^"]+)"', icons_text)
    counts = {prefix: sum(1 for s in symbols if s.startswith(prefix + '-')) for prefix in ('i', 'dv', 'si')}
    logos = counts['dv'] + counts['si']
    roots, owners = schema_owners()
    try:
        commands, tool_flags = tool_tables()
        import build_mappe
        sections = len(build_mappe.SECTIONS)
    except Exception as e:  # ein Werkzeug lässt sich nicht laden: das ist selbst ein Befund
        return out + [f'docs: Werkzeuge nicht lesbar ({type(e).__name__}: {e})']
    css_vars = {v for path in sorted((ROOT / SKILL / 'assets' / 'mappe').glob('*.css'))
                for v in re.findall(r'(--[a-z][a-z0-9-]*)\s*:', path.read_text(encoding='utf-8'))}
    all_flags = {f for table in commands.values() for flags in table.values() for f in flags} \
        | {f for flags in tool_flags.values() for f in flags} | EXTERNAL_FLAGS | css_vars
    viewports = {tuple(v) for v in (limits.get('qa.viewports') or {}).values()}
    # Zahl neben einem bekannten Stichwort -> erlaubte Werte (aus limits.json oder berechnet)
    keywords = (
        (r'\b(\d+) Logo-Symbole\b', {logos}, 'Logo-Symbole in icons.svg'),
        (r'\b(\d+) Quelldateien\b', {logos}, 'Logo-Symbole in icons.svg'),
        (r'\b(\d+) Devicon\b', {counts['dv']}, 'Devicon-Symbole in icons.svg'),
        (r'\b(\d+) Simple Icons\b', {counts['si']}, 'Simple-Icons-Symbole in icons.svg'),
        (r'\b(\d+) Linien-Icons\b', {counts['i']}, 'Linien-Icons in icons.svg'),
        (r'\b(\d+) Symbole\b', {len(symbols), logos, counts['i']}, 'Symbole in icons.svg'),
        (r'(?:älter als|höchstens) (\d+) Tage\b', {limits.get('letter.max_age_days')}, 'limits:letter.max_age_days'),
        (r'\b(\d+|' + '|'.join(NUMBER_WORDS) + r') Abschnitte\b', {sections}, 'SECTIONS in build_mappe.py'),
    )

    for rel, text in docs.items():
        prose, code = split_fences(text)

        def finding(pos: int, message: str, source: str = prose) -> None:
            out.append(f'docs: {rel}:{line_of(source, pos)}: {message}')

        # 3. Pfade, Dateinamen, Schemafelder, Symbol-Ids, Schlüssel aus limits.json: nur in `…` im Fließtext
        for span in SPAN.finditer(prose):
            if prose[max(span.start() - 6, 0):span.start()] == 'Regel ':
                continue  # Regel-Id, oben geprüft
            tokens = span.group(1).split()
            for raw in tokens:
                token = raw.strip('.,;()"„“')
                if not token or re.search(r'[<>…$=~]', token) or 'mustermann' in token:
                    continue
                if token.startswith('limits:'):
                    if token[7:] not in limits:
                        finding(span.start(), f'„{token}“ gibt es in {LIMITS} nicht')
                elif token.startswith(PATH_ROOTS) and not PROFILE_ASSETS.match(token):
                    if path_target(token) is None:
                        finding(span.start(), f'Pfad „{token}“ gibt es nicht')
                elif '/' not in token and FILE_NAME.fullmatch(token):
                    if token not in names:
                        finding(span.start(), f'Datei „{token}“ gibt es nicht')
                elif ICON_ID.fullmatch(token):
                    if token not in symbols:
                        finding(span.start(), f'Symbol „{token}“ fehlt in {ICONS}')
                elif (m := FIELD.fullmatch(token)) and ('.' in m.group(2) or m.group(1)):
                    segments = [re.sub(r'\[[^\]]*\]', '', s) for s in m.group(2).split('.')]
                    if m.group(1):
                        ok = field_resolves([roots[m.group(1)]], segments, roots[m.group(1)])
                    elif segments[0] in owners:
                        ok = any(field_resolves([sub], segments[1:], root) for root, sub in owners[segments[0]])
                    else:
                        ok = True  # kein Feld eines Schemas
                    if not ok:
                        finding(span.start(), f'Schemafeld „{token}“ gibt es in assets/schemas/ nicht')
            # Schalter ohne Werkzeugnamen: `application --qa`, `--pdf`
            flags = FLAG.findall(span.group(1))
            if flags and not TOOL_CALL.search(span.group(1)):
                first = tokens[0]
                known = commands['build_mappe'].get(first) or commands['pin_queue'].get(first)
                allowed = (known | {'--help'}) if known is not None else all_flags
                for flag in flags:
                    if flag not in allowed:
                        finding(span.start(), f'Schalter „{flag}“ gibt es nicht' + (f' für „{first}“' if known else ''))

        # 4. Befehle der Werkzeuge, in `…` und in Codeblöcken
        for m in TOOL_CALL.finditer(code):
            tool, rest = m.group(1), m.group(2)
            flags = FLAG.findall(rest)
            first = re.match(r'\s*([a-z][a-z-]*)(?![\w./-])', rest)
            if tool in commands:
                table = commands[tool]
                if first and first.group(1) not in table:
                    finding(m.start(), f'{tool}.py kennt den Befehl „{first.group(1)}“ nicht', text)
                    continue
                allowed = (table[first.group(1)] if first else {f for fl in table.values() for f in fl}) | {'--help'}
            else:
                allowed = tool_flags[tool] | {'--help'}
            for flag in flags:
                if flag not in allowed:
                    finding(m.start(), f'{tool}.py' + (f' {first.group(1)}' if first and tool in commands else '')
                            + f' kennt den Schalter „{flag}“ nicht', text)

        # 5. Zahlen: direkt vor (`limits:…`) und neben bekannten Stichwörtern
        for m in re.finditer(r'\(`limits:([a-z0-9_.]+)`\)', text):
            want = numbers_of(limits.get(m.group(1)))
            before = text[max(text.rfind('\n', 0, m.start()) + 1, m.start() - 45):m.start()]
            groups = re.findall(r'\d+(?:\s*(?:[–×-]|bis|und)\s*\d+)*', before)
            if want is None or not groups:
                continue
            have = [int(n) for n in re.findall(r'\d+', groups[-1])]
            if have != want:
                finding(m.start(), f'Zahl {groups[-1]} passt nicht zu limits:{m.group(1)} = '
                        f'{" / ".join(str(n) for n in want)}', text)
        for pattern, allowed, label in keywords:
            for m in re.finditer(pattern, text):
                if as_number(m.group(1)) not in allowed:
                    finding(m.start(), f'„{m.group(0)}“ passt nicht zu {label} '
                            f'({", ".join(str(n) for n in sorted(allowed))})', text)
        for m in re.finditer(r'\b(\d{3,4}) × (\d{3,4})\b(?! ?(?:px|mm))', text):
            if (int(m.group(1)), int(m.group(2))) not in viewports:
                finding(m.start(), f'Fenstergröße „{m.group(0)}“ steht nicht in limits:qa.viewports', text)

    # 6. Jedes Symbol steht in der Liste; jeder Grenzwert wird vom Build-Skript gelesen
    home = docs.get(ICON_HOME, '')
    out += [f'docs: {ICON_HOME}: Symbol „{s}“ aus {ICONS} fehlt in der Liste (Icons und Logos)'
            for s in symbols if f'`{s}`' not in home]
    try:
        listed = set(json.loads((ROOT / ICON_SOURCES).read_text(encoding='utf-8'))['symbols'])
    except (OSError, ValueError, KeyError, TypeError) as e:
        return out + [f'docs: {ICON_SOURCES}: nicht lesbar ({e})']
    logo_ids = {s for s in symbols if not s.startswith('i-')}
    out += [f'docs: {ICON_SOURCES}: Logo-Symbol „{s}“ aus {ICONS} hat keinen Eintrag (Quelldatei und Farbe)'
            for s in sorted(logo_ids - listed)]
    out += [f'docs: {ICON_SOURCES}: Eintrag „{s}“ ohne Symbol in {ICONS}' for s in sorted(listed - logo_ids)]
    used = set(re.findall(r'''limit\(['"]([a-z0-9_.]+)['"]\)''', read_text('tools/build_mappe.py') or ''))
    out += [f'docs: {LIMITS}: „{key}“ liest tools/build_mappe.py nicht (limit(…)); streichen oder verwenden'
            for key, value in limits.items() if not isinstance(value, dict)
            and not any(key == u or key.startswith(u + '.') for u in used)]

    # 7. Veraltete Formulierungen, in allen Textdateien
    for number, row in enumerate((read_text(STALE_TERMS) or '').splitlines(), 1):
        if not row.strip() or row.lstrip().startswith('#'):
            continue
        pattern, _, hint = (part.strip() for part in row.partition(' => '))
        try:
            rx = re.compile(pattern)
        except re.error as e:
            out.append(f'docs: {STALE_TERMS}:{number}: Muster ungültig ({e})')
            continue
        for rel, text in texts.items():
            masked = mask(text)
            out += [f'docs: {rel}:{line_of(masked, m.start())}: veraltete Formulierung „{m.group(0)}“'
                    + (f' ({hint})' if hint else '') for m in rx.finditer(masked)]
    out = list(dict.fromkeys(out))
    return [f for f in out if f.startswith(f'docs: {only}:')] if only else out


# --------------------------------------------------------------------------- Befehle

CHECKS = {'privacy': check_privacy, 'stray': check_stray, 'schemas': check_schemas, 'template': check_template,
          'pins': check_pins, 'docs': check_docs}
# Dateien, deren Inhalt die Doku zitiert: Nach einer Änderung dort prüft der Hook die ganze Doku.
DOC_INPUTS = (LIMITS, ICONS, ICON_SOURCES, STALE_TERMS, f'{SKILL}/assets/schemas/', 'tools/')


def cmd_rules() -> int:
    """Liste aller Regeln mit ihrem Zuhause."""
    files = git_files()
    index, problems = rule_index({rel: text for rel in files if rel.endswith('.md') and rel not in DOC_EXEMPT
                                  and (text := read_text(rel)) is not None})
    width = max((len(rid) for rid in index), default=0)
    for rid, (rel, line) in sorted(index.items(), key=lambda item: (item[1][0], item[1][1])):
        print(f'{rid:<{width}}  {rel}:{line}')
    print('\n'.join(problems) if problems else f'{len(index)} Regeln')
    return 1 if problems else 0


def cmd_hook() -> int:
    try:
        payload = json.load(sys.stdin)
        target = Path((payload.get('tool_input') or {}).get('file_path') or '').resolve()
        rel = target.relative_to(ROOT).as_posix()
    except (ValueError, AttributeError, OSError):
        return 0  # kein Hook-JSON oder Datei außerhalb des Repositorys
    if rel in ('', '.') or rel.startswith('.git/') or not target.exists():
        return 0
    if subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--', rel], capture_output=True).returncode == 0:
        return 0  # gitignoriert (profile/<name>/, .tmp/): hier dürfen persönliche Daten stehen
    findings = check_privacy([rel]) + check_stray([rel])
    if rel.endswith('.json'):
        schema_dir = f'{SKILL}/assets/schemas/'
        findings += check_schemas(git_files() if rel.startswith(schema_dir) else [rel])
    if rel.startswith(TEMPLATE_SOURCES):
        findings += check_template()
    if rel.startswith(PIN_SOURCES):
        findings += check_pins([rel])
    if rel.endswith('.md') and rel not in DOC_EXEMPT:
        findings += check_docs(only=rel)
    elif rel.startswith(DOC_INPUTS):
        findings += check_docs()
    if findings:
        print('tools/check_repo.py (Hook nach Edit/Write):\n' + '\n'.join(findings)
              + '\nBitte beheben: persönliche Daten nur unter profile/<name>/ und .tmp/, Dateien nur an den '
                'erlaubten Orten, Master-Vorlage nur über ihre Quellen und mit Anfrage in der Warteschlange, '
                'Doku passend zu Dateien, Befehlen, Schemas und limits.json (references/qa-and-export.md, '
                'Repository-Prüfung).', file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = '--quiet' in args
    args = [a for a in args if a != '--quiet']
    if args == ['hook']:
        return cmd_hook()
    if args == ['rules']:
        return cmd_rules()
    names = list(CHECKS) if args == ['all'] else args
    if not names or any(name not in CHECKS for name in names):
        print(__doc__)
        return 1
    files = git_files()
    # privacy und pins sehen selbst nach, was Git aufnehmen würde (Staging-Diff, gelöschte Dateien)
    findings = [f for name in names for f in CHECKS[name](None if name in ('privacy', 'pins') else files)]
    label = ' '.join(args)
    if findings:
        print('\n'.join(findings))
        print(f'check_repo {label}: {len(findings)} Befund(e)')
        return 1
    if not quiet:
        note = '' if 'privacy' not in names or load_needles() else \
            ' (kein Profil unter profile/: keine Suchmuster für persönliche Daten)'
        print(f'check_repo {label}: ok, {len(files)} Dateien{note}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
