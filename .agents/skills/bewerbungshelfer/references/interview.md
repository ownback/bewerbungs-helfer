# Profilinterview

## Ausgangspunkt

Ein frischer Clone enthält kein Profil. Prüfe zuerst:

- `profile/master-profile.json`
- `profile/master-profile.md`
- alle vom Nutzer bereitgestellten Dateien unter `profile/import/`

Übernimm nichts ungeprüft aus einem Lebenslauf. Fasse erkannte Angaben zusammen und lass sie bestätigen.

Beginne mit:

> Ich baue mit dir dein Master-Profil. Das bleibt lokal und wird nur für deine Bewerbungsmappen verwendet. Wir gleichen zuerst deine vorhandenen Unterlagen ab und fragen nur, was noch fehlt oder unklar ist.

## Unterlagen zuerst

Wenn der Nutzer einen Lebenslauf, ein Zeugnis, ein Zertifikat oder ein Foto bereitstellt:

1. Prüfe jede Datei technisch.
2. Lies PDFs, DOCX und Bilder auch visuell, nicht nur als Text.
3. Prüfe DOCX auf eingebettete Bilder.
4. Erfasse alle Stationen, Zeiträume, Aufgaben, Nachweise und Kontaktdaten.
5. Ordne jede Angabe als `confirmed`, `inferred`, `open` oder `conflict` ein.
6. Zeige eine kompakte Abweichungsliste: fehlt, widersprüchlich, unklar, zusätzlich erkannt.
7. Frage nur zu diesen Punkten nach.

Defekte Dateien werden nicht als gültig markiert. Eine leere Bilddatei wird ausdrücklich als offen gemeldet.

## Block 1: Ziel

- Welche Ausbildung?
- Welche Alternativen sind akzeptabel?
- Frühester Beginn?
- Welche Orte?
- Welcher Umkreis?
- Umzug oder Pendeln?

## Block 2: Identität, Kontakt und Foto

- Name
- Anschrift
- Telefon
- E-Mail
- gewünschte Anrede
- Geburtsdatum und Geburtsort
- Bewerbungsfoto verwenden?
- Ist die Bilddatei gültig, aktuell und ausdrücklich freigegeben?

## Block 3: Schulbildung

Für jeden Abschluss oder laufenden Bildungsgang:

- Einrichtung
- Ort
- offizieller Bildungsgang
- Abschluss oder Abschlussziel
- Zeitraum
- Besonderheiten, die zur Einordnung nötig sind

Klassenbezeichnungen nur als Detail erfassen, nicht als Bildungsgang.

## Block 4: Werdegang

Für jede Station:

- Art: Praktikum, Anstellung, Ehrenamt oder Sonstiges
- Organisation
- Rolle
- Ort
- Zeitraum
- konkrete Aufgaben
- belegbares Ergebnis
- Quelle

Keine Aufgabe erfinden, nur weil sie zur Ausbildung passt. Wenn der Nutzer typische Aufgaben ausdrücklich freigibt, werden sie als bestätigt gespeichert.

## Block 5: Projekte

- Name
- Zeitraum
- Ziel
- eigene Rolle
- Werkzeuge
- Ergebnis
- Link oder Bild
- Bildfreigabe

Frage nach Entscheidungen und Problemen, nicht nach Werbesätzen. Ein Projektbild muss echt, lesbar und freigegeben sein.

## Block 6: Fähigkeiten

- Sprachen mit Niveau
- fachliche Kenntnisse
- Werkzeuge
- Methoden
- Führerschein und Mobilität
- Soft Skills nur mit Beispiel

Für jede Fähigkeit:

- Niveau: `learning`, `basic`, `solid`, `advanced`, `future` oder `native`
- visuelle Skala 1–5
- kurzer Beleg oder ausdrückliche Selbsteinschätzung

Die Skala ist keine Prozentangabe. Sie dient nur der Darstellung.

## Block 7: Nachweise

- Titel
- Aussteller
- Datum
- Datei
- Zertifikat, Zeugnis oder sonstiger Nachweis?
- sichtbar in der Mappe?
- Original oder Kopie?
- technisch gültig?

## Block 8: Motivation und Stimme

- Wann entstand das Interesse?
- Welche Erfahrung hat es verstärkt?
- Welches Projekt beschäftigt den Nutzer noch?
- Was will er lernen?
- Drei Stärken mit Beispiel
- Was darf nicht in der Bewerbung stehen?

## Block 9: Darstellung

- Sollen Fähigkeiten als Diagramme erscheinen?
- Welche Icons sollen für wiederkehrende Kategorien verwendet werden?
- Unternehmensname auf dem Deckblatt?
- Nur der Name in der Fußzeile?

Die Entscheidungen werden in `presentation` gespeichert und gelten für künftige Mappen.

## Gesprächsregeln

- In kleinen Blöcken fragen.
- Nicht nach bereits bestätigten Angaben fragen.
- Widersprüche genau einmal ansprechen.
- Zusammenfassen und bestätigen lassen.
- Unbekanntes als offen markieren.
- Erst nach Bestätigung in das Profil schreiben.
- Keine persönlichen Daten in Git speichern.

## Ergebnis

`profile/master-profile.json` nach `assets/schemas/profile.schema.json` und `profile/master-profile.md` als lesbare Zusammenfassung.
