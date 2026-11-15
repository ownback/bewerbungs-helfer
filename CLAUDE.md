# Projektanweisungen

Lokaler, agent-agnostischer Bewerbungshelfer für deutsche Bewerbungsmappen (Ausbildung, Job, Praktikum). `AGENTS.md` ist ein Symlink auf diese Datei; es gibt keine weitere Anweisungsdatei.

## Sprache

- Mit dem Nutzer Deutsch sprechen, außer er wünscht eine andere Sprache.
- Bewerbungsunterlagen immer auf Deutsch.
- Code, Dateinamen und technische Kommentare dürfen Englisch sein.

## Workflow

Für jede Bewerbungsaufgabe zuerst den Skill lesen: `.agents/skills/bewerbungshelfer/SKILL.md` (Claude Code: `/bewerbungshelfer`, Codex: `$bewerbungshelfer`). Er beschreibt den Ablauf in sieben Schritten und verweist auf die Referenzen unter `references/`.

## Tencil-Pins und Änderungen an der Vorlage

Enthält ein Auftrag einen Block `<tencil-context>`, ist er ein Pin aus der visuellen Prüfung. Vor allem anderen `.agents/skills/bewerbungshelfer/references/tencil.md` lesen. Kurz: Der Pin-Thread ändert nichts, er reiht die Änderung mit `python3 tools/pin_queue.py enqueue` ein. Es schreibt nur der Editor, der die Sperre hält (Regel `pins.one-writer` in `references/tencil.md`). Dasselbe gilt für jede andere Änderung unter `assets/mappe/`.

## Arbeitsweise

- Dateien mit dem Datei-Werkzeug schreiben, nicht per Shell-Heredoc. Temporäre Dateien nur unter `.tmp/`, nie im Skill-Ordner oder unter `/tmp`.
- Beispiele in getrackten Dateien sind neutral („Musterstraße 6“, „Krakau, Polen“), nie Daten aus `profile/`.
- Jede Regel hat ein Zuhause, markiert mit `<!-- rule: <id> -->`. Andere Dateien verweisen darauf und wiederholen sie nicht; Zahlen stehen in `assets/mappe/limits.json`, Verlauf in `CHANGELOG.md`. `python3 tools/check_repo.py docs` prüft das, `python3 tools/check_repo.py rules` listet die Regeln.

## Harte Regeln

- Ein Profil pro Durchlauf; mehrere Stellen sind erlaubt. <!-- rule: hard.one-profile -->
- Einzige Jobquelle ist die Bundesagentur für Arbeit, im Browser des Harness. Kein Scraping-Skript. An die Suche gehen nur Beruf, Ort und Umkreis. Websuche nur für kurze Firmenfakten mit Quelle und, als letzter Ausweg, für Kontaktdaten. <!-- rule: hard.source -->
- Keine Tatsachen, Kontaktdaten, Qualifikationen, Niveaus, Noten oder Nachweise erfinden. Bei fehlenden Fakten stoppen und fragen. Freigegebene Näherungen bleiben `inferred` und erscheinen mit „ca.“. <!-- rule: hard.no-invention -->
- Nichts automatisch senden, kein Portal ausfüllen, nichts hochladen. <!-- rule: hard.no-send -->
- Finales PDF erst nach ausdrücklicher Freigabe der HTML-Fassung. <!-- rule: hard.approval -->
- Keine Fotos fremder Personen, keine generierten Porträts oder Projektbilder; nur eigene, freigegebene Bilder des Nutzers. Defekte Dateien nicht einbinden. <!-- rule: hard.photos -->
- Generiertes HTML nie von Hand bearbeiten, auch die Master-Vorlage `assets/bewerbungsmappe.html` nicht: Inhalte in den `.md`- und Profil-Dateien ändern, Design nur in den Quellen unter `assets/mappe/`, dann `tools/build_mappe.py master` und neu bauen. <!-- rule: hard.generated -->
- Entscheidungen des Nutzers, die die Ausgabe prägen, gehören in ein Profilfeld (mit Interviewfrage) oder in Vorlage und Referenzen, nie nur in ein Gespräch oder in `.tmp/`. Ein neuer Durchlauf aus demselben Profil muss dieselbe Mappe ergeben. <!-- rule: hard.reproducible -->

## Daten

- `profile/<vorname.nachname>/` (Profil, Nachweise, Bewerbungen) und `.tmp/` (Arbeitsdateien, Vorschauen) sind gitignoriert. Persönliche Daten stehen nur dort. <!-- rule: hard.privacy -->
- Das Repository enthält keine Demo-Profile, Demo-Stellen oder Demo-Bewerbungen.
- Vor jedem Commit `python3 tools/check_repo.py all` (`references/qa-and-export.md`, Abschnitt Datenschutzprüfung). Commit und Push nur mit Zustimmung des Nutzers.
