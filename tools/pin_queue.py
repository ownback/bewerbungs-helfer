#!/usr/bin/env python3
"""Warteschlange für Änderungen an den Quellen der Vorlage: ein Schreiber zur Zeit (nur Standardbibliothek).

Jede Änderung unter .agents/skills/bewerbungshelfer/assets/mappe/ beginnt als Anfrage, egal ob sie aus einem
Tencil-Pin oder aus dem Gespräch kommt. Regeln und Ablauf: references/tencil.md.

  .tmp/pins/<zeit>-<id>.md       offene Anfrage (status: open oder in_progress)
  .tmp/pins/done/<zeit>-<id>.md  erledigte Anfrage mit Ergebnis und Prüfsummen der geänderten Quellen
  .tmp/locks/template.lock       wer gerade Editor ist (JSON); Zugriffe darauf laufen unter flock

Befehle:
  enqueue --text "…" | --file <datei> [--context "…"] [--origin …] [--part …] [--id …] [--from …]
      Anfrage anlegen. --context ist die Kontextzeile des Pins; „Aussehen …“ und „Inhalt …“ daraus werden zu
      part und origin, wenn die Schalter fehlen. Gibt Kennung, Pfad und den Stand der Sperre aus.
  next --holder <name>
      Editor werden bzw. bleiben und die älteste offene Anfrage holen. Exit 0: Anfrage ausgegeben (dieselbe
      erneut, solange sie nicht mit done abgeschlossen ist; das hält die Sperre frisch). Exit 2: Warteschlange
      leer, Sperre freigegeben. Exit 3: ein anderer Editor hält die Sperre; nicht bearbeiten.
  done <kennung> --holder <name> --result "…"
      Anfrage abschließen: prüft das Repository (tools/check_repo.py all), hält die Prüfsummen der geänderten
      Quellen fest und verschiebt die Anfrage nach done/. Gibt die Sperre frei, wenn nichts mehr offen ist.
  status
      Sperre, offene Anfragen und geänderte Quellen ohne Anfrage.

Exit-Codes: 0 ok, 1 Fehler, 2 Warteschlange leer (next), 3 Sperre belegt (next).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / '.tmp' / 'pins'
DONE = PINS / 'done'
LOCK = ROOT / '.tmp' / 'locks' / 'template.lock'
SOURCES = '.agents/skills/bewerbungshelfer/assets/mappe'  # dieser Ordner gehört der Warteschlange
STALE_MINUTES = 30   # so lange gilt eine Sperre ohne Lebenszeichen (next oder done) des Editors
HEAD_FIELDS = ('id', 'created', 'status', 'holder', 'started', 'from', 'origin', 'part', 'context', 'done_at')
FILE_LINE = re.compile(r'^- ([0-9a-f]{64}|deleted)  (\S.*)$', re.M)


def now() -> dt.datetime:
    return dt.datetime.now().replace(microsecond=0)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------- Sperre

@contextmanager
def mutex():
    """Exklusiver Zugriff auf Sperrdatei und Warteschlange (flock wie beim Ledger in build_mappe.py)."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    PINS.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'a+', encoding='utf-8') as fh:
        try:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX)
        except ImportError:  # Windows: ohne Sperre
            pass
        yield fh


def read_lock(fh) -> dict:
    fh.seek(0)
    try:
        data = json.loads(fh.read() or '{}')
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def write_lock(fh, data: dict) -> None:
    fh.seek(0)
    fh.truncate()
    if data:
        fh.write(json.dumps(data, ensure_ascii=False) + '\n')
    fh.flush()


def stale(lock: dict) -> bool:
    try:
        seen = dt.datetime.fromisoformat(lock.get('seen') or '')
    except ValueError:
        return True
    return now() - seen > dt.timedelta(minutes=STALE_MINUTES)


def editor(lock: dict) -> str:
    """Name des Editors, der die Sperre gerade wirksam hält, sonst ''."""
    return lock.get('holder', '') if lock.get('holder') and not stale(lock) else ''


def lock_line(lock: dict) -> str:
    if not lock.get('holder'):
        return 'Sperre: frei'
    if stale(lock):
        return (f'Sperre: frei (verwaist: {lock["holder"]}, letztes Lebenszeichen {lock.get("seen", "?")}, '
                f'älter als {STALE_MINUTES} Minuten)')
    return f'Sperre: belegt von {lock["holder"]} seit {lock.get("since", "?")}, letztes Lebenszeichen {lock.get("seen", "?")}'


# --------------------------------------------------------------------------- Anfragen

