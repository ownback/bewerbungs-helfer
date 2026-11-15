#!/usr/bin/env python3
"""Frischer-Klon-Test, Stufe 1 (ohne Modell, nur Python-Standardbibliothek, git, Chromium, pdftoppm).

Beweist, dass die getrackten Dateien zusammen mit einem Profilordner dieselben Mappen ergeben wie der
Arbeitsordner: Nichts hängt an .tmp/, an installierten Paketen oder an Dateien, die nur lokal liegen.

  python3 tools/fresh_clone_test.py [profile/<name>] [--working-tree] [--keep]

Ablauf:
  1. Klon des Repositorys nach .tmp/fresh-clone/repo (Stand HEAD). Mit --working-tree zusätzlich alle Dateien,
     die ein Commit jetzt aufnehmen würde (geändert oder neu, nicht ignoriert): so lässt sich ein Stand vor dem
     Commit prüfen.
  2. profile/<name>/ wird in den Klon kopiert (ohne Angabe: das einzige Profil).
  3. Im Klon laufen, mit „python3 -I“ (keine Pakete des Nutzers, kein PYTHONPATH):
     check_repo.py mit allen Prüfungen außer pins (die Warteschlange unter .tmp/pins/ gehört zum Arbeitsordner,
     nicht zum Klon) · build_mappe.py master --check · validate · profile-template --qa · application --qa für
     jede Stelle, die im Arbeitsordner eine gebaute Mappe hat.
  4. Verglichen wird mit dem Arbeitsordner: Ausgabe von validate gleich; jede HTML-Datei Byte für Byte gleich;
     HTML-Seiten = A4-Seiten; Seitenbilder ohne Abweichung.

Exit 0, wenn alles übereinstimmt, sonst 1. Der Klon wird danach gelöscht (--keep lässt ihn stehen).
Stufe 2 (Profil aus den Interview-Antworten mit einem Agenten neu aufbauen) ist nicht Teil dieses Skripts.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_mappe as bm  # noqa: E402
import check_repo  # noqa: E402

WORK = ROOT / '.tmp' / 'fresh-clone'


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True, check=True).stdout


def run(clone: Path, *args: str) -> tuple[int, str]:
    """Befehl im Klon mit isoliertem Python; Rückgabe: Exit-Code und Ausgabe (stdout + stderr)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
    done = subprocess.run([sys.executable, '-I', *args], cwd=clone, env=env, capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def make_clone(working_tree: bool) -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    clone = WORK / 'repo'
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], check=True)
    dirty = [line for line in git('status', '--porcelain').splitlines() if line.strip()]
    if working_tree:
        wanted = {f for f in git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split('\0') if f}
        for name in git('ls-files', '-z', cwd=clone).split('\0'):
            if name and name not in wanted:
                (clone / name).unlink()
        for name in sorted(wanted):
            src, dst = ROOT / name, clone / name
            if src.is_symlink() or not src.is_file():
                continue  # Symlinks (AGENTS.md, .claude/skills/…) kommen aus dem Klon
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        print(f'Klon: HEAD {git("rev-parse", "--short", "HEAD").strip()} + Arbeitsstand '
              f'({len(dirty)} geänderte oder neue Dateien)')
    else:
        print(f'Klon: HEAD {git("rev-parse", "--short", "HEAD").strip()}')
        if dirty:
            print(f'  Hinweis: {len(dirty)} geänderte oder neue Dateien im Arbeitsordner sind nicht im Klon. '
                  'Ungespeicherte Arbeit prüfen: --working-tree')
    return clone


