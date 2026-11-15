#!/usr/bin/env python3
"""Wandelt lokal gespeicherte Logo-SVGs in <symbol>-Elemente in Markenfarbe für die Mappen-Vorlage.

Nur Python-Standardbibliothek, keine Daten, kein Netzzugriff. Quellen, Versionen, Lizenzen und der
Weg, ein neues Logo aufzunehmen: .agents/skills/bewerbungshelfer/assets/icons/README.md

Aufruf:  python3 tools/devicon_symbols.py <ordner-mit-svgs> [--prefix dv|si] [--only name1,name2]
         python3 tools/devicon_symbols.py <ordner> [--prefix dv|si] [--only …] --urls

- Devicon (MIT):       --prefix dv  ->  id dv-<dateiname>
- Simple Icons (CC0):  --prefix si  ->  id si-<dateiname>

Welche Quelldatei und welche Farbe ein Symbol bekommt, steht in assets/icons/sources.json (Schalter --sources
für eine andere Datei). Ein Symbol ohne Eintrag dort wird abgelehnt. fill je Symbol:
- "file": Die Füllfarben der Datei bleiben (mehrfarbiges Original oder einfarbige Datei mit eigener Farbe).
  Jede Form braucht dann eine Füllfarbe, an sich oder an einer Gruppe darüber; Verläufe gehen nicht.
- "#rrggbb": Alle Füllfarben der Datei entfallen, das Logo bekommt genau diese Farbe (Gruppe mit fill).
  Für Dateien ohne Farbe (Simple Icons) und für Logos, deren Original Verläufe hat.
In beiden Fällen werden weiße Füllungen zu Aussparungen (style fill: var(--dv-cutout, #fff)), damit Details
auf dem hellen Chip erhalten bleiben. <title>, <desc>, <defs>, class und id werden entfernt, Leerraum gekürzt.

--urls gibt nur die curl-Befehle aus, mit denen die Quelldateien aus sources.json nach <ordner> geladen werden
(jsDelivr, feste Versionen), und wandelt nichts um.

Prüfungen (jede Datei einzeln; ein Fehler nennt die Datei und bricht nur diese Datei ab, Exit-Code 1):
- gültiges XML ohne DOCTYPE/ENTITY, Wurzel <svg> im SVG-Namensraum, viewBox mit vier Zahlen (Breite, Höhe > 0)
- Dateiname (ohne .svg) nur a-z, 0-9 und Bindestrich, weil er Teil der Symbol-Id wird
- nur diese Elemente: svg, g, path, circle, ellipse, rect, polygon, polyline, line, title, desc, defs;
  nie script, style, foreignObject, use, image, a, Animationen oder Filter
- nur bekannte Attribute; keine Ereignis-Attribute, keine Verweise (href/xlink:href), kein url(…), kein data:/http(s):
- style-Attribut nur mit fill, fill-rule, clip-rule, opacity, fill-opacity; Strichfarben (stroke) sind nicht
  unterstützt (stroke nur none oder currentColor)
- das fertige Symbol wird nochmals als XML gelesen und gegen dieselben Regeln geprüft

Ausgabe: je gültiger Datei eine Zeile <symbol id="…" viewBox="…">…</symbol> auf stdout, Fehler auf stderr.
Die Zeilen kommen nach assets/mappe/icons.svg (alphabetisch nach id, eine Zeile pro Symbol), danach die
Tabelle in references/template.md und assets/icons/README.md ergänzen und die Master-Vorlage neu bauen
(build_mappe.py master)."""
import argparse
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'
XML_NS = 'http://www.w3.org/XML/1998/namespace'
XLINK_NS = 'http://www.w3.org/1999/xlink'

WHITE = {'#fff', '#ffffff', 'white'}
CUTOUT = 'var(--dv-cutout,#fff)'
SOURCES = pathlib.Path(__file__).resolve().parents[1] / '.agents/skills/bewerbungshelfer/assets/icons/sources.json'
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')
CDN = 'https://cdn.jsdelivr.net/npm'

SHAPES = {'g', 'path', 'circle', 'ellipse', 'rect', 'polygon', 'polyline', 'line'}
ALLOWED_ELEMENTS = SHAPES | {'svg', 'title', 'desc', 'defs'}
FORBIDDEN_ELEMENTS = {'script', 'style', 'foreignObject', 'use', 'image', 'a', 'iframe', 'animate',
                      'animateTransform', 'animateMotion', 'set', 'filter', 'text', 'tspan', 'switch'}
