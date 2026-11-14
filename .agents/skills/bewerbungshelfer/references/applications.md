# Ordner, Namen, Ledger und Status

## Profilordner

```text
profile/<vorname.nachname>/
  assets/
    documents/<name>_<inhalt>.png        Zeugnisse, Zertifikate
    documents/old/                       alter Lebenslauf, extracted_information.md
    photos/cv/<name>_bewerbungsbild.png  Bewerbungsfoto
    photos/project/                      Projektfotos
    signature/<name>_unterschrift.png
    profile/<name>_profile.json|.md      Profil
    profile/<name>_template.html|.pdf    Profilvorlage und Vorschau (gebaut)
  applications/
    ledger.json
    apprenticeships/ jobs/ internships/                              aktive Stellen
    sent/apprenticeships/ sent/jobs/ sent/internships/               gesendete Bewerbungen
    dropped/apprenticeships/ dropped/jobs/ dropped/internships/      aussortierte Stellen
```

## Stellenordner

```text
applications/<typ>/<beruf-slug>/<suchort-slug>/<NN>-<ort-slug>-<firma-slug>/
  job_information/
    ba_scrape.md
    job.json
    portal_page.md                      nur bei Portal- oder Partnerseiten (references/job-search.md)
  text_generation/
    anschreiben.md
    motivationsschreiben.md
    kontaktdaten.md
  application/
    bewerbungsmappe - <name>.html
    bewerbungsmappe - <name>.pdf        erst nach Freigabe
    email.md
    application-manifest.json
    assets/                             vom Build-Skript kopierte Bilder
  DROPPED.txt                           nur unter dropped/: Grund und Datum
```

- `<typ>`: `apprenticeships`, `jobs` oder `internships` (`job.json` → `type`).
- `<beruf-slug>`: gesuchter Beruf, z. B. `fachinformatiker-systemintegration`.
- `<suchort-slug>`: Ort, in dem gesucht wurde, z. B. `musterstadt`.
- `<NN>`: zweistelliger Rang nach Entfernung vom Suchort, `01` = am nächsten.
- `<ort-slug>`: Arbeitsort der Stelle (kann der Suchort sein).
- `<firma-slug>`: kurzer Firmenname ohne Rechtsform, z. B. `musterfirma` (aus „Musterfirma GmbH & Co. KG“).

