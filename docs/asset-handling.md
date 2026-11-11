# Nachweise und Bilder

## Grundsatz

Zeugnisse und Zertifikate sind echte, vom Nutzer bereitgestellte Dokumente. Der Agent erfindet keine Nachweise und ersetzt keine fehlenden Scans durch dekorative Platzhalter.

## Eingang

Der Nutzer legt Dateien unter `profile/import/` ab oder übergibt sie im Harness. Unterstützt werden:

- PDF
- DOCX (nur als Quelle für Lebenslauf und eingebettete Bilder; wird nicht selbst in die Mappe eingebunden)
- PNG
- JPEG
- WebP

Eingebettete Bilder aus DOCX werden einzeln geprüft. Ein Vorlagen-Platzhalter (z. B. „Foto einfügen“) ist kein Foto.

Der Agent ordnet jede Datei einem Nachweis zu und prüft:

- Ist der Inhalt lesbar?
- Gehört die Datei zum Nutzer?
- Ist das Ausstellungsdatum erkennbar?
- Handelt es sich um ein Zertifikat oder ein Zeugnis?
- Darf die Datei in der Mappe erscheinen?

## Übernahme in die Bewerbung

Für jede Bewerbung werden nur die benötigten Dateien nach `applications/<unternehmen>-<beruf>/assets/` kopiert. Der Originalname bleibt in `application-manifest.json` erhalten.

### Bilder

Bilder werden als echte `<img>`-Elemente in einer Nachweiskarte angezeigt. Das Seitenverhältnis bleibt erhalten. Bei sehr großen Scans wird eine lesbare Vorschau erzeugt; das Original bleibt daneben erhalten.

### PDFs

PDFs werden nicht als Screenshot maskiert. Zulässig sind:

- ein eingebettetes `<object>` für die Browserfassung,
- eine verlinkte Dokumentkarte mit Titel, Aussteller und Datum,
- ein separates Anhangsverzeichnis für den Versand.

Vor dem PDF-Export prüft der Agent, ob der Browser eingebettete PDFs zuverlässig übernimmt. Wenn nicht, wird eine gerenderte Vorschau verwendet und das Original separat beigelegt.

## Seitenaufbau

### Mehrere Nachweise

- ein Nachweis pro Seite im Regelfall,
- zwei Nachweise nebeneinander mit `.evidence-grid.is-pair`, wenn beide lesbar bleiben,
- mehr Nachweise auf Folgeseiten mit Titel „Fortsetzung“ und fortlaufender Seitenzahl,
- jede Seite und jedes Asset wird im Manifest unter `pages` bzw. `assets` erfasst.

`certificate` erscheint unter Zertifikate, `school_report` und `work_reference` unter Zeugnisse.

### Zertifikate

- Karten mit Titel, Aussteller, Datum
- Vorschaubild oder PDF-Link
- optional eine kurze Einordnung, warum der Nachweis relevant ist

### Zeugnisse

- Schulzeugnisse
- Praktikums- und Arbeitszeugnisse
- Bescheinigungen
- jeweils mit Original oder klarer Kennzeichnung „liegt noch nicht vor“

## Datenschutz

- Keine Nachweise in Git.
- Keine Uploads in externe Dienste.
- Keine Weitergabe an die Jobsuche.
- Vor dem Versand prüft der Nutzer, ob sensible Angaben wie Geburtsdatum, Adresse oder Gesundheitsdaten sichtbar sein sollen.