ROOT_ATTRS = {'viewBox', 'width', 'height', 'x', 'y', 'version', 'baseProfile', 'role', 'aria-hidden',
              'aria-labelledby', 'focusable', 'preserveAspectRatio', 'enable-background', 'id', 'class', 'fill',
              'style', 'fill-rule', 'clip-rule', 'space'}
SHAPE_ATTRS = {'d', 'cx', 'cy', 'r', 'rx', 'ry', 'x', 'y', 'width', 'height', 'points', 'x1', 'y1', 'x2', 'y2',
               'transform', 'fill', 'fill-rule', 'clip-rule', 'fill-opacity', 'opacity', 'style', 'class', 'id',
               'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit'}
STYLE_PROPS = {'fill', 'fill-rule', 'clip-rule', 'opacity', 'fill-opacity'}
COLOR = re.compile(r'^(#[0-9a-fA-F]{3,8}|(rgb|rgba|hsl|hsla)\([0-9 .,%/-]+\)|[a-zA-Z]+)$')
ID_PART = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
NUMBER = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'


class SvgError(Exception):
    pass


def local(name: str) -> str:
    """Lokaler Name eines ElementTree-Tags oder -Attributs; fremde Namensräume sind ein Fehler."""
    if not name.startswith('{'):
        return name
    ns, _, rest = name[1:].partition('}')
    if ns in (SVG_NS, XML_NS, XLINK_NS):
        return rest
    raise SvgError(f'unbekannter Namensraum {ns}')


def check_value(attr: str, value: str) -> None:
    low = value.strip().lower()
    if 'url(' in low or re.search(r'(^|[\s,(])(data|https?|javascript|file):', low) or '&' in value:
        raise SvgError(f'Attribut {attr} enthält einen Verweis oder eine Referenz („{value[:40]}“); '
                       'externe und interne Referenzen (url(…), data:, http:) sind nicht erlaubt')


def check_color(attr: str, value: str, *, allow_none: bool = True) -> None:
    low = value.strip()
    if low == 'none' and allow_none:
        return
    if low in ('currentColor', 'inherit', CUTOUT) or COLOR.match(low):
        return
    raise SvgError(f'Attribut {attr}="{value}" ist keine einfache Farbe')


def parse_style(value: str) -> list[tuple[str, str]]:
    decls = []
    for part in value.split(';'):
        if not part.strip():
            continue
        prop, sep, val = part.partition(':')
        prop, val = prop.strip().lower(), val.strip()
        if not sep or not prop:
            raise SvgError(f'style-Attribut nicht lesbar: „{value[:60]}“')
        if prop not in STYLE_PROPS:
            raise SvgError(f'style-Eigenschaft „{prop}“ nicht unterstützt (erlaubt: {", ".join(sorted(STYLE_PROPS))})')
        check_value(f'style/{prop}', val)
        if prop == 'fill':
            check_color('style/fill', val)
        decls.append((prop, val))
    return decls


def validate_tree(root: ET.Element, *, symbol: bool) -> None:
    """Prüft Elemente und Attribute. symbol=True: bereits umgewandelter Inhalt (ohne defs/title/desc/svg-Wurzel)."""
    if not symbol:
        if root.tag != f'{{{SVG_NS}}}svg':
            raise SvgError(f'Wurzelelement muss <svg> im Namensraum {SVG_NS} sein (gefunden: {root.tag})')

    def visit(e: ET.Element) -> None:
        name = local(e.tag)
        if name in FORBIDDEN_ELEMENTS or name not in ALLOWED_ELEMENTS or name == 'svg':
            raise SvgError(f'Element <{name}> nicht erlaubt (erlaubt: {", ".join(sorted(ALLOWED_ELEMENTS - {"svg"}))})')
        if symbol and name in ('defs', 'title', 'desc'):
            raise SvgError(f'Element <{name}> darf im Symbol nicht vorkommen')
        for raw, val in e.attrib.items():
            attr = local(raw)
            if attr == 'href' or attr.startswith('on'):
                raise SvgError(f'Attribut {attr} nicht erlaubt (keine Verweise, keine Ereignisse)')
            check_value(attr, val)
        if name in ('title', 'desc'):
            return
        if name == 'defs':
            for child in e.iter():
                if child is not e:
                    cname = local(child.tag)
                    if cname in FORBIDDEN_ELEMENTS:
                        raise SvgError(f'Element <{cname}> nicht erlaubt (auch nicht in defs)')
                    for raw, val in child.attrib.items():
                        attr = local(raw)
                        if attr == 'href' or attr.startswith('on'):
                            raise SvgError(f'Attribut {attr} nicht erlaubt (auch nicht in defs)')
                        check_value(attr, val)
            return
        if name in SHAPES:
            for raw, val in e.attrib.items():
                attr = local(raw)
                if attr not in SHAPE_ATTRS:
                    raise SvgError(f'Attribut {attr} an <{name}> nicht unterstützt')
                if attr == 'fill':
                    check_color('fill', val)
                if attr == 'stroke' and val.strip() not in ('none', 'currentColor'):
                    raise SvgError(f'stroke="{val}" nicht unterstützt (nur none oder currentColor; Strichfarben '
                                   'gehen beim Einfärben verloren): anderes Logo oder Fläche statt Strich wählen')
                if attr == 'style':
                    parse_style(val)
        if (e.text or '').strip() or any((c.tail or '').strip() for c in e):
            raise SvgError(f'Textinhalt in <{name}> nicht erlaubt')
        for child in e:
            visit(child)

    if not symbol:
        for raw, val in root.attrib.items():
            attr = local(raw)
            if attr not in ROOT_ATTRS:
                raise SvgError(f'Attribut {attr} an <svg> nicht unterstützt')
            check_value(attr, val)
        if (root.text or '').strip():
            raise SvgError('Textinhalt in <svg> nicht erlaubt')
    for child in root:
        visit(child)


