# HTML-Bewerbungsmappe

## Prinzip

Die HTML-Datei ist die technische Quelle der Wahrheit. Sie wird im Browser geprüft und erst nach Freigabe als PDF exportiert. Es gibt keinen separaten PDF-Renderer. Die Mappe ist für den Versand per E-Mail gedacht, nicht zum Ausdrucken oder handschriftlichen Unterschreiben.

Wenn Stencil verwendet wird, ist Stencil die visuelle Quelle für Markierungen und freigegebene Designänderungen. HTML und Stencil müssen nach jeder Runde denselben Stand zeigen.

## Aufbau

Die Mappe hat immer sechs Seiten in dieser Reihenfolge:

1. Deckblatt
2. Anschreiben
3. Lebenslauf
4. Motivationsschreiben
5. Zertifikate
6. Zeugnisse

Jede Seite ist ein eigener A4-Abschnitt mit festem Seitenumbruch.

## Stabile und variable Inhalte

| Seite | Herkunft | Ändert sich pro Stelle? |
|---|---|---|
| Deckblatt | Master-Profil | nein |
| Anschreiben | Profil + Stelle | ja |
| Lebenslauf | Master-Profil | nein |
| Motivationsschreiben | Profil + Stelle | ja |
| Zertifikate | bereitgestellte Nachweise | nein |
| Zeugnisse | bereitgestellte Nachweise | nein |

## Vorlage

Die Vorlage liegt unter:

```text
.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html
```

Der Agent kopiert sie in den Bewerbungsordner und ersetzt alle Platzhalter. Struktur, CSS-Klassen und PDF-Regeln bleiben erhalten.

## Browser-Vorschau

Die Mappe verwendet bewusst unterschiedliche Layouts für Bildschirm und Papier. Eine Vorschau ist deshalb immer an der passenden Breite zu prüfen:

- Desktop: 1440 × 900 oder 1280 × 800 für Gesamtlayout und Lesbarkeit.
- Smartphone: 390 × 844 und 375 × 812 für Umbruch, Lesbarkeit und horizontalen Überlauf.
- PDF: ausschließlich die A4-Ausgabe mit 210 × 297 mm; das responsive Bildschirmlayout ist nicht die Druckfassung.

Bei jeder Freigabe werden Desktop- und Mobilansicht getrennt geprüft. Eine schmale Desktopvorschau ist kein Ersatz für die Mobilansicht. Vor dem PDF-Export wird zusätzlich ausschließlich die A4-Ausgabe geprüft. Das responsive Bildschirmlayout ist nicht die Druckfassung.

## Umgang mit generierten Inhalten

Der Agent formuliert Anschreiben, Motivationsschreiben und einzelne Projektbeschreibungen. Das ist erwünscht, aber nicht ungeprüft.

Regeln:

- Jede Aussage über den Bewerber muss durch das Master-Profil belegt sein.
- Jede Aussage über das Unternehmen muss aus der Stellenanzeige oder einer öffentlichen Unternehmensseite stammen.
- Der Agent darf Formulierungen verbessern, aber keine Fakten ergänzen.
- Unbelegte Sätze werden entfernt, nicht geglättet.
- Der Nutzer prüft die HTML-Fassung und gibt sie ausdrücklich frei.
- Erst danach entsteht das PDF.

## Anschreiben

Das Anschreiben beantwortet:

- Warum passt der Bewerber fachlich?
- Welche belegbaren Erfahrungen und Fähigkeiten helfen in der Ausbildung?
- Warum dieses Unternehmen?
- Welche Lücke wird ehrlich benannt?

Es ist sachlich, konkret und auf eine Seite begrenzt.

## Motivationsschreiben

Das Motivationsschreiben beantwortet:

- Warum dieser Beruf?
- Woher kommt das Interesse?
- Welche Erfahrung hat es verstärkt?
- Warum beschäftigt den Bewerber das Thema?
- Warum diese Ausbildung bei diesem Unternehmen?

Es ist persönlicher und erzählerischer. Es wiederholt nicht das Anschreiben.

## Projektbilder

Projektbilder sind optional. Zulässig sind nur:

- echte, vom Nutzer freigegebene Bilder,
- lesbare Bilder mit Bezug zum Projekt,
- Bilder, die im A4-PDF nicht unscharf werden.

Ein generiertes Bild darf nicht als echtes Projekt ausgegeben werden.

## Nachweise

Zertifikate und Zeugnisse werden als echte Bild- oder PDF-Assets eingebunden. Fehlt ein Scan, steht das ausdrücklich in der Mappe.

Details: [asset-handling.md](asset-handling.md)

## PDF-Export

- A4
- Ränder über CSS
- Hintergrundgrafiken an
- Kopf- und Fußzeile aus
- Maßstab 100 %
- sechs Seiten
- nichts abgeschnitten

PDF erst nach HTML-Freigabe. Das PDF ist für den E-Mail-Versand gedacht; es wird nicht ausgedruckt oder handschriftlich unterschrieben.

## Prüfliste

- [ ] sechs Seiten in richtiger Reihenfolge
- [ ] Name und Kontaktdaten identisch
- [ ] Unternehmen und Ausbildung korrekt
- [ ] Ansprechpartner belegt oder bewusst neutral
- [ ] keine offenen Platzhalter
- [ ] keine erfundenen Aussagen
- [ ] Anschreiben und Motivation erfüllen unterschiedliche Aufgaben
- [ ] Nachweise sichtbar und lesbar
- [ ] keine externen Ressourcen
- [ ] PDF-Vorschau ohne Überlauf
- [ ] HTML und Stencil stimmen überein, falls Stencil verwendet wurde