Slugs: Kleinbuchstaben, ASCII, `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, alles andere als Bindestrich, keine doppelten oder randständigen Bindestriche.

Ränge: Die Stellen eines Durchlaufs werden nach Entfernung sortiert. Liegen im Ordner `<beruf>/<suchort>/` schon Stellen (auch unter `sent/` oder `dropped/`), zählen neue Ränge ab der höchsten vorhandenen Nummer weiter (in Entfernungsreihenfolge). Der Ordnername bleibt für immer gleich; nur `mark-sent`, `drop` und `restore` verschieben den Ordner zwischen `applications/`, `applications/sent/` und `applications/dropped/`.

Generierte Dateinamen enthalten den Profilnamen, z. B. `bewerbungsmappe - max.mustermann.html`.

## Status

| Status | Bedeutung | gesetzt durch |
|---|---|---|
| `captured` | Anzeige erfasst (`job.json` liegt vor), noch keine Mappe | ergibt sich aus dem Ordner |
| `draft` | Mappe gebaut, nicht freigegeben | `application` |
| `html_approved` | Nutzer hat die HTML-Fassung ausdrücklich freigegeben; das Manifest hält die Prüfsumme dieses Stands fest (`references/qa-and-export.md`, Freigabe) | `status … html_approved` |
| `pdf_exported` | finales PDF erzeugt und geprüft | `application --pdf` |
| `sent` | Nutzer hat bestätigt, dass er gesendet hat | nur `mark-sent --channel …` |
| `interview`, `offer`, `rejected`, `withdrawn` | Rückmeldung nach dem Versand | `status …` |
| `dropped` | Stelle aussortiert, mit Grund | nur `drop --reason …` |

Der normale Weg ist `captured → draft → html_approved → pdf_exported → sent`, danach eine Rückmeldung. `dropped` ist aus jedem Status vor `sent` möglich.

`status <ordner> sent`, `status <ordner> dropped` und `status <ordner> captured` werden abgelehnt (Fehlermeldung mit dem richtigen Befehl): Bei `sent` und `dropped` gehören Ordner und Status zusammen, `captured` gilt von selbst. `status <ordner> html_approved` warnt, wenn bei Bewerbungsweg `email` der Entwurf `application/email.md` noch fehlt; das PDF gibt es erst mit Entwurf (`references/qa-and-export.md`).

Ändert sich eine freigegebene Mappe beim Neubau, fällt sie auf `draft` zurück.

## Ledger

`applications/ledger.json` nach `assets/schemas/ledger.schema.json`, Startpunkt `assets/templates/ledger.json`. Ein Eintrag pro erfasster Stelle, auch für aussortierte.

Der Stand jeder Stelle liegt im Stellenordner: `job.json` (Fakten, offene Fragen), `application-manifest.json` (Status, Zeitpunkte, `history`), `DROPPED.txt` (Grund und Datum) und die Lage des Ordners. Das Ledger wird daraus abgeleitet:

```bash
python3 tools/build_mappe.py ledger sync profile/<name>
```

- Der Befehl ist idempotent. Fehlt `ledger.json` oder ist sie veraltet, stellt er sie vollständig wieder her.
- `application`, `status`, `mark-sent`, `drop`, `restore` und `stats` gleichen das Ledger selbst ab. `ledger sync` braucht es nur nach Handarbeit an den Ordnern (neue Erfassung, geänderte `job.json`).
- Von Hand wird im Ledger nur `notes` gepflegt; der Abgleich übernimmt das Feld aus dem vorhandenen Eintrag. Alles andere überschreibt er.
- Einträge ohne Stellenordner bleiben stehen und werden als Warnung gemeldet.

Felder je Eintrag:

- `id` (Referenznummer), `reference_number`, `company`, `title`, `occupation`, `type`
- `folder` (relativ zum Profilordner), `search_city`, `rank`
- `status`, `created_at`, `deadline`, `html_approved_at`, `pdf_exported_at`, `sent_at`, `dropped_at`, `drop_reason`
- `channel` (`email`, `post`, `portal`, `unknown`): Bewerbungsweg laut `job.json`, nach `mark-sent` der genutzte Kanal
- `open_blocking`: Zahl der offenen blockierenden Fragen (`references/job-search.md`, Offene Punkte)
- `contact` (Name, E-Mail, Telefon), `application_email`, `source_url`
- `history[]` mit Datum, Status und Notiz: `captured` aus `source.retrieved_at`, die weiteren Schritte aus `history` im Manifest, `dropped` aus `DROPPED.txt`

## Übersicht

```bash
python3 tools/build_mappe.py status profile/<name>
```

Gleicht das Ledger ab und zeigt eine Zeile pro Stelle: Status, Frist (`!` = abgelaufen), Bewerbungsweg, offene blockierende Fragen, Ordner, nächster Schritt. Aktive Stellen stehen nach Frist sortiert oben, aussortierte mit Grund unten. Darunter folgen die Summen und die Hinweise der Duplikatprüfung. Mit einem Stellenordner statt des Profils zeigt der Befehl nur diese Zeile.

Mit dieser Übersicht beginnt jede Sitzung, die an Bewerbungen weiterarbeitet. Sie ersetzt Notizen über den Stand.

## Duplikate

Die Regel steht nur hier; `tools/build_mappe.py check-duplicate` setzt sie um.

Verglichen werden vier Merkmale aus `job.json`:

- **Firma:** `company` ohne Klammerzusätze und Rechtsform (GmbH, AG, SE, KG, Co., e.V. …), als Slug
- **Beruf:** `occupation` als Slug
- **Arbeitsort:** `locations[].city` ohne Zusatz nach Komma oder Klammer („Musterstadt, Donau“ → `musterstadt`); bei mehreren Orten genügt ein gemeinsamer
- **Startjahr:** erste Jahreszahl in `start`, sonst in `start_text`, sonst im Titel

| Ergebnis | Bedingung | Folge |
|---|---|---|
| `same_posting` | gleiche Referenznummer, oder alle vier Merkmale gleich | Exit-Code 3: den Nutzer fragen |
| `same_role_other_site` | Firma, Beruf und Startjahr gleich, anderer Arbeitsort | Hinweis, Exit-Code 0; beide Stellen bleiben |
| `same_employer_other_role` | gleiche Firma, anderer Beruf oder anderes Startjahr | Hinweis, Exit-Code 0 |

```bash
python3 tools/build_mappe.py check-duplicate <stellenordner>
```

- Der Befehl vergleicht mit allen Stellenordnern des Profils, auch unter `sent/` und `dropped/`. Er läuft nach dem Erfassen jeder neuen Stelle und vor dem Schreiben.
- Vor dem Anlegen eines Ordners reicht die Suche nach Referenznummer (aus der Treffer-URL `/jobsuche/jobdetail/<referenznummer>`) und Firma in `ledger.json`.
- Bei `same_posting` bleibt die Fassung mit vollständigem BA-Text, die beim Arbeitgeber noch offen ist; die andere wird mit `drop` aussortiert. Unterscheiden sich die Anzeigen im Schwerpunkt, entscheidet der Nutzer.
- Die Entscheidung des Nutzers steht in beiden `job.json` unter `duplicate_decision` (`reference_numbers` der anderen Stelle, `decision`, `decided_at`). Danach meldet der Befehl das Paar als entschieden, mit Exit-Code 0.
- Ist die andere Stelle schon aussortiert, ist der Treffer nur ein Hinweis. Die gleiche Referenznummer ergibt immer Exit-Code 3.

## Aussortieren

Stellen, die nicht weiterverfolgt werden (Filter in `references/job-search.md`, Duplikat, Entscheidung des Nutzers), werden nie gelöscht:

```bash
python3 tools/build_mappe.py drop <stellenordner> --reason "<Grund>" [--date JJJJ-MM-TT]
python3 tools/build_mappe.py restore <stellenordner unter dropped/>
```

`drop` verschiebt den Ordner nach `applications/dropped/<typ>/<beruf>/<suchort>/<NN-…>/`, schreibt `DROPPED.txt` (erste Zeile der Grund, zweite Zeile `Datum: JJJJ-MM-TT`) und setzt im Ledger `dropped` mit `drop_reason`. `restore` macht das rückgängig. Aussortierte Stellen lassen sich nicht bauen oder im Status ändern; `validate` prüft bei ihnen nur das Schema. Gesendete Bewerbungen werden nicht aussortiert, sondern mit `status <ordner> withdrawn` zurückgezogen.

## Versandablage

Der einzige Weg zum Status `sent`, nur auf Bestätigung des Nutzers („ist raus“, „habe ich abgeschickt“):

```bash
python3 tools/build_mappe.py mark-sent <stellenordner> --channel email [--date JJJJ-MM-TT]
```

Der Ordner wird nach `applications/sent/<typ>/<beruf>/<suchort>/<NN-…>/` verschoben, leere Elternordner werden entfernt, Manifest und Ledger bekommen `sent`, Datum und Kanal.

## Statistik

```bash
python3 tools/build_mappe.py stats profile/<name>
```

Gibt die Anzahl der Stellen nach Status, Typ, Anlagemonat, Versandmonat und Kanal aus. So berichtet der Agent:

> Du hast 6 Bewerbungen: 2 Entwürfe, 1 freigegeben, 3 gesendet (alle per E-Mail, im November). Eine Einladung zum Gespräch, noch keine Absage.

Für Fragen, die das Skript nicht abdeckt (z. B. „Welche Firmen haben noch nicht geantwortet?“), liest der Agent `ledger.json` direkt und filtert nach `status` und `sent_at`.
