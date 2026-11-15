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
| Quellen der Vorlage, Seiten, Design, Attribute für Pins | `references/template.md` |
| Vorlage visuell prüfen und ändern (Tencil) | `references/tencil.md` |
| BA-Suche und Erfassung im Browser | `references/job-search.md` |
| Ordner, Namen, Ledger, Status, Übersicht, Duplikate, Aussortieren, Statistik | `references/applications.md` |
| Paralleles Schreiben mit Subagenten | `references/fan-out.md` |
| Anschreiben, Motivation, E-Mail, Kontaktdaten | `references/writing.md` |
| Build, QA, Freigabe, PDF, Datenschutz | `references/qa-and-export.md` |

Vorlagen und Schemas: `assets/mappe/` (Quellen der Mappe: CSS, Partials, Symbole, Grenzwerte in `limits.json`), `assets/bewerbungsmappe.html` (daraus gebaute Master-Vorlage mit Platzhaltern), `assets/templates/`, `assets/schemas/`.

Werkzeuge im Repository (nur Python-Standardbibliothek, Chromium für A4):

| Werkzeug | Zweck |
|---|---|
| `tools/build_mappe.py` | bauen, prüfen, exportieren, Stand und Ledger (`references/qa-and-export.md`, `references/applications.md`) |
| `tools/pin_queue.py` | Warteschlange für Änderungen an der Vorlage, ein Editor zur Zeit (`references/tencil.md`) |
| `tools/check_repo.py` | Repository-Prüfung vor jedem Commit und nach jedem Schreiben, auch Doku gegen Code (`references/qa-and-export.md`, Repository-Prüfung) |

Jede Regel hat genau ein Zuhause in einer dieser Dateien oder in `CLAUDE.md`; `python3 tools/check_repo.py rules` listet sie.

## Ablauf

### 1. Profil wählen oder anlegen

Liste die Ordner unter `profile/` (ohne `import/` und `assets/`). Frage, welches Profil dieser Durchlauf nutzt; pro Durchlauf genau eines.

Bestehendes Profil mit Stellen: zuerst den Stand lesen. `python3 tools/build_mappe.py status profile/<name>` zeigt pro Stelle Status, Frist, Bewerbungsweg, offene blockierende Fragen und den nächsten Schritt (`references/applications.md`, Übersicht).

Neues Profil: Der Nutzer legt seine Unterlagen in `profile/import/`. Lege `profile/<vorname.nachname>/` nach `references/applications.md` an und verschiebe die Dateien in die passenden Unterordner (`assets/documents/old/` für den alten Lebenslauf, `assets/documents/` für Zeugnisse und Zertifikate, `assets/photos/cv/`, `assets/signature/`). Dateinamen: `<vorname.nachname>_<inhalt>.<endung>`.

### 2. Interview und Profil

Nach `references/interview.md`:

- Unterlagen aus `assets/documents/old/` vollständig und visuell lesen und in `assets/documents/old/extracted_information.md` festhalten.
- Nur nach Lücken, Widersprüchen und defekten Dateien fragen. Nichts erfinden, nichts raten.
- Pro Projekt nach einem eigenen Foto und der Einwilligung fragen (`references/interview.md`, Block 5).
- Bestätigte Angaben in `assets/profile/<name>_profile.json` speichern, `<name>_profile.md` als lesbare Fassung pflegen.
- Prüfen: `python3 tools/build_mappe.py validate profile/<name>` (läuft ohne Installation, siehe `references/qa-and-export.md`).

### 3. Profilvorlage bauen und freigeben

```bash
python3 tools/build_mappe.py profile-template profile/<name> --qa --pdf
```

Das erzeugt `assets/profile/<name>_template.html` und die A4-Vorschau `<name>_template.pdf`: die stabilen Teile aus dem Profil (Deckblatt, Absender, Lebenslauf, Zertifikate, Zeugnisse); Anschreiben und Motivationsschreiben bleiben Platzhalter. Zeige dem Nutzer die Vorschau und frage, ob sie passt.

- Das Skript meldet den Füllgrad der Lebenslauf-Seiten und ausgeblendete Schulen; die Aufteilung folgt Regel `cv.layout` in `references/template.md`.
- Inhaltliche Änderungen: im Profil-JSON, dann neu bauen.
- Designänderungen: als Anfrage über die Warteschlange, mit Tencil oder aus dem Gespräch (`references/tencil.md`):

  ```bash
  python3 tools/pin_queue.py enqueue --text "<Wunsch des Nutzers>"
  python3 tools/pin_queue.py status
  ```

Schleife, bis der Nutzer zufrieden ist. Jede spätere Profiländerung braucht einen neuen Bau und einen neuen Blick des Nutzers.

