# Skill statt Skripte

Die erste Version ist ein Agent-Workflow, kein Automatisierungsprogramm.

## Warum

Die schwierigen Entscheidungen sind nicht mechanisch:

- ein unvollständiges Profil sinnvoll ergänzen
- eine Stellenanzeige interpretieren
- Anforderungen mit belegbaren Erfahrungen abgleichen
- Anschreiben und Motivationsschreiben unterschiedlich erzählen
- fehlende Nachweise erkennen
- vor dem Versand stoppen

Dafür ist ein Agent mit Browser- und Dateizugriff geeignet. Ein starres Skript würde diese Entscheidungen nur hinter Prompts verstecken.

## Was das Repo besitzt

- Workflow
- Fragebogen
- Datenverträge im Skill
- HTML-Vorlage
- Designregeln
- Prüflisten
- leere Vorlagen für Profil, Job und Versand

## Was lokal bleibt

- Master-Profil
- importierte Zeugnisse und Zertifikate
- Bewerbungsmappen
- PDFs
- Kontaktübersichten
- E-Mail-Entwürfe

## Wann Skripte sinnvoll wären

Erst nach mehreren echten Durchläufen, wenn ein konkreter wiederholbarer Engpass sichtbar wird. Beispiele:

- wiederholtes Validieren des JSON-Schemas
- konsistentes Kopieren von Assets
- automatisches Prüfen auf offene Platzhalter

Auch dann bliebe der Agent für Inhalt und Entscheidungen verantwortlich.

## Entscheidung

Keine CLI, keine Scraping-Skripte, kein eigener PDF-Renderer in der ersten Version.
