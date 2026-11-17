#!/usr/bin/env python3
"""Firmenrecherche für job_information/firma.md (Regel company.research in references/job-search.md).

Nur Python-Standardbibliothek. Holt öffentliche Seiten der Firma als Text und prüft, dass jeder Beleg in
firma.md wörtlich in einer gelesenen Quelle steht. Nicht für die Jobsuche der BA (Regel hard.source in
CLAUDE.md): Stellen kommen nur aus dem Browser des Harness.

Befehle:
  fetch <stellen-ordner> <url>…
      Lädt jede Seite (öffentlich, ohne Anmeldung, ohne Formulare) und legt sie als Text unter
      .tmp/research/<ordnername>/NN.txt ab, erste Zeile „URL: …“. mailto-Adressen bleiben als [mailto:…] sichtbar.
  verify <stellen-ordner>…
      Prüft jede Zeile „Beleg: „…““ in job_information/firma.md gegen die Texte unter .tmp/research/<ordnername>/
      und die übrigen Dateien in job_information/ (Anzeige, Portalseite). Exit 2, wenn ein Beleg fehlt.
"""
import argparse, html.parser, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
BLOCK = {'p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'tr', 'section', 'article', 'td', 'dd', 'dt'}


class Text(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.skip += 1
        if tag in BLOCK:
            self.out.append('\n')
        if tag == 'a':
            href = dict(attrs).get('href') or ''
            if href.startswith('mailto:'):
                self.out.append(f' [mailto:{href[7:].split("?")[0]}] ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def research_dir(folder: pathlib.Path) -> pathlib.Path:
    return ROOT / '.tmp' / 'research' / folder.resolve().name


def norm(s: str) -> str:
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('**', '')).strip()


def cmd_fetch(a) -> int:
    folder = pathlib.Path(a.folder)
    out = research_dir(folder); out.mkdir(parents=True, exist_ok=True)
    n = len(list(out.glob('*.txt')))
    for url in a.urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'de-DE,de;q=0.9'})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode(r.headers.get_content_charset() or 'utf-8', 'replace')
        except Exception as e:
            print(f'FEHLER {url}: {e}'); continue
        p = Text(); p.feed(raw)
        text = re.sub(r'[ \t]+', ' ', re.sub(r'\n\s*\n+', '\n', ''.join(p.out))).strip()
        n += 1
        dst = out / f'{n:02d}.txt'
        dst.write_text(f'URL: {url}\n{text}\n', encoding='utf-8')
        print(f'{dst.relative_to(ROOT)} ({len(text)} Zeichen)')
    return 0


def cmd_verify(a) -> int:
    bad_total = 0
    for f in a.folders:
        folder = pathlib.Path(f)
        firma = folder / 'job_information' / 'firma.md'
        if not firma.is_file():
            print(f'FEHLT {firma}'); bad_total += 1; continue
        sources = [p for p in (folder / 'job_information').glob('*.md') if p.name != 'firma.md']
        sources += list(research_dir(folder).glob('*.txt'))
        corpus = norm(' '.join(p.read_text(encoding='utf-8', errors='replace') for p in sources))
        quotes = re.findall(r'Beleg: „([^“]+)“', firma.read_text(encoding='utf-8'))
        bad = [q for q in quotes if norm(q) not in corpus]
        bad_total += len(bad)
        print(f'{"ok    " if not bad else "FEHLER"} {folder.name}: {len(quotes)} Belege, {len(bad)} nicht gefunden')
        for q in bad:
            print(f'    „{q[:120]}“')
    return 2 if bad_total else 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('fetch'); s.add_argument('folder'); s.add_argument('urls', nargs='+'); s.set_defaults(fn=cmd_fetch)
    s = sp.add_parser('verify'); s.add_argument('folders', nargs='+'); s.set_defaults(fn=cmd_verify)
    return ap


if __name__ == '__main__':
    a = build_parser().parse_args()
    sys.exit(a.fn(a))
