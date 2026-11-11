---
name: bewerbungshelfer
description: Führt ein Profilinterview für deutsche Ausbildungsbewerbungen, sucht genau eine Stelle bei der Bundesagentur für Arbeit, erstellt eine sechsseitige Bewerbungsmappe als HTML und bereitet nach Freigabe PDF, Kontaktübersicht und E-Mail-Entwurf vor.
metadata:
  short-description: Deutsche Ausbildungsbewerbung als sechsseitige Mappe
---

# Bewerbungshelfer

## Ergebnis

Für **genau eine Ausbildungsstelle** entsteht eine sechsseitige Bewerbungsmappe:

1. Deckblatt
2. Anschreiben
3. Lebenslauf
4. Motivationsschreiben
5. Zertifikate
6. Zeugnisse

Anschreiben und Motivationsschreiben werden pro Stelle neu geschrieben. Die übrigen vier Teile kommen aus dem stabilen Master-Profil und den importierten Nachweisen.

Nach der HTML-Freigabe entstehen ein A4-PDF per Browser-Export, eine Kontaktübersicht und ein E-Mail-Entwurf. Die Mappe ist für den E-Mail-Versand gedacht, nicht zum Ausdrucken und handschriftlichen Unterschreiben. Es wird nichts gesendet.

## Zuerst lesen

Im Repository:

1. `AGENTS.md`
2. `docs/workflow.md`
3. `docs/bewerbungsmappe.md`

Aus diesem Skill nur die benötigte Referenz:

- Profil oder Fragebogen: `references/interview.md`
- Profilstruktur und Datenvertrag: `references/profile-schema.md`
- Jobsuche und Unternehmensbelege: `references/job-search.md`
- Schreiben: `references/writing.md`
- Prüfung und Export: `references/qa-and-export.md`

Die Vorlage liegt unter `assets/bewerbungsmappe.html`. Wenn Stencil im Harness verfügbar ist, kann der Nutzer sie dort visuell markieren; HTML und Stencil sind dann gemeinsam die Quelle der Wahrheit. Ohne Stencil bleibt das HTML maßgeblich.

## Ablauf

### 0. Basisvorlage gestalten

Die gemeinsame Vorlage liegt unter `assets/bewerbungsmappe.html`. Wenn Stencil im Harness verfügbar ist, öffnet der Nutzer sie dort und markiert gewünschte Änderungen. Der Agent übernimmt freigegebene Markierungen ins HTML. Ohne Stencil prüfen Agent und Nutzer die Vorlage direkt im Browser.

Die Basisvorlage wird einmal gestaltet. Unternehmensspezifische Änderungen bleiben in der jeweiligen Bewerbung.

### 1. Profil aufnehmen und ergänzen

Prüfe `profile/master-profile.json` und `profile/master-profile.md`.

Wenn das Profil noch nicht bestätigt ist:

- lies vorhandene Dateien unter `profile/import/` vollständig und visuell,
- prüfe PDFs, DOCX und Bilder auch auf eingebettete Grafiken,
- fasse die erkannten Angaben mit Status `confirmed`, `inferred`, `open` oder `conflict` zusammen,
- frage nur nach fehlenden, defekten oder widersprüchlichen Angaben,
- speichere erst nach Bestätigung,
- validiere das JSON gegen `assets/schemas/profile.schema.json`.

Ein frischer Clone startet ohne Profil. Wenn der Nutzer vorhandene Unterlagen bereitstellt, sind sie der Ausgangspunkt; der Fragebogen ergänzt sie, statt sie zu wiederholen. Defekte Dateien, besonders ein leeres Bewerbungsfoto, werden ausdrücklich als offener Punkt gemeldet und nicht eingebunden.

### 2. Eine Stelle auswählen

Nutze den Browser des Harness und die öffentliche Bundesagentur-Jobsuche im Bereich **Ausbildung**.

Zeige eine kurze Auswahl mit Titel, Unternehmen, Ort, Entfernung, Beginn und Link. Der Nutzer wählt genau eine Stelle.

### 3. Stelle belegen

Lies die vollständige Anzeige. Erfasse die Pflichtfelder aus `references/job-search.md` in `job.json`.

