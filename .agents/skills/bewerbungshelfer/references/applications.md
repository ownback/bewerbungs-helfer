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
    apprenticeships/ jobs/ internships/
    sent/apprenticeships/ sent/jobs/ sent/internships/
```

## Stellenordner

```text
applications/<typ>/<beruf-slug>/<suchort-slug>/<NN>-<ort-slug>-<firma-slug>/
  job_information/
    ba_scrape.md
    job.json
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
```

- `<typ>`: `apprenticeships`, `jobs` oder `internships` (`job.json` → `type`).
- `<beruf-slug>`: gesuchter Beruf, z. B. `fachinformatiker-systemintegration`.
- `<suchort-slug>`: Ort, in dem gesucht wurde, z. B. `musterstadt`.
- `<NN>`: zweistelliger Rang nach Entfernung vom Suchort, `01` = am nächsten.
- `<ort-slug>`: Arbeitsort der Stelle (kann der Suchort sein).
- `<firma-slug>`: kurzer Firmenname ohne Rechtsform, z. B. `musterfirma` (aus „Musterfirma GmbH & Co. KG“).

Slugs: Kleinbuchstaben, ASCII, `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, alles andere als Bindestrich, keine doppelten oder randständigen Bindestriche.

Ränge: Die Stellen eines Durchlaufs werden nach Entfernung sortiert. Liegen im Ordner `<beruf>/<suchort>/` schon Stellen, zählen neue Ränge ab der höchsten vorhandenen Nummer weiter (in Entfernungsreihenfolge). Bestehende Ordner werden nie umbenannt, weil Ledger und Manifest ihren Pfad speichern.

Generierte Dateinamen enthalten den Profilnamen, z. B. `bewerbungsmappe - max.mustermann.html`.

## Ledger

`applications/ledger.json` nach `assets/schemas/ledger.schema.json`, Startpunkt `assets/templates/ledger.json`. Ein Eintrag pro Bewerbung:

- `id` (Referenznummer), `reference_number`, `company`, `title`, `occupation`, `type`
- `folder` (relativ zum Profilordner), `search_city`, `rank`
- `status`, `created_at`, `html_approved_at`, `pdf_exported_at`, `sent_at`
- `channel` (`email`, `post`, `portal`), `contact` (Name, E-Mail, Telefon), `application_email`, `source_url`
- `history[]` mit Datum, Status und Notiz

`tools/build_mappe.py application` legt den Eintrag an bzw. aktualisiert ihn; `status` und `mark-sent` pflegen Status, Daten und Verlauf. Von Hand nur `notes` ergänzen. `sent` kann nur `mark-sent` setzen (Ordner und Ledger bleiben so konsistent).

### Duplikate

Vor dem Anlegen eines Stellenordners und vor jeder Generierung prüfen:

```bash
python3 tools/build_mappe.py check-duplicate <stellenordner>
```

Duplikat = gleiche Referenznummer **oder** gleiche Firma und gleicher Titel. Exit-Code 3 bei Treffer. Dann den Nutzer warnen (mit Status und Ordner des vorhandenen Eintrags) und nur nach ausdrücklichem Ja weitermachen. Vor dem Anlegen des Ordners reicht ein Blick in `ledger.json` (Referenznummer aus der Treffer-URL `/jobsuche/jobdetail/<referenznummer>`).

## Status

| Status | Bedeutung | gesetzt durch |
|---|---|---|
| `draft` | Mappe gebaut, nicht freigegeben | `application` |
| `html_approved` | Nutzer hat die HTML-Fassung ausdrücklich freigegeben | `status … html_approved` |
| `pdf_exported` | finales PDF erzeugt und geprüft | `application --pdf` |
| `sent` | Nutzer hat bestätigt, dass er gesendet hat | nur `mark-sent --channel …` |
| `interview`, `offer`, `rejected`, `withdrawn` | Rückmeldung nach dem Versand | `status …` |

`status <ordner> sent` wird abgelehnt (Fehlermeldung mit Verweis auf `mark-sent`): sonst stünde das Ledger auf „gesendet“, während der Ordner noch unter den aktiven Bewerbungen läge. `status <ordner> html_approved` warnt, wenn bei Bewerbungsweg `email` der Entwurf `application/email.md` noch fehlt; das PDF gibt es erst mit Entwurf (`references/qa-and-export.md`).

Manifest und Ledger tragen denselben Status. Ändert sich eine freigegebene Mappe beim Neubau, fällt sie auf `draft` zurück.

## Versandablage

Der einzige Weg zum Status `sent`, nur auf Bestätigung des Nutzers („ist raus“, „habe ich abgeschickt“):

```bash
python3 tools/build_mappe.py mark-sent <stellenordner> --channel email [--date JJJJ-MM-TT]
```

Der Ordner wird nach `applications/sent/<typ>/<beruf>/<suchort>/<NN-…>/` verschoben, leere Elternordner werden entfernt, Ledger und Manifest bekommen `sent`, Datum und Kanal. Verschieben und Ledger-Eintrag sind ein Vorgang; `status … sent` gibt es nicht.

## Statistik

```bash
python3 tools/build_mappe.py stats profile/<name>
```

Gibt die Anzahl der Bewerbungen nach Status, Typ, Anlagemonat, Versandmonat und Kanal aus. So berichtet der Agent:

> Du hast 6 Bewerbungen: 2 Entwürfe, 1 freigegeben, 3 gesendet (alle per E-Mail, im November). Eine Einladung zum Gespräch, noch keine Absage.

Für Fragen, die das Skript nicht abdeckt (z. B. „Welche Firmen haben noch nicht geantwortet?“), liest der Agent `ledger.json` direkt und filtert nach `status` und `sent_at`.
