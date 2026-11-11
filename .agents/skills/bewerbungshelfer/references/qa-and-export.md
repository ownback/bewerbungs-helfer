# Prüfung und Export

## Vor der HTML-Freigabe

### Profil

- [ ] `profile/master-profile.json` ist gegen `assets/schemas/profile.schema.json` gültig
- [ ] `job.json` ist gegen `assets/schemas/job.schema.json` gültig und hat mindestens einen `company_facts`-Eintrag
- [ ] `application-manifest.json` ist gegen sein Schema gültig
- [ ] Profil ist ausdrücklich bestätigt
- [ ] alle blockierenden offenen Punkte sind geklärt
- [ ] alle Stationen sind als Praktikum, Anstellung, Schulbildung oder Projekt klassifiziert
- [ ] Jahres- und Monatsangaben sind plausibel
- [ ] freigegebene Näherungen sind als `inferred` gespeichert
- [ ] Foto ist gültig, korrekt zugeordnet und freigegeben – oder der Fotoblock fehlt ganz (kein leerer Rahmen)

### Inhalt

- [ ] genau eine Stelle
- [ ] Unternehmen und Titel stimmen mit der Quelle überein
- [ ] Ansprechpartner belegt oder bewusst neutral
- [ ] keine erfundenen Qualifikationen
- [ ] keine offenen Platzhalter
- [ ] jede Unternehmensaussage ist belegt
- [ ] Anschreiben zeigt Eignung
- [ ] Motivationsschreiben zeigt persönlichen Antrieb
- [ ] keine Wiederholung der Hauptargumente zwischen den Schreiben
- [ ] Frist und Bewerbungsweg stimmen
- [ ] Kontaktdaten auf allen Seiten identisch

### Seiten

- [ ] Deckblatt
- [ ] Anschreiben
- [ ] Lebenslauf
- [ ] Motivationsschreiben
- [ ] Zertifikate
- [ ] Zeugnisse
- [ ] jede Seite beginnt auf einer neuen A4-Seite
- [ ] keine einsame Zeile
- [ ] nichts abgeschnitten oder über den Rand (Überlaufprüfung unten)
- [ ] Folgeseiten nur für weitere Nachweise oder Lebenslauf-Fortsetzung, Inhaltsangabe nennt die Startseiten
- [ ] Nachweise lesbar
- [ ] keine kaputten Bildsymbole oder Alternativtexte in der A4-Fassung
- [ ] langer Name bricht nicht in die Sidebar oder über den Satzspiegel
- [ ] Seitenzahlen ohne führende Nullen und ohne Gesamtseitenzahl
- [ ] keine vertikale Dekorlinie
- [ ] Fußzeile enthält nur den Namen
- [ ] Unternehmensname steht nicht auf dem Deckblatt
- [ ] Timeline hat keine Verbindungslinien
- [ ] Fähigkeiten erscheinen als Diagramme mit gespeicherten Niveaus
- [ ] Icons sind vorhanden, konsistent und optisch zentriert
- [ ] Desktop-Vorschau bei 1440 × 900 oder 1280 × 800 geprüft
- [ ] Mobil-Vorschau bei 390 × 844 und 375 × 812 ohne horizontalen Überlauf geprüft
- [ ] Desktop-, Mobil- und A4-Fassung getrennt beurteilt; keine Vorschaubreite als Ersatz für eine andere verwendet

### Überlauf

Jede `.page` hat eine feste A4-Höhe mit `overflow: hidden`. Zu langer Inhalt verschwindet sonst still. In der Browser-Konsole bei aktivierter Druckemulation (oder in der A4-Vorschau) prüfen:

```js
[...document.querySelectorAll('.page')].map((p, i) => {
  const over = p.scrollHeight > p.clientHeight + 1 || p.scrollWidth > p.clientWidth + 1;
  if (over) p.setAttribute('data-overflow', '');
  return over ? i + 1 : null;
}).filter(Boolean)
```

Das Ergebnis muss `[]` sein. Zusätzlich die Seitenbilder ansehen: Elemente, die innerhalb der Seite aus ihrem Block ragen (z. B. ein langer Name in die Sidebar), erkennt die Abfrage nicht. Ergebnis unter `validation.overflow_pages` im Manifest eintragen.

### A4-Vorschau

Wenn die Druckvorschau des Harness-Browsers nicht nutzbar ist, darf die A4-Fassung mit einem direkten Headless-Aufruf gerendert werden, z. B. `chromium --headless --no-pdf-header-footer --print-to-pdf=<vorschau.pdf> <bewerbungsmappe.html>`, und die Seiten als Bilder geprüft werden. Dabei kein Skript im Repository anlegen. Die Vorschau ist nicht der finale Export und liegt außerhalb des Repos oder im gitignorierten Bewerbungsordner.

### Druck

- [ ] `@page` ist A4
- [ ] keine externen Fonts oder Bilder
- [ ] Links als Text lesbar
- [ ] Hintergründe druckbar
- [ ] Kontrast ausreichend

## Freigabe

Prüfe die HTML-Fassung auf unbelegte Aussagen, erfundene Details, falsche Unternehmensangaben und Platzhalter. Entferne oder korrigiere sie. Prüfe das responsive Bildschirmlayout mindestens auf Desktop- und Mobilbreite. Zeige die Fassung im Browser und frage:

> Ist diese HTML-Fassung inhaltlich und optisch freigegeben? Erst danach erzeuge ich das PDF.

Das Bildschirmlayout ersetzt nicht die Prüfung der festen A4-Fassung. Ohne eindeutiges Ja kein PDF.

## PDF

Browser-PDF-Export (nicht ausdrucken):

- Ziel: PDF
- Papier: A4
- Hintergrundgrafiken: an
- Kopf- und Fußzeile: aus
- Maßstab: 100 %

Exportieren als:

```text
applications/<unternehmen>-<beruf>/bewerbungsmappe.pdf
```

## PDF prüfen

- [ ] sechs Abschnitte, Seitenzahl wie im Manifest unter `pages`
- [ ] keine leeren Seiten
- [ ] keine abgeschnittenen Zeilen
- [ ] Text auswählbar
- [ ] Kontaktdaten lesbar
- [ ] Bilder scharf
- [ ] Reihenfolge korrekt

## Kontaktübersicht

`contact-summary.md` wird aus `assets/templates/contact-summary.md` erstellt und enthält:

- Unternehmen
- Stellenbezeichnung
- Quelle
- Ansprechpartner
- Rolle oder Abteilung
- E-Mail
- Telefon
- Bewerbungsweg
- Frist
- offene Fragen
- fehlende Unterlagen

## E-Mail-Entwurf

`email-draft.md` wird aus `assets/templates/email-draft.md` erstellt und enthält:

- Empfänger
- Betreff
- kurzer Text
- Anhänge
- Hinweis: Entwurf, nicht gesendet

Keine Anhänge nennen, die nicht existieren.

## Abschlussbericht

Nenne:

- Stelle und Quelle
- verwendete Profilbelege
- nicht belegte Anforderungen
- Freigabestatus
- Pfade zu HTML, PDF, Kontaktübersicht und E-Mail-Entwurf
- dass nichts gesendet wurde
