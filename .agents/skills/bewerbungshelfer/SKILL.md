---
name: bewerbungshelfer
description: Führt ein Profilinterview für deutsche Ausbildungsbewerbungen, sucht genau eine Stelle bei der Bundesagentur für Arbeit, erstellt eine Bewerbungsmappe mit sechs Abschnitten als HTML und bereitet nach Freigabe PDF, Kontaktübersicht und E-Mail-Entwurf vor.
metadata:
  short-description: Deutsche Ausbildungsbewerbung als Mappe mit sechs Abschnitten
---

# Bewerbungshelfer

## Ergebnis

Für **genau eine Ausbildungsstelle** entsteht eine Bewerbungsmappe mit sechs Abschnitten, im Regelfall sechs A4-Seiten:

1. Deckblatt
2. Anschreiben
3. Lebenslauf
4. Motivationsschreiben
5. Zertifikate
6. Zeugnisse

Folgeseiten sind nur für weitere Nachweise (höchstens zwei pro Seite) oder eine Lebenslauf-Fortsetzung erlaubt. Sie tragen denselben Abschnittstitel mit „Fortsetzung“ und eine fortlaufende Seitenzahl.

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

Die Basisvorlage wird **einmalig** gestaltet und enthält keine persönlichen Daten. Ist sie bereits freigegeben, beginnt jeder weitere Durchlauf direkt mit Schritt 1. Unternehmensspezifische Änderungen bleiben in der jeweiligen Bewerbung.

### 1. Profil aufnehmen und ergänzen

Prüfe `profile/master-profile.json` und `profile/master-profile.md`.

Wenn das Profil noch nicht bestätigt ist:

- lies vorhandene Dateien unter `profile/import/` vollständig und visuell,
- prüfe PDFs, DOCX und Bilder auch auf eingebettete Grafiken,
- fasse die erkannten Angaben mit Status `confirmed`, `inferred`, `open` oder `conflict` zusammen (in `field_status` bzw. `source_status`),
- frage nur nach fehlenden, defekten oder widersprüchlichen Angaben,
- speichere erst nach Bestätigung,
- validiere das JSON gegen `assets/schemas/profile.schema.json`.

Ein frischer Clone startet ohne Profil. Wenn der Nutzer vorhandene Unterlagen bereitstellt, sind sie der Ausgangspunkt; der Fragebogen ergänzt sie, statt sie zu wiederholen. Defekte Dateien, besonders ein leeres Bewerbungsfoto, werden ausdrücklich als offener Punkt gemeldet und nicht eingebunden.

### 2. Eine Stelle auswählen

Nutze den Browser des Harness und die öffentliche Bundesagentur-Jobsuche im Bereich **Ausbildung**. An die Jobsuche gehen nur Suchbegriff, Ort oder PLZ und Umkreis, keine weiteren Profildaten.

Zeige eine kurze Auswahl mit Titel, Unternehmen, Ort, Entfernung, Beginn und Link. Der Nutzer wählt genau eine Stelle.

### 3. Stelle belegen

Lies die vollständige Anzeige. Erfasse die Pflichtfelder aus `references/job-search.md` in `job.json` und validiere gegen `assets/schemas/job.schema.json`. Unternehmensaussagen für die Briefe kommen nach `company_facts` (Aussage, wörtlicher Beleg, Quell-URL, Abrufdatum).

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

Lege dort `application-manifest.json` nach `assets/templates/application-manifest.json` mit Status `draft` an und trage Seiten (`pages`) und Assets ein.

Ersetze alle Platzhalter. Behalte die sechs Abschnitte, CSS-Klassen und PDF-Regeln. Das Foto erscheint nur, wenn `person.photo.valid` und `consent` true sind; sonst bleibt der Fotoblock weg. Fähigkeitsbalken setzen nur die Klasse `s<scale>` aus dem Profil. Wenn Stencil verfügbar ist, übernimm freigegebene visuelle Markierungen aus der Stencil-Fassung in das HTML. Prüfe jede generierte Aussage gegen Profil und Stellenanzeige; unbelegte Formulierungen werden entfernt, nicht geglättet.

Fehlt das Foto, entfällt der Fotoblock ersatzlos. Läuft der Lebenslauf über, entsteht eine Folgeseite nach dem Kommentar in der Vorlage; Inhaltsangabe und Seitenzahlen werden angepasst. Für Bewerbungen ohne Foto oder Unterschrift wird nichts ersetzt oder generiert.

Die freigegebenen Darstellungsregeln aus `presentation` in `profile/master-profile.json` gelten:

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

Prüfe in der A4-Fassung jede Seite auf Überlauf (`references/qa-and-export.md`, Abschnitt Überlauf). Abgeschnittener Inhalt blockiert die Freigabe. Trage das Ergebnis unter `validation` im Manifest ein.

Mobil, Desktop und A4 sind drei getrennte Abnahmeflächen. Eine schmale Desktopvorschau ist kein Ersatz für die Mobilansicht. Das responsive Bildschirmlayout ist nicht die Druckfassung.

Frage ausdrücklich:

> Ist diese HTML-Fassung inhaltlich und optisch freigegeben?

Ohne eindeutiges Ja kein PDF. Nach dem Ja: Manifest auf `html_approved` mit `approved_at` setzen.

### 7. PDF und Versandvorbereitung

Nach der Freigabe:

- exportiere über den Browser ein A4-PDF,
- prüfe alle Seiten visuell,
- schreibe `contact-summary.md` nach `assets/templates/contact-summary.md`,
- schreibe `email-draft.md` nach `assets/templates/email-draft.md`,
- setze das Manifest nach geprüftem PDF auf `pdf_exported` (`pdf`, `pdf_exported_at`) und nach Kontaktübersicht und E-Mail-Entwurf auf `ready_to_send`. Das heißt nicht, dass gesendet wurde.

Keine Bewerbung senden und kein Portal ausfüllen.

## Harte Regeln

- Deutsch
- nur Ausbildung
- nur Bundesagentur für Arbeit
- eine Stelle pro Durchlauf
- keine erfundenen Qualifikationen, Kontakte oder Nachweise
- keine unbelegten Aussagen
- keine externen Ressourcen ohne Freigabe
- keine Scraping- oder Rendering-Skripte anlegen (ein direkter Headless-Browser-Aufruf für die A4-Vorschau ist erlaubt)
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
