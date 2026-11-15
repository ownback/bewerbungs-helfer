# Bewerbungshelfer

Ein lokales Werkzeug, das mit einem KI-Agenten (Claude Code, Codex oder einem anderen Harness mit Datei- und Browserzugriff) deutsche Bewerbungsmappen baut: für Ausbildungsplätze, Jobs und Praktika.

Du sprichst mit dem Agenten. Er gleicht deine vorhandenen Unterlagen ab, fragt nur nach, was fehlt, sucht passende Stellen bei der Bundesagentur für Arbeit und baut für jede ausgewählte Stelle eine eigene Mappe als HTML und nach deiner Freigabe als A4-PDF. Abschicken tust du selbst.

## Was eine Mappe enthält

1. Deckblatt
2. Anschreiben (pro Stelle neu: warum diese Firma, warum dieser Beruf)
3. Lebenslauf
4. Motivationsschreiben (ein Text für alle Bewerbungen: deine eigenen Projekte, was geklappt hat und was nicht; pro Stelle ändern sich nur der erste und der letzte Satz)
5. Zertifikate
6. Zeugnisse

Deckblatt, Lebenslauf, Zertifikate und Zeugnisse kommen aus deiner persönlichen Profilvorlage und bleiben für alle Bewerbungen gleich. Zu jeder Mappe gibt es eine Kontaktübersicht und einen E-Mail-Entwurf.

## Voraussetzungen

- ein Agent-Harness mit Dateizugriff, Shell und Browser, z. B. [Claude Code](https://claude.com/claude-code) oder Codex
- Python 3.10 oder neuer (nur Standardbibliothek)
- Chromium oder Google Chrome für A4-Prüfung und PDF-Export
- optional: `pdftoppm` (Poppler) für Seitenbilder und den Seitenvergleich

## Starten

```bash
git clone https://github.com/ownback/bewerbungs-helfer
cd bewerbungs-helfer
git config core.hooksPath tools/hooks
```

Die letzte Zeile schaltet einmal pro Klon den Git-Hook `tools/hooks/pre-commit` ein. Er ruft vor jedem Commit `python3 tools/check_repo.py all` auf und bricht ab, wenn persönliche Daten aus deinem Profil, verirrte Dateien, kaputte Schemas, eine Master-Vorlage, die nicht zu ihren Quellen passt, eine Änderung an der Vorlage ohne Anfrage oder eine Doku, die nicht zum Code passt, im Commit lägen. Claude Code führt dieselbe Prüfung nach jedem Schreiben einer Datei aus (Hook in `.claude/settings.json`).

Dann im Ordner den Agenten starten und den Skill aufrufen:

- Claude Code: `/bewerbungshelfer`
- Codex: `$bewerbungshelfer`

Beim ersten Mal legst du deine vorhandenen Unterlagen (alter Lebenslauf, Zeugnisse, Zertifikate, Bewerbungsfoto, Unterschrift) in `profile/import/`. Der Agent legt daraus dein Profil unter `profile/<vorname.nachname>/` an.

## So läuft ein Durchlauf

1. Profil wählen oder neu anlegen.
2. Kurzes Interview, nur zu fehlenden oder unklaren Angaben, dazu ein paar Fragen zu jedem deiner Projekte. Daraus entsteht dein Motivationsschreiben, das du einmal freigibst.
3. Der Agent baut deine Profilvorlage (Deckblatt, Lebenslauf, Nachweise). Du prüfst sie, bis sie passt.
4. Gemeinsame Suche bei der Bundesagentur für Arbeit. Du wählst eine oder mehrere Stellen. Für die Kontaktdaten löst du jeweils das Captcha im Browser. Zu jeder Firma sammelt der Agent belegte Fakten von ihrer Website.
5. Der Agent schreibt pro Stelle das Anschreiben, passt Motivationsschreiben und E-Mail an und baut die Mappe.
6. Du prüfst jede Mappe. Erst nach deinem ausdrücklichen Ja entsteht das PDF.
7. Du schickst die Bewerbung selbst ab und sagst dem Agenten Bescheid. Er verschiebt sie nach `sent/` und führt Buch.

Den Stand aller Stellen mit dem jeweils nächsten Schritt zeigt `python3 tools/build_mappe.py status profile/<vorname.nachname>`.

## Deine Daten

Alles Persönliche bleibt auf deinem Rechner: `profile/` und `.tmp/` sind gitignoriert und landen nie im Repository. Der Agent erfindet keine Angaben, sendet nichts und füllt keine Portale aus.

## Aufbau

```text
CLAUDE.md                          Anweisungen für Agenten (AGENTS.md verweist darauf)
.agents/skills/bewerbungshelfer/   Skill: Ablauf, Referenzen, Schemas, Textvorlagen
  assets/mappe/                    Quellen der Mappe: CSS, Partials (Markup), Symbole, Platzhalter-Modell, Grenzwerte
  assets/bewerbungsmappe.html      Master-Vorlage mit Platzhaltern, gebaut aus assets/mappe/ (nie von Hand ändern)
.claude/agents/                    Subagenten für Claude Code (Texte + Mappe, QA)
.claude/settings.json              Claude-Code-Hook: Repository-Prüfung nach jedem Edit/Write
tools/build_mappe.py               Baut, prüft und exportiert die Mappen; führt Ledger und Status
tools/mustache_lite.py             Rendert die Partials (Mustache-Teilmenge mit strengen Schlüsseln)
tools/schema_lite.py               JSON-Schema-Prüfung ohne Installation (für validate)
tools/serve_template.py            Vorschau-Server für die visuelle Prüfung (Tencil)
tools/pin_queue.py                 Warteschlange für Änderungen an der Vorlage: ein Editor zur Zeit
tools/check_repo.py                Prüft vor Commits: persönliche Daten, verirrte Dateien, Schemas, Master-Vorlage, Doku
tools/stale-terms.txt              Formulierungen, die in keiner Datei mehr stehen dürfen
tools/fresh_clone_test.py          Beweist an einem frischen Klon, dass dieselben Mappen entstehen
tools/hooks/pre-commit             Git-Hook für tools/check_repo.py
tools/devicon_symbols.py           Wandelt Logo-SVGs in Vorlagen-Symbole (nur für neue Logos)
profile/                           deine Profile und Bewerbungen (lokal, nicht versioniert)
```

Die Werkzeuge im Detail: `python3 tools/build_mappe.py --help`. Was sich wann geändert hat, steht in `CHANGELOG.md`; die übrige Doku beschreibt nur den heutigen Stand.

## Grenzen

- nur Deutsch
- nur Stellen der Bundesagentur für Arbeit
- kein automatisches Absenden, kein Ausfüllen von Bewerbungsportalen
- keine erfundenen Qualifikationen, Kontakte oder Nachweise