def viewbox_of(root: ET.Element) -> str:
    vb = root.attrib.get('viewBox')
    if not vb:
        raise SvgError('viewBox fehlt (z. B. viewBox="0 0 128 128")')
    nums = re.findall(NUMBER, vb)
    if not re.fullmatch(rf'\s*{NUMBER}(?:[\s,]+{NUMBER}){{3}}\s*', vb):
        raise SvgError(f'viewBox „{vb}“ braucht genau vier Zahlen (min-x min-y Breite Höhe)')
    if float(nums[2]) <= 0 or float(nums[3]) <= 0:
        raise SvgError(f'viewBox „{vb}“: Breite und Höhe müssen größer als 0 sein')
    return vb


def symbol_id(prefix: str, stem: str) -> str:
    if not ID_PART.match(stem):
        raise SvgError(f'Dateiname „{stem}“ ergibt keine gültige Id: nur a-z, 0-9 und einzelne Bindestriche '
                       '(Datei umbenennen)')
    return f'{prefix}-{stem}'


def unfilled_shapes(root: ET.Element) -> int:
    """Formen ohne Füllfarbe an sich oder an einer Gruppe darüber (Attribut fill oder fill im style-Attribut)."""
    def has_fill(e: ET.Element) -> bool:
        return 'fill' in e.attrib or any(prop == 'fill' for prop, _ in parse_style(e.attrib.get('style', '')))

    def walk(e: ET.Element, inherited: bool) -> int:
        name = local(e.tag)
        if name in ('defs', 'title', 'desc'):
            return 0
        filled = inherited or has_fill(e)
        own = 1 if name in SHAPES - {'g'} and not filled else 0
        return own + sum(walk(c, filled) for c in e)

    return sum(walk(c, 'fill' in root.attrib) for c in root)