def same_pages(a: Path, b: Path) -> str:
    """'' wenn beide Mappen dieselben Seitenbilder ergeben, sonst eine kurze Beschreibung."""
    with tempfile.TemporaryDirectory(dir=WORK) as tmp:
        pages_a = bm.render_pages(a, Path(tmp) / 'a')
        pages_b = bm.render_pages(b, Path(tmp) / 'b')
        if len(pages_a) != len(pages_b):
            return f'{len(pages_a)} statt {len(pages_b)} Seiten'
        changed = [str(n) for n, (x, y) in enumerate(zip(pages_a, pages_b), 1)
                   if bm.diff_pages(bm.read_pgm(x), bm.read_pgm(y), 0)]
        return f'Seite {", ".join(changed)} weicht ab' if changed else ''


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('profile', nargs='?')
    ap.add_argument('--working-tree', action='store_true')
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args(argv)
    if args.profile:
        pdir = bm.profile_dir_arg(args.profile)
    else:
        found = sorted(p.parents[2] for p in (ROOT / 'profile').glob('*/assets/profile/*_profile.json'))
        if len(found) != 1:
            print(f'Profilordner angeben: {len(found)} Profile unter profile/ gefunden.', file=sys.stderr)
            return 1
        pdir = found[0]
    name = pdir.name
    prel = f'profile/{name}'
    postings = [p for p in bm.iter_postings(pdir) if (p / 'application' / bm.html_name(name)).is_file()
                and not bm.posting_info(p)['dropped']]
    clone = make_clone(args.working_tree)
    shutil.copytree(pdir, clone / prel, symlinks=True)
    print(f'Profil kopiert: {prel} ({len(postings)} gebaute Mappe(n))')

    results: list[tuple[bool, str, str]] = []

    def record(ok: bool, what: str, detail: str = '') -> None:
        results.append((ok, what, detail))
        print(f'{"ok     " if ok else "FEHLER "} {what}' + (f': {detail}' if detail else ''))

    checks = [name for name in check_repo.CHECKS if name != 'pins']
    rc, out = run(clone, 'tools/check_repo.py', *checks)
    record(rc == 0, f'check_repo.py {" ".join(checks)}', '' if rc == 0 else out.strip().splitlines()[-1])
    rc, out = run(clone, 'tools/build_mappe.py', 'master', '--check')
    record(rc == 0, 'master --check', '' if rc == 0 else out.strip())
    rc, out = run(clone, 'tools/build_mappe.py', 'validate', prel)
    ref = subprocess.run([sys.executable, '-I', 'tools/build_mappe.py', 'validate', prel], cwd=ROOT,
                         capture_output=True, text=True)
    lines = out.strip().splitlines()
    schema_bad = sum(1 for line in lines if line.startswith('FEHLER') and line.rstrip().endswith('.json'))
    record(rc == ref.returncode and out == ref.stdout + ref.stderr and not schema_bad, 'validate ohne installierte Pakete',
           f'{sum(1 for line in lines if line.startswith("ok"))} ok, {schema_bad} Schemafehler, Exit {rc} wie im '
           f'Arbeitsordner' if rc == ref.returncode else f'Exit {rc}, im Arbeitsordner {ref.returncode}')

    def compare(label: str, original: Path, built: Path, qa_rc: int, qa_out: str, want_rc: set[int]) -> None:
        if not built.is_file():
            record(False, label, f'nicht gebaut: {qa_out.strip().splitlines()[-1] if qa_out.strip() else ""}')
            return
        problems = []
        if qa_rc not in want_rc:
            problems.append(f'Exit {qa_rc}')
        if built.read_bytes() != original.read_bytes():
            problems.append('HTML weicht ab ('
                            + bm.first_difference(original.read_text(encoding='utf-8'),
                                                  built.read_text(encoding='utf-8')) + ')')
        pages = next((line.strip() for line in qa_out.splitlines() if line.strip().startswith('Seiten:')), '')
        counts = [int(x) for x in pages.replace(',', ' ').split() if x.isdigit()]
        if len(counts) != 2 or counts[0] != counts[1]:
            problems.append(f'Seitenzahl: {pages or "keine Angabe"}')
        diff = same_pages(original, built)
        if diff:
            problems.append(diff)
        record(not problems, label, '; '.join(problems) or f'HTML byteidentisch, {pages}, Seitenbilder gleich')

    tpl = bm.profile_template_path(pdir)
    rc, out = run(clone, 'tools/build_mappe.py', 'profile-template', prel, '--qa')
    compare('Profilvorlage', tpl, clone / tpl.relative_to(ROOT), rc, out, {0})
    for posting in postings:
        rel_posting = posting.relative_to(ROOT).as_posix()
        html_path = posting / 'application' / bm.html_name(name)
        rc, out = run(clone, 'tools/build_mappe.py', 'application', rel_posting, '--qa')
        # Exit 2 = QA-Befund am Inhalt (z. B. fehlender E-Mail-Entwurf): kein Unterschied zwischen Klon und Original
        compare(f'Mappe {posting.name}', html_path, clone / html_path.relative_to(ROOT), rc, out, {0, 2})
    bad = [r for r in results if not r[0]]
    print(f'Frischer Klon, Stufe 1: {"bestanden" if not bad else f"{len(bad)} von {len(results)} Prüfungen fehlgeschlagen"}'
          f' ({len(results)} Prüfungen)')
    if args.keep:
        print(f'Klon bleibt stehen: {clone.relative_to(ROOT)}')
    else:
        shutil.rmtree(WORK)
    return 1 if bad else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except bm.BuildError as e:
        print(f'Fehler: {e}', file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f'Fehler beim Aufruf von {e.cmd[0]}: {e.stderr or e}', file=sys.stderr)
        sys.exit(1)
