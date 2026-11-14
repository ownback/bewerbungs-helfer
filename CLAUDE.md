# Projektanweisungen

Lokaler, agent-agnostischer Bewerbungshelfer für deutsche Bewerbungsmappen (Ausbildung, Job, Praktikum). `AGENTS.md` ist ein Symlink auf diese Datei; es gibt keine weitere Anweisungsdatei.

## Sprache

- Mit dem Nutzer Deutsch sprechen, außer er wünscht eine andere Sprache.
- Bewerbungsunterlagen immer auf Deutsch.
- Code, Dateinamen und technische Kommentare dürfen Englisch sein.

## Workflow

Für jede Bewerbungsaufgabe zuerst den Skill lesen: `.agents/skills/bewerbungshelfer/SKILL.md` (Claude Code: `/bewerbungshelfer`, Codex: `$bewerbungshelfer`). Er beschreibt den Ablauf und verweist auf die Referenzen unter `references/`.

Kurz: ein Profil pro Durchlauf, mehrere Bewerbungen pro Durchlauf. Profil wählen oder anlegen → Interview nur für Lücken → Profilvorlage bauen und freigeben lassen → Suche bei der Bundesagentur für Arbeit → Anzeigen nacheinander erfassen → pro Stelle parallel Texte, Mappe und QA → Freigabe pro Mappe → PDF → Versand durch den Nutzer → Ordner nach `sent/`.

## Tencil-Pins

Enthält ein Auftrag einen Block `<tencil-context>`, ist er ein Pin aus der visuellen Prüfung. Vor jeder Änderung `.agents/skills/bewerbungshelfer/references/tencil.md` lesen: richtige Quelle wählen, Doku im selben Durchgang anpassen, andere Pin-Threads berücksichtigen.

## Arbeitsweise

- Dateien mit dem Datei-Werkzeug schreiben, nicht per Shell-Heredoc. Temporäre Dateien nur unter `.tmp/`, nie im Skill-Ordner oder unter `/tmp`.
- Beispiele in getrackten Dateien sind neutral („Musterstraße 6“, „Krakau, Polen“), nie Daten aus `profile/`.

## Harte Regeln

- Einzige Jobquelle ist die Bundesagentur für Arbeit, im Browser des Harness. Kein Scraping-Skript.
- Keine Tatsachen, Kontaktdaten, Qualifikationen, Niveaus oder Nachweise erfinden. Lücken erfragen.
- Nichts automatisch senden, kein Portal ausfüllen, nichts hochladen.
- Finales PDF erst nach ausdrücklicher Freigabe der HTML-Fassung.
- Keine Fotos fremder Personen; nur das eigene, freigegebene Foto des Nutzers.
- Generiertes HTML nie von Hand bearbeiten: Inhalte in den `.md`- und Profil-Dateien ändern, Design nur in der Skill-Vorlage `assets/bewerbungsmappe.html`, dann `tools/build_mappe.py` erneut ausführen.

## Daten

- `profile/<vorname.nachname>/` (Profil, Nachweise, Bewerbungen) und `.tmp/` (Arbeitsdateien, Vorschauen) sind gitignoriert.
- Das Repository enthält keine Demo-Profile, Demo-Stellen oder Demo-Bewerbungen.
- Vor jedem Commit getrackte Dateien auf Namen, Telefonnummern, E-Mail-Adressen und Straßen des Nutzers prüfen (`references/qa-and-export.md`, Abschnitt Datenschutzprüfung). Commit und Push nur mit Zustimmung des Nutzers.