Jede Anforderung und jeder Kontakt bekommt eine Quelle. Fehlt ein persönlicher Ansprechpartner, prüfe die öffentliche Unternehmensseite. Rate nichts.

### 4. Passung prüfen

Bewerte jede Anforderung gegen das Profil:

- `met`
- `partial`
- `not_met`
- `unknown`

Belege zusätzlich jede geplante Aussage über das Unternehmen mit Quelle und Datum. Nur belegte Stärken dürfen im Anschreiben stehen. Lücken werden nicht wegformuliert.

Das Anschreiben beantwortet, warum der Bewerber für die Ausbildung geeignet ist und sie wahrscheinlich erfolgreich abschließen wird. Das Motivationsschreiben beantwortet, warum er diesen Weg gehen will und warum ihn das Thema beschäftigt. Prüfe vor der Freigabe, dass beide Texte keine Hauptargumente, Anekdoten oder Projektgeschichten doppelt erzählen.

### 5. Mappe bauen

Kopiere die Vorlage nach:

```text
applications/<unternehmen>-<beruf>/bewerbungsmappe.html
```

Ersetze alle Platzhalter. Behalte die sechs Seiten, CSS-Klassen und PDF-Regeln. Wenn Stencil verfügbar ist, übernimm freigegebene visuelle Markierungen aus der Stencil-Fassung in das HTML. Prüfe jede generierte Aussage gegen Profil und Stellenanzeige; unbelegte Formulierungen werden entfernt, nicht geglättet.

Die freigegebenen Darstellungsregeln aus `profile.master-profile.json` gelten:

- Fußzeile nur mit Name
- kein Unternehmensname auf dem Deckblatt
- Fähigkeiten als Diagramme
- keine Timeline-Verbindungslinien
- Seitenzahlen ohne führende Nullen und ohne Gesamtseitenzahl

Schreibe Anschreiben und Motivationsschreiben nach `references/writing.md`. Binde echte Zertifikate und Zeugnisse aus `profile/import/` oder den bereitgestellten Dateien als lokale Assets ein. Fehlende Nachweise werden ausdrücklich markiert.

### 6. HTML prüfen und freigeben

Öffne die Mappe im Browser. Prüfe Inhalt, Reihenfolge, Kontaktdaten, Anrede und Nachweise.

Prüfe jede Fassung bei der richtigen Auflösung:

- Desktop: 1440 × 900 oder 1280 × 800
- Mobil: 390 × 844 und 375 × 812
- PDF: A4 mit 210 × 297 mm

Mobil, Desktop und A4 sind drei getrennte Abnahmeflächen. Eine schmale Desktopvorschau ist kein Ersatz für die Mobilansicht. Das responsive Bildschirmlayout ist nicht die Druckfassung.

Frage ausdrücklich:

> Ist diese HTML-Fassung inhaltlich und optisch freigegeben?

Ohne eindeutiges Ja kein PDF.

### 7. PDF und Versandvorbereitung

Nach der Freigabe:

- exportiere über den Browser ein A4-PDF,
- prüfe alle Seiten visuell,
- schreibe `contact-summary.md` nach `assets/templates/contact-summary.md`,
- schreibe `email-draft.md` nach `assets/templates/email-draft.md`.

Keine Bewerbung senden und kein Portal ausfüllen.

## Harte Regeln

- Deutsch
- nur Ausbildung
- nur Bundesagentur für Arbeit
- eine Stelle pro Durchlauf
- keine erfundenen Qualifikationen, Kontakte oder Nachweise
- keine unbelegten Aussagen
- keine externen Ressourcen ohne Freigabe
- keine Scraping- oder Rendering-Skripte anlegen
- keine persönlichen Daten committen
- kein PDF vor HTML-Freigabe
- kein automatisches Absenden
- bei fehlenden Fakten stoppen und fragen
- keine defekten oder fremden Bilder einbinden
- freigegebene Näherungen als `inferred` kennzeichnen
- Diagramme nur aus gespeicherten Niveaus erzeugen

## Ordner

```text
profile/
  import/
  assets/
  master-profile.json
  master-profile.md
applications/<unternehmen>-<beruf>/
  job.json
  application-manifest.json
  bewerbungsmappe.html
  bewerbungsmappe.pdf
  contact-summary.md
  email-draft.md
  assets/
```
