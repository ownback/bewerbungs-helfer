# Bewerbungshelfer

Ein lokales Werkzeug, das mit einem KI-Agenten (Claude Code, Codex oder einem anderen Harness mit Datei- und Browserzugriff) deutsche Bewerbungsmappen baut: für Ausbildungsplätze, Jobs und Praktika.

Du sprichst mit dem Agenten. Er gleicht deine vorhandenen Unterlagen ab, fragt nur nach, was fehlt, sucht passende Stellen bei der Bundesagentur für Arbeit und baut für jede ausgewählte Stelle eine eigene Mappe als HTML und nach deiner Freigabe als A4-PDF. Abschicken tust du selbst.

## Was eine Mappe enthält

1. Deckblatt
2. Anschreiben (pro Stelle neu: warum das Unternehmen dich nehmen sollte)
3. Lebenslauf
4. Motivationsschreiben (pro Stelle neu: warum dich das Fach begeistert)
5. Zertifikate
6. Zeugnisse

Deckblatt, Lebenslauf, Zertifikate und Zeugnisse kommen aus deiner persönlichen Profilvorlage und bleiben für alle Bewerbungen gleich. Zu jeder Mappe gibt es eine Kontaktübersicht und einen E-Mail-Entwurf.

## Voraussetzungen

- ein Agent-Harness mit Dateizugriff, Shell und Browser, z. B. [Claude Code](https://claude.com/claude-code) oder Codex
- Python 3.10 oder neuer (nur Standardbibliothek)
- Chromium oder Google Chrome für A4-Prüfung und PDF-Export
- optional: `pdftoppm` (Poppler) für Seitenbilder, `jsonschema` für die Schemaprüfung

## Starten

```bash
git clone https://github.com/ownback/bewerbungs-helfer
cd bewerbungs-helfer
```

Dann im Ordner den Agenten starten und den Skill aufrufen:

- Claude Code: `/bewerbungshelfer`
- Codex: `$bewerbungshelfer`

Beim ersten Mal legst du deine vorhandenen Unterlagen (alter Lebenslauf, Zeugnisse, Zertifikate, Bewerbungsfoto, Unterschrift) in `profile/import/`. Der Agent legt daraus dein Profil unter `profile/<vorname.nachname>/` an.

## So läuft ein Durchlauf

1. Profil wählen oder neu anlegen.
2. Kurzes Interview, nur zu fehlenden oder unklaren Angaben.
3. Der Agent baut deine Profilvorlage (Deckblatt, Lebenslauf, Nachweise). Du prüfst sie, bis sie passt.
4. Gemeinsame Suche bei der Bundesagentur für Arbeit. Du wählst eine oder mehrere Stellen. Für die Kontaktdaten löst du jeweils das Captcha im Browser.
5. Der Agent schreibt pro Stelle Anschreiben, Motivationsschreiben und E-Mail und baut die Mappe.
6. Du prüfst jede Mappe. Erst nach deinem ausdrücklichen Ja entsteht das PDF.
7. Du schickst die Bewerbung selbst ab und sagst dem Agenten Bescheid. Er verschiebt sie nach `sent/` und führt Buch.

## Deine Daten

Alles Persönliche bleibt auf deinem Rechner: `profile/` und `.tmp/` sind gitignoriert und landen nie im Repository. Der Agent erfindet keine Angaben, sendet nichts und füllt keine Portale aus.

## Aufbau

```text
CLAUDE.md                          Anweisungen für Agenten (AGENTS.md verweist darauf)
.agents/skills/bewerbungshelfer/   Skill: Ablauf, Referenzen, HTML-Vorlage, Schemas, Textvorlagen
.claude/agents/                    Subagenten für Claude Code (Texte + Mappe, QA)
tools/build_mappe.py               Baut, prüft und exportiert die Mappen
tools/devicon_symbols.py           Wandelt Logo-SVGs in Vorlagen-Symbole (nur für neue Logos)
profile/                           deine Profile und Bewerbungen (lokal, nicht versioniert)
```

Die Werkzeuge im Detail: `python3 tools/build_mappe.py --help`.

## Grenzen

- nur Deutsch
- nur Stellen der Bundesagentur für Arbeit
- kein automatisches Absenden, kein Ausfüllen von Bewerbungsportalen
- keine erfundenen Qualifikationen, Kontakte oder Nachweise
