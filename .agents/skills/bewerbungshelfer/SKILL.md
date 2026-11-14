---
name: bewerbungshelfer
description: Baut deutsche Bewerbungsmappen (Ausbildung, Job, Praktikum) aus einem lokalen Profil und Stellen der Bundesagentur für Arbeit. Ein Profil pro Durchlauf, mehrere Bewerbungen parallel. Profil anlegen oder wählen, Lücken erfragen, Profilvorlage bauen, BA-Suche im Browser, pro Stelle Anschreiben, Motivationsschreiben, E-Mail und HTML-Mappe, PDF nach Freigabe, Ledger und Versandablage.
metadata:
  short-description: Deutsche Bewerbungsmappen aus Profil und BA-Stellen
---

# Bewerbungshelfer

## Ergebnis

Für **ein Profil** und **eine oder mehrere Stellen** der Bundesagentur für Arbeit (BA) entsteht pro Stelle ein eigener Ordner mit:

- `job_information/ba_scrape.md` (wörtliche Anzeige) und `job.json` (strukturiert),
- `text_generation/anschreiben.md`, `motivationsschreiben.md`, `kontaktdaten.md`,
- `application/bewerbungsmappe - <vorname.nachname>.html`, nach Freigabe `.pdf`, dazu `email.md` und `application-manifest.json`.

Die Mappe hat sechs Abschnitte: Deckblatt, Anschreiben, Lebenslauf, Motivationsschreiben, Zertifikate, Zeugnisse. Deckblatt, Lebenslauf und Nachweise kommen aus der freigegebenen **Profilvorlage** und sind für alle Bewerbungen gleich. Anschreiben, Motivationsschreiben und E-Mail werden pro Stelle neu geschrieben. Nichts wird gesendet.

## Referenzen

Nur lesen, was der aktuelle Schritt braucht:

| Schritt | Referenz |
|---|---|
| Profil wählen, Import, Interview | `references/interview.md` |
| Profildaten und Schema | `references/profile-schema.md` |
| Vorlage, Seiten, Design, Datenvertrag | `references/template.md` |
| Vorlage visuell prüfen und ändern (Tencil) | `references/tencil.md` |
| BA-Suche und Erfassung im Browser | `references/job-search.md` |
| Ordner, Namen, Ledger, Status, Statistik | `references/applications.md` |
| Paralleles Schreiben mit Subagenten | `references/fan-out.md` |
| Anschreiben, Motivation, E-Mail, Kontaktdaten | `references/writing.md` |
| Build, QA, Freigabe, PDF, Datenschutz | `references/qa-and-export.md` |

Vorlagen und Schemas: `assets/bewerbungsmappe.html`, `assets/templates/`, `assets/schemas/`. Das Werkzeug für Bau und Prüfung ist `tools/build_mappe.py` im Repository (nur Python-Standardbibliothek, Chromium für A4).

## Ablauf

### 1. Profil wählen oder anlegen

Liste die Ordner unter `profile/` (ohne `import/` und `assets/`). Frage, welches Profil dieser Durchlauf nutzt; pro Durchlauf genau eines.

Neues Profil: Der Nutzer legt seine Unterlagen in `profile/import/`. Lege `profile/<vorname.nachname>/` nach `references/applications.md` an und verschiebe die Dateien in die passenden Unterordner (`assets/documents/old/` für den alten Lebenslauf, `assets/documents/` für Zeugnisse und Zertifikate, `assets/photos/cv/`, `assets/signature/`). Dateinamen: `<vorname.nachname>_<inhalt>.<endung>`.

### 2. Interview und Profil

Nach `references/interview.md`:

- Unterlagen aus `assets/documents/old/` vollständig und visuell lesen und in `assets/documents/old/extracted_information.md` festhalten.
- Nur nach Lücken, Widersprüchen und defekten Dateien fragen. Nichts erfinden, nichts raten.
- Pro Projekt nach einem eigenen Foto und der Einwilligung fragen (`references/interview.md`, Block 5). Ohne Foto entfällt es, die Mappe baut trotzdem.
- Bestätigte Angaben in `assets/profile/<name>_profile.json` speichern, `<name>_profile.md` als lesbare Fassung pflegen.
- Prüfen: `python3 tools/build_mappe.py validate profile/<name>` (braucht `jsonschema`, siehe `references/qa-and-export.md`).

### 3. Profilvorlage bauen und freigeben

```bash
python3 tools/build_mappe.py profile-template profile/<name> --qa --pdf
```

Das erzeugt `assets/profile/<name>_template.html` und die A4-Vorschau `<name>_template.pdf`: Skill-Vorlage plus stabile Teile (Deckblatt, Absender, Lebenslauf, Zertifikate, Zeugnisse); Anschreiben und Motivationsschreiben bleiben Platzhalter. Zeige dem Nutzer die Vorschau und frage, ob sie passt.

- Das Skript meldet den Füllgrad der Lebenslauf-Seiten und ausgeblendete Schulen; die Aufteilung folgt `references/template.md` (Lebenslauf).
- Inhaltliche Änderungen: im Profil-JSON, dann neu bauen.
- Designänderungen: nur in der Skill-Vorlage `assets/bewerbungsmappe.html`, visuell über Tencil (`references/tencil.md`), dann neu bauen.
- Generiertes HTML nie von Hand bearbeiten.

Schleife, bis der Nutzer zufrieden ist. Jede spätere Profiländerung braucht einen neuen Bau und einen neuen Blick des Nutzers.

### 4. Stellen suchen und erfassen

Nach `references/job-search.md` im Browser des Harness (kein Skript). Ablauf und Selektoren stehen dort. Kurz:

1. Suche mit Beruf, Zielort und Umkreis (Vorgabe des Nutzers, sonst „ganzer Ort“; ohne Treffer erst fragen, dann vorsichtig erweitern).
2. Treffer kurz zeigen (Titel, Firma, Ort, Entfernung, Beginn, Veröffentlichung). Der Nutzer wählt eine oder mehrere Stellen.
3. Duplikate prüfen: gleiche Referenznummer oder gleiche Firma + Titel im Ledger → Nutzer warnen (`references/applications.md`).
4. Ränge nach Entfernung vom Suchort vergeben (`NN`), Ordner anlegen.
5. Jede Anzeige **nacheinander im selben Tab** vollständig erfassen (Kopf, Text und Kontakt in einem Besuch): `ba_scrape.md` wörtlich, `job.json` strukturiert. Für die Kontaktdaten zum Captcha scrollen und den **Nutzer** bitten, es zu lösen. Kurze Websuche zur Firma ist erlaubt (Fakten mit Quelle).
6. `job.json` gegen das Schema prüfen.

Browserarbeit bleibt beim Hauptagenten; Subagenten haben oft keinen Browser.

### 5. Pro Stelle schreiben, bauen, prüfen (parallel)

Nach `references/fan-out.md`: pro Stelle ein Subagent (Claude Code: `bewerbung-writer`, danach `bewerbung-qa`). Jeder Subagent arbeitet nur in seinem Stellenordner:

1. Passung prüfen (`requirements[].status` in `job.json`).
2. `anschreiben.md`, `motivationsschreiben.md`, `email.md` nach `references/writing.md` schreiben, `kontaktdaten.md` aus `job.json` erstellen.
3. Skill `humanizer` auf Anschreiben, Motivationsschreiben und E-Mail anwenden (nicht auf `kontaktdaten.md`). Fehlt der Skill, das sagen und seine Grundsätze von Hand anwenden.
4. Bauen und prüfen: `python3 tools/build_mappe.py application <stellenordner> --qa`. Bei Überlauf Text kürzen oder `dichte: dicht` setzen, nie das HTML ändern. Bei Bewerbungsweg `email` meldet die QA einen fehlenden oder unvollständigen `email.md`-Entwurf als Fehler; der Entwurf gehört vor die Freigabe.
5. QA-Durchgang mit Faktencheck gegen Profil und Anzeige (`references/qa-and-export.md`).

Ohne Subagenten: dieselben Schritte nacheinander pro Stelle.

### 6. Freigabe pro Mappe

Zeige jede Mappe (HTML im Browser, A4-Vorschau als Bild oder PDF in `.tmp/`). Frage einzeln:

> Ist die HTML-Fassung für <Firma> inhaltlich und optisch freigegeben?

Nur bei eindeutigem Ja:

```bash
python3 tools/build_mappe.py status <stellenordner> html_approved
python3 tools/build_mappe.py application <stellenordner> --qa --pdf
```

Das Skript verweigert das PDF ohne Freigabe, mit QA-Befund oder bei Bewerbungsweg `email` ohne gültigen Entwurf `email.md`. Ändert sich danach ein Text, fällt der Status auf `draft` zurück und die Freigabe ist neu einzuholen.

### 7. Versand durch den Nutzer und Ablage

Der Nutzer sendet selbst (E-Mail-Entwurf in `email.md`, Kontaktdaten in `kontaktdaten.md`). Kein Portal ausfüllen, nichts hochladen, nichts senden. Erst wenn der Nutzer bestätigt, dass die Bewerbung raus ist:

```bash
python3 tools/build_mappe.py mark-sent <stellenordner> --channel email|post|portal
```

Der Ordner wandert nach `applications/sent/<typ>/…`, das Ledger bekommt Status, Datum und Kanal. `status … sent` gibt es nicht: nur `mark-sent` setzt „gesendet“, weil es Ordner und Ledger zusammen aktualisiert. Spätere Rückmeldungen: `status <ordner> interview|offer|rejected|withdrawn`. Statistik: `stats profile/<name>` (`references/applications.md`).

## Harte Regeln

- Ein Profil pro Durchlauf; mehrere Stellen sind erlaubt.
- Einzige Jobquelle: Bundesagentur für Arbeit, im Browser des Harness. Kein Scraping-Skript. Websuche nur für kurze Firmenfakten mit Quelle und, als letzter Ausweg, für Kontaktdaten.
- An die BA-Suche gehen nur Beruf, Ort und Umkreis, keine weiteren Profildaten.
- Keine erfundenen Tatsachen, Kontaktdaten, Qualifikationen, Niveaus, Noten oder Nachweise. Bei fehlenden Fakten stoppen und fragen.
- Freigegebene Näherungen bleiben `inferred` und erscheinen mit „ca.“.
- Kein automatisches Senden, kein Portal ausfüllen, kein Upload.
- Finales PDF erst nach ausdrücklicher HTML-Freigabe.
- Keine Fotos fremder Personen, keine generierten Porträts oder Projektbilder; Projektfotos nur mit `consent` und `valid` und nur am Beleg mit gleichem Projektnamen; defekte Dateien nicht einbinden.
- Generiertes HTML nie von Hand bearbeiten; Design nur in der Skill-Vorlage.
- Entscheidungen des Nutzers, die die Ausgabe prägen, gehören in ein Profilfeld (mit Interviewfrage) oder in Vorlage und Referenzen, nie nur in ein Gespräch oder in `.tmp/`. Ein neuer Durchlauf aus demselben Profil muss dieselbe Mappe ergeben.
- Persönliche Daten nur in `profile/` und `.tmp/`; nichts davon committen.