def convert(svg: str, symbol_id_: str, fill: str) -> str:
    """fill: „file“ (Farben der Datei behalten) oder „#rrggbb“ (eine Farbe für das ganze Logo)."""
    if fill != 'file' and not HEX.match(fill):
        raise SvgError(f'fill „{fill}“ in sources.json: erlaubt sind "file" oder eine Farbe "#rrggbb"')
    if re.search(r'<!(DOCTYPE|ENTITY)|<!\[CDATA\[|<\?(?!xml\b)', svg, flags=re.I):
        raise SvgError('DOCTYPE, ENTITY, CDATA und Verarbeitungsanweisungen sind nicht erlaubt')
    try:
        root = ET.fromstring(svg.lstrip('﻿').encode('utf-8'))
    except ET.ParseError as e:
        raise SvgError(f'kein gültiges XML: {e}') from e
    validate_tree(root, symbol=False)
    viewbox = viewbox_of(root)
    keep = fill == 'file'
    if keep and unfilled_shapes(root):
        raise SvgError(f'{unfilled_shapes(root)} Form(en) ohne Füllfarbe: in sources.json statt "file" eine Farbe '
                       '"#rrggbb" eintragen')

    inner = re.sub(r'<!--.*?-->', '', svg, flags=re.S)
    inner = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', inner, flags=re.S).strip()
    inner = re.sub(r'<defs>.*?</defs>', '', inner, flags=re.S)
    inner = re.sub(r'<(title|desc)>.*?</\1>', '', inner, flags=re.S)

    def fix(m):
        value = m.group(1)
        if value.lower() in WHITE:
            return f'style="fill:{CUTOUT}"'
        if value == 'none':
            return 'fill="none"'
        return m.group(0) if keep else ''

    def fix_style(m):
        kept = []
        for prop, val in parse_style(m.group(1)):
            if prop == 'fill':
                if val.lower() in WHITE:
                    kept.append(f'fill:{CUTOUT}')
                elif val == 'none':
                    kept.append('fill:none')
                elif keep:
                    kept.append(f'fill:{val}')
                continue  # sonst entfallen andere Farben: das Logo bekommt die eine Farbe aus sources.json
            kept.append(f'{prop}:{val}')
        return f'style="{";".join(kept)}"' if kept else ''

    def sub_style(m):
        new = fix_style(m)
        return f' {new}' if new else ''

    inner = re.sub(r'\sstyle="([^"]*)"', sub_style, inner)
    inner = re.sub(r'fill="([^"]+)"', fix, inner)
    inner = re.sub(r'\s(class|id)="[^"]*"', '', inner)
    inner = re.sub(r'<g\s*>', '<g>', inner)
    inner = re.sub(r'\s+', ' ', inner)
    if not keep:
        inner = f'<g fill="{fill}">{inner}</g>'

    # Ergebnis erneut prüfen (gültiges XML, keine doppelten Attribute, nur erlaubte Inhalte)
    try:
        out_root = ET.fromstring(f'<svg xmlns="{SVG_NS}">{inner}</svg>')
    except ET.ParseError as e:
        raise SvgError(f'Umwandlung ergibt kein gültiges XML (z. B. doppeltes style-Attribut): {e}') from e
    validate_tree(out_root, symbol=True)
    return f'<symbol id="{symbol_id_}" viewBox="{viewbox}">{inner}</symbol>'


def load_sources(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        data['packages'], data['symbols']
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise SystemExit(f'Fehler: {path} nicht lesbar ({type(e).__name__}: {e})')
    return data


def source_url(sources: dict, sid: str) -> str:
    """Adresse der Quelldatei eines Symbols: Paket und Version aus packages, Pfad nach dem Muster des Pakets."""
    prefix, _, name = sid.partition('-')
    pkg = sources['packages'][prefix]
    path = pkg['path'].replace('<name>', name).replace('<variant>', sources['symbols'][sid].get('variant', ''))
    return f'{CDN}/{pkg["npm"]}@{pkg["version"]}/{path}'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('src', help='Ordner mit <name>.svg')
    ap.add_argument('--prefix', default='dv', choices=('dv', 'si'))
    ap.add_argument('--only', default='', help='kommagetrennte Dateinamen ohne .svg')
    ap.add_argument('--sources', default=str(SOURCES), help='Quellen und Farben je Symbol (Standard: sources.json)')
    ap.add_argument('--urls', action='store_true', help='nur die curl-Befehle für die Quelldateien ausgeben')
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(',') if x.strip()}
    sources = load_sources(pathlib.Path(args.sources))
    if args.urls:
        for sid in sorted(sources['symbols']):
            name = sid.partition('-')[2]
            if sid.startswith(args.prefix + '-') and (not only or name in only):
                print(f'curl -fLo {args.src.rstrip("/")}/{name}.svg {source_url(sources, sid)}')
        return 0
    files = [f for f in sorted(pathlib.Path(args.src).glob('*.svg')) if not only or f.stem in only]
    errors = 0
    for missing in sorted(only - {f.stem for f in files}):
        print(f'Fehler: {args.src}/{missing}.svg nicht gefunden', file=sys.stderr)
        errors += 1
    if not files and not errors:
        print(f'Fehler: keine .svg-Dateien in {args.src}', file=sys.stderr)
        return 1
    for f in files:
        try:
            sid = symbol_id(args.prefix, f.stem)
            if sid not in sources['symbols']:
                raise SvgError(f'kein Eintrag „{sid}“ in {args.sources} (Quelldatei und fill eintragen)')
            print(convert(f.read_text(encoding='utf-8'), sid, sources['symbols'][sid].get('fill', '')))
        except (SvgError, UnicodeDecodeError, OSError) as e:
            print(f'Fehler in {f}: {e}', file=sys.stderr)
            errors += 1
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