def parse(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    head: dict[str, str] = {}
    body = text
    m = re.match(r'---\n(.*?)\n---\n?', text, re.S)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            key, sep, value = line.partition(':')
            if sep:
                head[key.strip()] = value.strip()
    return {'path': path, 'head': head, 'body': body.strip('\n')}


def save(req: dict, path: Path | None = None) -> Path:
    head = req['head']
    keys = [k for k in HEAD_FIELDS if head.get(k)] + sorted(k for k in head if k not in HEAD_FIELDS and head[k])
    text = '---\n' + ''.join(f'{k}: {head[k]}\n' for k in keys) + '---\n\n' + req['body'].strip('\n') + '\n'
    target = path or req['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + '.part')
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, target)
    if path and path != req['path'] and req['path'].exists():
        req['path'].unlink()
    req['path'] = target
    return target


def open_requests() -> list[dict]:
    """Offene Anfragen (open, in_progress), älteste zuerst (nach created, bei Gleichstand nach Dateiname)."""
    found = [parse(p) for p in PINS.glob('*.md')] if PINS.is_dir() else []
    return sorted(found, key=lambda r: (r['head'].get('created', ''), r['path'].name))


def done_requests() -> list[dict]:
    return [parse(p) for p in sorted(DONE.glob('*.md'))] if DONE.is_dir() else []


def one_line(text: str, width: int = 90) -> str:
    flat = ' '.join(text.split())
    return flat if len(flat) <= width else flat[:width - 1] + '…'


# --------------------------------------------------------------------------- Quellen der Vorlage

def changed_sources() -> dict[str, str]:
    """Dateien unter SOURCES, die vom letzten Commit abweichen (geändert, neu, gelöscht): Pfad -> SHA-256."""
    try:
        out = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain', '-z', '--untracked-files=all', '--',
                              SOURCES], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    fields, found, i = out.split('\0'), {}, 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        code, names = entry[:2], [entry[3:]]
        if 'R' in code or 'C' in code:  # Umbenennung: der alte Name folgt als eigenes Feld
            names.append(fields[i])
            i += 1
        for name in names:
            path = ROOT / name
            found[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else 'deleted'
    return found


def uncovered(files: list[str] | None = None) -> list[str]:
    """Geänderte Quellen, zu denen es keine Anfrage gibt. Gedeckt ist eine Änderung, solange eine Anfrage offen
    ist, oder wenn eine erledigte Anfrage genau diesen Stand der Datei festgehalten hat."""
    changed = changed_sources()
    if files is not None:
        changed = {name: digest for name, digest in changed.items() if name in files}
    if not changed or open_requests():
        return []
    recorded = {(name, digest) for req in done_requests() for digest, name in FILE_LINE.findall(req['body'])}
    return sorted(name for name, digest in changed.items() if (name, digest) not in recorded)


# --------------------------------------------------------------------------- Befehle

def cmd_enqueue(args) -> int:
    if bool(args.text) == bool(args.file):
        print('Fehler: genau eines von --text und --file angeben.', file=sys.stderr)
        return 1
    text = args.text or Path(args.file).read_text(encoding='utf-8')
    if not text.strip():
        print('Fehler: Die Anfrage hat keinen Text.', file=sys.stderr)
        return 1
    context = ' '.join((args.context or '').split())
    part = args.part or (m.group(1) if (m := re.search(r'Aussehen (\S+)', context)) else '')
    origin = args.origin or (m.group(1).strip() if (m := re.search(r'Inhalt ([^\]]+)', context)) else '')
    stamp = dt.datetime.now()  # mit Mikrosekunden: die Reihenfolge der Anfragen folgt dem Eingang
    suffix = re.sub(r'[^a-z0-9]+', '-', (args.id or '').lower()).strip('-') or os.urandom(2).hex()
    with mutex() as fh:
        ident = f'{stamp:%Y%m%d-%H%M%S}-{suffix}'
        while (PINS / f'{ident}.md').exists() or (DONE / f'{ident}.md').exists():
            ident = f'{stamp:%Y%m%d-%H%M%S}-{suffix}-{os.urandom(1).hex()}'
        req = {'path': PINS / f'{ident}.md', 'body': text.strip('\n'),
               'head': {'id': ident, 'created': stamp.isoformat(), 'status': 'open', 'from': args.sender or '',
                        'origin': origin, 'part': part, 'context': context}}
        save(req)
        lock = read_lock(fh)
        ahead = len(open_requests()) - 1
    print(f'Anfrage: {ident}')
    print(f'Datei: {rel(req["path"])}')
    print(f'Davor in der Warteschlange: {ahead}')
    print(lock_line(lock))
    return 0


def cmd_next(args) -> int:
    with mutex() as fh:
        lock = read_lock(fh)
        other = editor(lock)
        if other and other != args.holder:
            print(lock_line(lock))
            print(f'Offene Anfragen: {len(open_requests())}. Nicht bearbeiten: Der Editor {other} arbeitet sie der '
                  'Reihe nach ab.')
            return 3
        requests = open_requests()
        if not requests:
            write_lock(fh, {})
            print('Warteschlange leer. Sperre: frei')
            return 2
        mine = [r for r in requests if r['head'].get('status') == 'in_progress' and r['head'].get('holder') == args.holder]
        req = (mine or requests)[0]
        stamp = now().isoformat()
        if not mine:
            req['head'].update(status='in_progress', holder=args.holder, started=stamp)
            save(req)
        since = lock.get('since') if lock.get('holder') == args.holder and not stale(lock) else stamp
        write_lock(fh, {'holder': args.holder, 'since': since, 'seen': stamp, 'request': req['head'].get('id', '')})
        waiting = len(requests) - 1
    print(f'Anfrage: {req["head"].get("id", req["path"].stem)}')
    print(f'Datei: {rel(req["path"])}')
    print(f'Danach noch offen: {waiting}')
    for key, label in (('context', 'Kontext'), ('part', 'Aussehen (data-part)'), ('origin', 'Inhalt (data-origin)'),
                       ('from', 'Von')):
        if req['head'].get(key):
            print(f'{label}: {req["head"][key]}')
    print('\n' + req['body'])
    return 0


def find_open(ident: str) -> dict | None:
    stem = Path(ident).stem if ident.endswith('.md') else ident
    hits = [r for r in open_requests() if r['path'].stem == stem] or \
           [r for r in open_requests() if r['path'].stem.endswith(stem)]
    return hits[0] if len(hits) == 1 else None


def cmd_done(args) -> int:
    if not args.result.strip():
        print('Fehler: --result fehlt (was wurde geändert, welche Regel gilt jetzt).', file=sys.stderr)
        return 1
    with mutex() as fh:
        lock = read_lock(fh)
        req = find_open(args.request)
        if not req:
            print(f'Fehler: keine offene Anfrage „{args.request}“ (siehe pin_queue.py status).', file=sys.stderr)
            return 1
        if req['head'].get('status') != 'in_progress' or req['head'].get('holder') != args.holder:
            print(f'Fehler: Die Anfrage gehört nicht {args.holder} (Status {req["head"].get("status")}, Editor '
                  f'{req["head"].get("holder") or "keiner"}). Zuerst: pin_queue.py next --holder {args.holder}',
                  file=sys.stderr)
            return 1
        other = editor(lock)
        if other and other != args.holder:
            print(f'Fehler: {lock_line(lock)}', file=sys.stderr)
            return 1
        check = subprocess.run([sys.executable, str(ROOT / 'tools' / 'check_repo.py'), 'all'], capture_output=True,
                               text=True)
        if check.returncode:
            print('Fehler: Die Anfrage bleibt offen, weil die Repository-Prüfung Befunde meldet. Beheben, dann done '
                  'erneut aufrufen.\n' + (check.stdout + check.stderr).strip(), file=sys.stderr)
            return 1
        stamp = now().isoformat()
        files = changed_sources()
        req['head'].update(status='done', done_at=stamp)
        req['body'] += ('\n\n## Ergebnis\n\n' + args.result.strip() + '\n\n## Geänderte Quellen\n\n'
                        + (''.join(f'- {digest}  {name}\n' for name, digest in sorted(files.items()))
                           or 'keine\n'))
        save(req, DONE / req['path'].name)
        left = len(open_requests())
        write_lock(fh, {'holder': args.holder, 'since': lock.get('since') or stamp, 'seen': stamp} if left else {})
    print(f'Erledigt: {rel(req["path"])} ({len(files)} geänderte Quelle(n) festgehalten)')
    print(f'Noch offen: {left}. Weiter mit: pin_queue.py next --holder {args.holder}' if left
          else 'Warteschlange leer. Sperre: frei')
    return 0


def cmd_status(args) -> int:
    with mutex() as fh:
        lock = read_lock(fh)
        requests = open_requests()
    print(lock_line(lock))
    print(f'Offene Anfragen: {len(requests)}')
    for req in requests:
        head = req['head']
        who = f', Editor {head["holder"]}' if head.get('holder') else ''
        print(f'  {req["path"].stem}  {head.get("status", "?")}{who}  {one_line(req["body"])}')
    missing = uncovered()
    changed = changed_sources()
    print(f'Geänderte Quellen unter {SOURCES}/ seit dem letzten Commit: {len(changed)}')
    for name in missing:
        print(f'  ohne Anfrage: {name}')
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return args.fn(args)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('enqueue')
    s.add_argument('--text')
    s.add_argument('--file')
    s.add_argument('--context')
    s.add_argument('--origin')
    s.add_argument('--part')
    s.add_argument('--id')
    s.add_argument('--from', dest='sender')
    s.set_defaults(fn=cmd_enqueue)
    s = sub.add_parser('next')
    s.add_argument('--holder', required=True)
    s.set_defaults(fn=cmd_next)
    s = sub.add_parser('done')
    s.add_argument('request')
    s.add_argument('--holder', required=True)
    s.add_argument('--result', required=True)
    s.set_defaults(fn=cmd_done)
    s = sub.add_parser('status')
    s.set_defaults(fn=cmd_status)
    return ap


if __name__ == '__main__':
    sys.exit(main())