### 4. Stellen suchen und erfassen

Nach `references/job-search.md` im Browser des Harness (kein Skript). Ablauf und Selektoren stehen dort. Kurz:

1. Suche mit Beruf, Zielort und Umkreis (Vorgabe des Nutzers, sonst „ganzer Ort“; ohne Treffer erst fragen, dann vorsichtig erweitern).
2. Treffer kurz zeigen (Titel, Firma, Ort, Entfernung, Beginn, Veröffentlichung). Der Nutzer wählt eine oder mehrere Stellen.
3. Duplikate prüfen: vor dem Erfassen im Ledger, danach mit `python3 tools/build_mappe.py check-duplicate <stellenordner>` (Regel `jobs.duplicate` in `references/applications.md`).
4. Ränge nach Entfernung vom Suchort vergeben (`NN`), Ordner anlegen.
5. Jede Anzeige vollständig erfassen: `ba_scrape.md` wörtlich, `job.json` strukturiert. Ein Tab, eine Anzeige nach der anderen (Regel `capture.one-tab` in `references/job-search.md`); das Captcha löst der Nutzer (Regel `capture.captcha` in `references/job-search.md`).
6. `python3 tools/build_mappe.py validate <stellenordner>`, offene Punkte mit `status` führen (Regel `jobs.open-questions` in `references/job-search.md`), dann `python3 tools/build_mappe.py ledger sync profile/<name>`: Die Stellen stehen mit Status `captured` im Ledger.
7. Stellen, die der Filter oder der Nutzer ausschließt, mit `drop --reason` aussortieren (Regel `jobs.drop` in `references/applications.md`).

Browserarbeit bleibt beim Hauptagenten (Regel `agents.lanes` in `references/fan-out.md`).

### 5. Pro Stelle schreiben, bauen, prüfen (parallel)

Nach `references/fan-out.md`: pro Stelle ein Subagent (Claude Code: `bewerbung-writer`, danach `bewerbung-qa`). Jeder Subagent arbeitet nur in seinem Stellenordner:

1. Passung prüfen (`requirements[].status` in `job.json`). Stellen mit offener blockierender Frage oder nicht eingearbeiteter Antwort gehen erst nach der Klärung an den Subagenten.
2. `anschreiben.md`, `motivationsschreiben.md`, `email.md` nach `references/writing.md` schreiben, `kontaktdaten.md` aus `job.json` erstellen.
3. Humanizer anwenden (Regel `letters.humanizer` in `references/writing.md`).
4. Bauen und prüfen: `python3 tools/build_mappe.py application <stellenordner> --qa`. Befunde über die Texte beheben (`references/qa-and-export.md`, Bei Problemen).
5. QA-Durchgang nach der Prüfliste in `references/qa-and-export.md`.

Ohne Subagenten: dieselben Schritte nacheinander pro Stelle.

### 6. Freigabe pro Mappe

Zeige jede Mappe (HTML im Browser, A4-Vorschau als Bild oder PDF in `.tmp/`). Frage einzeln:

> Ist die HTML-Fassung für <Firma> inhaltlich und optisch freigegeben?

Nur bei eindeutigem Ja:

```bash
python3 tools/build_mappe.py status <stellenordner> html_approved
python3 tools/build_mappe.py application <stellenordner> --qa --pdf
```

Die Freigabe gilt für genau den gezeigten Stand (Regel `approval.checksum` in `references/qa-and-export.md`). Wann das Skript das PDF verweigert: Regel `pdf.refuse` in `references/qa-and-export.md`.

### 7. Versand durch den Nutzer und Ablage

Der Nutzer sendet selbst (E-Mail-Entwurf in `email.md`, Kontaktdaten in `kontaktdaten.md`; Regel `hard.no-send` in `CLAUDE.md`). Erst wenn der Nutzer bestätigt, dass die Bewerbung raus ist:

```bash
python3 tools/build_mappe.py mark-sent <stellenordner> --channel email|post|portal
```

Der Ordner wandert nach `applications/sent/<typ>/…`, das Ledger bekommt Status, Datum und Kanal (Regel `status.sent` in `references/applications.md`). Spätere Rückmeldungen: `status <ordner> interview|offer|rejected|withdrawn`. Übersicht: `status profile/<name>`, Statistik: `stats profile/<name>` (`references/applications.md`).

## Harte Regeln

Die harten Regeln stehen in `CLAUDE.md` (Abschnitte „Harte Regeln“ und „Daten“, Regeln `hard.…`) und gelten in jedem Schritt. Diese Datei wiederholt sie nicht.
