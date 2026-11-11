# Profil und Fragebogen

## Ziel

Beim ersten Start ein stabiles, belegbares Master-Profil aufbauen. Das Repository startet ohne Profildaten. Vorhandene Unterlagen können den Einstieg erleichtern, sind aber nicht erforderlich.

## Optionaler Import

Der Import ist nicht der Standardweg. Der Agent beginnt mit dem Abgleich vorhandener Unterlagen und nutzt sie, wenn der Nutzer sie bereitstellt.

Der Nutzer kann Dateien unter `profile/import/` ablegen:

- Lebenslauf als PDF oder DOCX
- Zeugnisse als PDF oder Bild
- Zertifikate als PDF oder Bild
- Bewerbungsfoto, optional

Der Agent liest die Dateien vollständig und prüft PDFs, DOCX und Bilder auch visuell. Er zeigt eine Zusammenfassung und markiert:

- sicher gelesen
- freigegebene Näherung
- unklar
- widersprüchlich
- fehlt oder defekt

## Frageblöcke

### 1. Ziel

- Welche Ausbildung?
- Nur ein Beruf oder auch Alternativen?
- Frühester Beginn?
- Welche Orte?
- Welcher Umkreis?
- Umzugsbereitschaft?
- Pendelbereitschaft?

### 2. Kontakt und Foto

- Name
- Anschrift
- Telefon
- E-Mail
- gewünschte Anrede
- Geburtsdatum und Geburtsort (optional; nur nach Freigabe im Lebenslauf)
- Bewerbungsfoto verwenden?
- Ist die Bilddatei gültig, aktuell und ausdrücklich freigegeben?

### 3. Schulbildung

Für jeden Abschluss oder laufenden Bildungsgang:

- Einrichtung
- Ort
- offizieller Bildungsgang
- Abschluss oder Abschlussziel
- Zeitraum
- Note, falls verwendet
- Schwerpunkte

Klassenbezeichnungen nur als Detail erfassen, nicht als Bildungsgang.

### 4. Erfahrung

- Praktika
- Nebenjobs
- Ehrenamt
- Schülerfirma
- eigene Projekte

Für jede Station:

- Art: Praktikum, Anstellung, Ehrenamt oder Sonstiges
- Zeitraum
- Organisation
- Rolle
- konkrete Aufgaben
- belegbares Ergebnis

### 5. Projekte

Für jedes Projekt:

- Name
- Zeitraum
- Ziel
- eigene Rolle
- Werkzeuge
- Ergebnis
- Link, optional
- Bild, optional – nur echt, lesbar und ausdrücklich freigegeben

### 6. Motivation

- Wann ist das Interesse entstanden?
- Welche Erfahrung hat es verstärkt?
- Welches Projekt beschäftigt den Nutzer noch?
- Was will er in der Ausbildung lernen?
- Was soll auf keinen Fall in der Bewerbung stehen?

### 7. Fähigkeiten

- Sprachen und Niveau
- fachliche Kenntnisse
- Werkzeuge
- Methoden
- Führerschein und Mobilität

Für jede Fähigkeit:

- Niveau: `learning`, `basic`, `solid`, `advanced`, `future` oder `native`
- visuelle Skala 1–5
- Beleg oder ausdrückliche Selbsteinschätzung

Die Skala ist eine visuelle Einordnung, kein Prozentwert.

### 8. Nachweise

Für jeden Nachweis:

- Titel
- Aussteller
- Datum
- Datei
- Zertifikat, Schulzeugnis, Arbeits-/Praktikumszeugnis oder sonstiger Nachweis?
- in der Mappe sichtbar?
- Original oder Kopie?
- technisch gültig?

### 9. Stimme

- drei Stärken mit Beispiel
- ein Problem, das selbst gelöst wurde
- ein Projekt, über das der Nutzer gerne spricht
- Formulierungen, die nicht verwendet werden dürfen

### 10. Darstellung

- Sollen Fähigkeiten als Diagramme erscheinen?
- Welche Icons sollen für wiederkehrende Kategorien verwendet werden?
- Unternehmensname auf dem Deckblatt?
- Nur der Name in der Fußzeile?

## Gesprächsregeln

- In kleinen Blöcken fragen.
- Antworten zusammenfassen und bestätigen lassen.
- Nicht nach Dingen fragen, die bereits klar im importierten Profil stehen.
- Widersprüche genau einmal ansprechen.
- Fehlende Angaben als offen markieren.
- Keine Antwort als Tatsache speichern, bevor der Nutzer sie bestätigt hat.
- Freigegebene Näherungen als `inferred` speichern.

## Ergebnis

- `profile/master-profile.json` nach `.agents/skills/bewerbungshelfer/assets/schemas/profile.schema.json`
- `profile/master-profile.md` als lesbare Zusammenfassung
- beide Dateien bleiben lokal und gitignoriert
