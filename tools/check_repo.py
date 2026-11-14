#!/usr/bin/env python3
"""Repository-Prüfungen vor dem Commit (nur Python-Standardbibliothek). Regeln: references/qa-and-export.md.

Befehle:
  privacy   Persönliche Daten in Dateien, die Git aufnimmt (getrackt oder neu und nicht ignoriert), in ihren
            Pfaden und im Staging-Diff. Die Suchmuster entstehen aus jedem Profil unter profile/ (Name, Telefon,
            E-Mail, eigene Domain, Straße, PLZ mit Ort, Geburtsdatum, Geburtsort) und aus der optionalen Datei
            profile/privacy-needles.txt (ein Suchtext pro Zeile). Meldet Datei, Zeile und Art, nie den Wert.
  stray     Dateien außerhalb der Konventionen: unbekannter Ort, leere Datei, Reste wie *.orig, *.bak, EOF.
  schemas   Alle JSON-Dateien lesbar; Schemas in sich stimmig; Vorlagen passen in Feldern und Typen zum Schema.
  all       privacy, stray und schemas.
  hook      Für den Claude-Code-Hook PostToolUse (Edit|Write): liest das Hook-JSON von stdin und prüft nur die
            geänderte Datei. Exit 2 mit Meldung auf stderr bei Befund, sonst still.

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
    f'{SKILL}/assets/fonts/*.woff2', f'{SKILL}/assets/fonts/OFL.txt', f'{SKILL}/assets/fonts/README.md',
    f'{SKILL}/assets/icons/*.md',
    f'{SKILL}/assets/schemas/*.schema.json',
    f'{SKILL}/assets/templates/*.json', f'{SKILL}/assets/templates/*.md',
    f'{SKILL}/references/*.md',
    '.claude/agents/*.md', '.claude/settings.json', '.claude/skills/bewerbungshelfer',
    'profile/README.md', 'profile/import/.gitkeep', 'profile/assets/.gitkeep',
    'tools/*.py', 'tools/hooks/pre-commit',
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


# --------------------------------------------------------------------------- Befehle

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
    if findings:
        print('tools/check_repo.py (Hook nach Edit/Write):\n' + '\n'.join(findings)
              + '\nBitte beheben: persönliche Daten nur unter profile/<name>/ und .tmp/, Dateien nur an den '
                'erlaubten Orten (references/qa-and-export.md, Repository-Prüfung).', file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = '--quiet' in args
    args = [a for a in args if a != '--quiet']
    checks = {'privacy': [check_privacy], 'stray': [check_stray], 'schemas': [check_schemas],
              'all': [check_privacy, check_stray, check_schemas]}
    if args == ['hook']:
        return cmd_hook()
    if len(args) != 1 or args[0] not in checks:
        print(__doc__)
        return 1
    files = git_files()
    findings = [f for check in checks[args[0]] for f in check(files if check is not check_privacy else None)]
    if findings:
        print('\n'.join(findings))
        print(f'check_repo {args[0]}: {len(findings)} Befund(e)')
        return 1
    if not quiet:
        note = '' if args[0] == 'stray' or args[0] == 'schemas' or load_needles() else \
            ' (kein Profil unter profile/: keine Suchmuster für persönliche Daten)'
        print(f'check_repo {args[0]}: ok, {len(files)} Dateien{note}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
