# Produktbrief

## Ziel

Ein lokales, agent-agnostisches Repository, das aus dem Profil des Nutzers und genau einer Ausbildungsanzeige der Bundesagentur für Arbeit eine vollständige deutsche Bewerbungsmappe baut.

Die Mappe ist zuerst eine sehr gute HTML-Datei. Erst nach inhaltlicher und visueller Freigabe wird sie über die PDF-Funktion des Browsers als A4-PDF exportiert. Sie ist für den Versand per E-Mail gedacht; es wird nichts ausgedruckt oder handschriftlich unterschrieben.

## Nutzer

Eine Person, die eine Ausbildung sucht und den Workflow in ihrem eigenen Harness startet. Das Repository ist kein SaaS und keine Mehrbenutzerplattform.

Ein frischer Clone enthält keine Profil-, Job- oder Bewerbungsdaten. Der Nutzer öffnet das Repo mit Claude, Codex oder einem anderen Harness und startet den Skill. Der Agent beginnt mit dem Profilinterview. Eine gemeinsame Basisvorlage wird einmal gestaltet; Stencil kann dafür als visuelles Markierungswerkzeug dienen.

## Ein erfolgreicher Durchlauf

1. Der Nutzer startet den Skill in einem frischen Clone.
2. Der Agent gleicht vorhandene Unterlagen ab, führt das Profilinterview für Lücken und speichert `profile/master-profile.json` (primär, schemavalidiert) sowie `profile/master-profile.md` (lesbare Fassung).
3. Der Agent sucht im Browser eine Ausbildungsstelle bei der Bundesagentur für Arbeit.
4. Der Nutzer wählt genau eine Stelle.
5. Der Agent liest die Anzeige und belegt Anforderungen, Kontakt und Bewerbungsweg.
6. Der Agent erstellt eine Bewerbungsmappe mit sechs Abschnitten als HTML.
7. Der Nutzer prüft und gibt die HTML-Fassung frei.
8. Der Agent exportiert per Browser ein PDF sowie Kontaktübersicht und E-Mail-Entwurf.

## Sechs Seiten

1. **Deckblatt** – gestaltete Titelseite mit Inhaltsangabe, großem optionalen Foto, Name, Ausbildungsziel, Kontakt und Kurzprofil; stabil, ohne Unternehmensname
2. **Anschreiben** – pro Stelle neu: Warum passt der Bewerber fachlich und persönlich zu dieser Ausbildung und diesem Unternehmen?
3. **Lebenslauf** – stabil, aus dem Master-Profil
4. **Motivationsschreiben** – pro Stelle neu: Warum will der Bewerber diesen Weg gehen, und warum beschäftigt ihn das Thema?
5. **Zertifikate** – stabile, vom Nutzer bereitgestellte Nachweise als Bild oder PDF
6. **Zeugnisse** – stabile, vom Nutzer bereitgestellte Zeugnisse als Bild oder PDF

**Variabel:** Anschreiben und Motivationsschreiben.  
**Stabil:** Deckblatt, Lebenslauf, Zertifikate, Zeugnisse.

## Inhalte der variablen Seiten

### Anschreiben

Beantwortet:

- Warum sollte das Unternehmen den Bewerber auswählen?
- Welche belegbaren Fähigkeiten und Erfahrungen passen zur Ausbildung?
- Welche konkreten Beispiele zeigen die Eignung?
- Welche Lücke bleibt ehrlich benannt?

Keine Nacherzählung der gesamten Biografie.

### Motivationsschreiben

Beantwortet:

- Warum will der Bewerber diesen Beruf erlernen?
- Woher kommt das Interesse?
- Welche Erfahrung hat es verstärkt?
- Warum beschäftigt den Bewerber das Thema auch außerhalb der Pflicht?
- Warum diese Ausbildung bei diesem Unternehmen?

Persönlicher und erzählerischer als das Anschreiben. Projektbilder sind optional und nur mit echten, vom Nutzer bereitgestellten Bildern zulässig. Stencil kann für visuelle Markierungen der HTML-Vorlage und einzelner Unternehmensmappen genutzt werden.

## Umfang der ersten Version

- Deutsch
- nur Ausbildung
- nur Bundesagentur für Arbeit
- eine Stelle pro Durchlauf
- Profilinterview ab leerem Profil
- optionaler Import vorhandener Unterlagen
- HTML zuerst, PDF per Browser-Export
- Skill plus lokale Dokumentation, Schemas und HTML-Vorlage
- keine CLI, keine Scraping-Skripte, kein eigener PDF-Renderer
- agent-agnostisch: T3 Code, Codex, Claude Code oder ein anderer Harness mit Datei- und Browserzugriff

## Kontakt

Wenn die Anzeige keinen Ansprechpartner nennt, sucht der Agent auf der öffentlichen Unternehmensseite nach einem passenden Kontakt. Findet er keinen verlässlichen persönlichen Kontakt, nutzt er eine neutrale Anrede wie „Sehr geehrte Damen und Herren“ und dokumentiert die Unsicherheit in `contact-summary.md`.

## Nicht enthalten

- automatisches Absenden
- automatisches Ausfüllen von Bewerbungsportalen
- Bewerbungen für reguläre Jobs
- Batch-Bewerbungen
- Datenbank oder Web-App
- erfundene Qualifikationen, Kontakte oder Nachweise
- externe Stockbilder als angebliche Projekte
- Demo-Profil oder Demo-Bewerbung im Repository
- Stencil als Voraussetzung

## Definition of Done

Eine Bewerbung ist fertig, wenn:

- alle sechs Abschnitte vorhanden sind,
- Anschreiben und Motivationsschreiben unterschiedliche Aufgaben erfüllen,
- jede Aussage durch Profil oder Stellenanzeige belegt ist,
- die Nachweise als echte Scans eingebunden oder klar als fehlend markiert sind,
- die HTML-Fassung im Browser geprüft und freigegeben ist,
- das PDF saubere A4-Seiten ohne Überlauf hat (sechs im Regelfall, Folgeseiten nur für weitere Nachweise),
- Kontaktübersicht und E-Mail-Entwurf vorliegen,
- nichts gesendet wurde.
