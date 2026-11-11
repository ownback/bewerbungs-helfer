# Datenverträge

Die Schemas liegen im Skill:

- `.agents/skills/bewerbungshelfer/assets/schemas/profile.schema.json`
- `.agents/skills/bewerbungshelfer/assets/schemas/job.schema.json`
- `.agents/skills/bewerbungshelfer/assets/schemas/application-manifest.schema.json`

Sie sind Dokumentation und Prüfhilfe, keine Laufzeitabhängigkeit. Ein Agent kann die Dateien lesen, muss aber keinen Validator installieren.

## Warum Schemas?

- Sie verhindern, dass Unternehmen, Kontakt und Bewerbungsweg in Prosa verloren gehen.
- Sie trennen belegte Angaben von offenen Fragen und freigegebenen Näherungen.
- Sie unterscheiden Praktikum, Anstellung, Schulbildung und Projekt.
- Sie halten Zeiträume und ihre Präzision fest.
- Sie machen sichtbar, welche Seiten stabil und welche variabel sind.
- Sie erlauben später eine deterministische Prüfung, ohne den Workflow jetzt zu verbauen.

## Profil

Das Profil enthält:

- `confirmed`: vom Nutzer bestätigte Angabe
- `inferred`: vom Nutzer freigegebene Näherung
- `open`: fehlende oder defekte Angabe
- `conflict`: widersprüchliche Angabe

Offene Punkte haben eine Auswirkung:

- `blocking`: Workflow stoppt
- `non_blocking`: Ausgabe kann weitergehen
- `research_needed`: öffentliche Recherche erforderlich

## Stelle

`job.json` trennt:

- Anforderungen aus der Anzeige
- Unternehmensaussagen mit Quelle
- persönlichen und allgemeinen Kontakt
- Bewerbungsweg
- offene Punkte mit Auswirkung

## Status der Mappe

- `draft`: HTML wird gebaut
- `html_approved`: Nutzer hat Inhalt und Layout freigegeben
- `pdf_exported`: PDF wurde exportiert und geprüft
- `ready_to_send`: Kontaktübersicht und E-Mail-Entwurf sind fertig

`ready_to_send` bedeutet nicht, dass gesendet wurde.
