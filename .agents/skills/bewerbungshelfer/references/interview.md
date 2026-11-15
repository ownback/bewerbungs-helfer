# Profil wählen, Unterlagen auswerten, Interview

## Profil wählen

1. Ordner unter `profile/` auflisten (`import/` und `assets/` sind keine Profile).
2. Fragen, mit welchem Profil gearbeitet wird. Pro Durchlauf genau ein Profil.
3. Bei einem bestehenden Profil: `assets/profile/<name>_profile.json` lesen, offene Punkte (`open_questions` mit `status: open`) und `profile_status` zeigen. Ist es bestätigt und nichts Blockierendes offen, weiter mit der Profilvorlage.

## Neues Profil anlegen

Einstieg:

> Ich lege dein Profil an. Es bleibt lokal auf deinem Rechner und wird nur für deine Bewerbungsmappen verwendet. Leg bitte deine Unterlagen in `profile/import/`: alten Lebenslauf, Zeugnisse, Zertifikate, Bewerbungsfoto und Unterschrift, soweit vorhanden. Danach frage ich nur, was fehlt oder unklar ist.

Dann:

1. Ordnername aus Vor- und Nachname: Kleinbuchstaben, ASCII, `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, Leerzeichen im Vornamen als Bindestrich, Punkt zwischen Vor- und Nachname, z. B. `max.mustermann`, `anna-lena.mueller`.
2. Ordnerstruktur nach `references/applications.md` anlegen (`assets/{documents/old,photos/cv,photos/project,signature,profile}`, `applications/{apprenticeships,jobs,internships,sent/…}`).
3. Dateien aus `profile/import/` verschieben und umbenennen (`<name>_<inhalt>.<endung>`):
   - alter Lebenslauf (PDF, DOCX) → `assets/documents/old/`
   - Zeugnisse, Zertifikate (Bild) → `assets/documents/`; PDF-Nachweise zusätzlich als PNG rendern (`pdftoppm -png -r 150`), das PDF bleibt daneben
   - Bewerbungsfoto → `assets/photos/cv/`, Projektfotos → `assets/photos/project/`
   - Unterschrift → `assets/signature/`
4. `assets/templates/profile.json` und `profile.md` aus dem Skill als Startpunkt kopieren.

## Unterlagen auswerten

Für jede Datei:

1. Technisch prüfen: lesbar, nicht leer (0 Byte), richtiges Format.
2. PDFs, DOCX und Bilder **visuell** lesen, nicht nur per Textextraktion. Entscheidende Angaben stehen oft in Grafiken.
3. DOCX auf eingebettete Bilder prüfen. Ein Vorlagen-Platzhalter („Foto einfügen“) ist kein Foto.
4. Alle Stationen, Zeiträume, Aufgaben, Nachweise und Kontaktdaten erfassen.
5. Jede Angabe einordnen: `confirmed`, `inferred`, `open` oder `conflict`.

Ergebnis in `assets/documents/old/extracted_information.md` nach `assets/templates/extracted_information.md`: je Quelle die erkannten Angaben mit Fundstelle, dazu eine Abweichungsliste (fehlt, widersprüchlich, unklar, zusätzlich erkannt). Diese Datei ist die Arbeitsgrundlage für das Interview, nicht das Profil selbst.

Defekte Dateien werden ausdrücklich als offen gemeldet und nie eingebunden, besonders ein leeres oder fremdes Bewerbungsfoto.

## Interview

Nur zu den Punkten der Abweichungsliste und zu Feldern, die das Profil braucht und keine Quelle haben. In kleinen Blöcken fragen.

### Block 1: Ziel

- Art: Ausbildung, Job oder Praktikum (`goal.type`)
- Beruf, Alternativen, frühester Beginn
- Zielorte und Umkreis (Vorgabe für die BA-Suche)
- Umzug oder Pendeln? Wenn Umzug: in welche Zielorte (`goal.locations`) und wann (`goal.relocation_timing`, z. B. „Sommer 2027“)? Das steuert den Umzugssatz in der E-Mail (Regel `email.relocation` in `references/writing.md`).

### Block 2: Person und Kontakt

- Name, Anrede im eigenen Absender (`person.salutation`): „Herr“, „Frau“ oder ohne. Standard ist ohne; die Anrede vor dem eigenen Namen ist im deutschen Geschäftsbrief unüblich und steht nur auf ausdrücklichen Wunsch.
- Anschrift, gespeichert nach Regel `address.format` in `references/template.md`
- Telefon (so speichern, wie es erscheinen soll, z. B. „+49 …“), E-Mail für Bewerbungen
- Geburtsdatum und Geburtsort (optional; Schreibweise des Orts nach Regel `person.birth-place` in `references/profile-schema.md`; im Lebenslauf nur mit `presentation.show_birth_data: true`)
- Bewerbungsfoto: gültig, aktuell, zum Nutzer gehörend, ausdrücklich freigegeben (Regel `person.photo` in `references/profile-schema.md`)? Größe und Ausschnitt (`photo.focus`) nach Regel `cover.photo-crop` in `references/template.md`; den Ausschnitt wählt der Agent mit dem Nutzer an der Vorschau.
- Unterschrift als Bild: gültig und freigegeben? Wörtlich fragen: „Darf deine Unterschrift als Bild in der Mappe stehen, unter dem Anschreiben und am Ende des Lebenslaufs?“ Nur ein Ja für beide Stellen setzt `consent: true` (Regel `person.signature` in `references/profile-schema.md`).

### Block 3: Schulbildung

Je Abschluss oder laufendem Bildungsgang: Einrichtung, Ort, offizieller Bildungsgang, Kurzform „Schulform · Profil“ (Ableitung in `references/profile-schema.md`), Abschluss oder Abschlussziel, Zeitraum, ob der Abschluss noch aussteht. Klassenbezeichnungen sind kein Bildungsgang.

Grundschulen: Der Agent schlägt vor, sie aus dem Lebenslauf zu lassen, und lässt das bestätigen (Regel `education.primary-school` in `references/profile-schema.md`).

### Block 4: Werdegang

Je Station: Art (Praktikum, Anstellung mit Vollzeit/Teilzeit, Ehrenamt, Sonstiges), Organisation, Rolle, Ort, Zeitraum, konkrete Aufgaben, belegbares Ergebnis. Keine Aufgabe erfinden, nur weil sie zum Beruf passt. Gibt der Nutzer typische Aufgaben ausdrücklich frei, werden sie `confirmed` gespeichert.

### Block 5: Projekte

Name, Zeitraum, Ziel, eigene Rolle, Werkzeuge, Ergebnis, Link, echtes Bild mit Freigabe. Nach Entscheidungen und Problemen fragen, nicht nach Werbesätzen.

Pro Projekt fragen: „Gibt es ein eigenes Foto zu diesem Projekt (z. B. Aufbau, eigene Oberfläche)? Dürfen wir es in der Bewerbungsmappe zeigen?“ Wenn ja: Datei nach `assets/photos/project/` legen und nach Sichtprüfung eintragen. Wenn nein oder unklar: kein Foto. Was eingetragen wird und wann das Foto erscheint: Regel `project.photo` in `references/profile-schema.md`.

Lebenslauf: Soll ein Projekt im Block „Eigene Projekte“ erscheinen? Das braucht Platz und meist eine zusätzliche Seitenaufteilung (Regel `cv.projects-block` in `references/template.md`). Wenn ja: Reihenfolge, ein belegter Satz (`cv_summary`), Werkzeuge als Chips, Titel des Blocks (`presentation.cv_projects`); Feldregeln in `references/profile-schema.md`, Projekte.

### Block 6: Fähigkeiten

- Sprachen mit Niveau
- Fachliche Kenntnisse in Gruppen (z. B. Systeme, Netzwerk, Entwicklung)
- je Zeile Technologien gleichen Themas und gleichen Niveaus zusammenfassen und das Niveau (`future`, `learning`, `basic`, `solid`, `advanced`, `native`) und die Skala 1–5 **je Zeile** erfragen, nicht je Technologie; Technologien als kommagetrennte Liste in `evidence`
- `future` ist ein Lernwunsch (noch nicht angewandt) und erscheint als Skala 1 ohne Zusatztext
- Führerschein und Mobilität (Klasse → `person.driving_license`, z. B. „Klasse B“, Status `confirmed`; erscheint im Lebenslauf als „Führerschein Klasse B“, leer = nicht angezeigt; Pendel-/Umzugsbereitschaft gehört zu `goal`)

Fähigkeiten ohne erkennbares Niveau (z. B. Icons ohne Balken im alten Lebenslauf) bekommen kein geratenes Niveau: nachfragen, bis dahin `open` und nicht anzeigen. Technologien, die der Nutzer nicht genannt hat, nie ergänzen, auch wenn ein Logo vorhanden ist; bei Anregungen (z. B. gängige Netzwerk-Werkzeuge) fragen, ob und auf welchem Niveau sie stimmen.

Gruppen, Zeilenbezeichnungen, Icons und Chips leitet der Agent aus diesen Antworten ab (Regeln in `references/profile-schema.md`) und zeigt sie in der Profilvorlage zur Freigabe.

### Block 7: Nachweise

Je Nachweis: Titel, Aussteller, Datum, Datei, Art (Zertifikat, Schulzeugnis, Arbeits- oder Praktikumszeugnis), in der Mappe zeigen, Original-Scan oder Kopie, technisch gültig.

### Block 8: Motivation und Stimme

- Wann und wodurch entstand das Interesse?
- Welche Erfahrung hat es verstärkt? Welches Projekt beschäftigt den Nutzer?
- Was will er lernen?
- Drei Stärken mit je einem Beispiel; ein selbst gelöstes Problem
- Was darf nicht in der Bewerbung stehen?

### Block 9: Darstellung

- Kurzprofil für das Deckblatt (`portfolio.cover_bio`: zwei bis drei natürliche Sätze, Vorschlag des Agenten nach den Regeln in `references/profile-schema.md`, Freigabe durch den Nutzer)
- Berufsbezeichnung auf dem Deckblatt (`portfolio.cover_role`), ggf. auf zwei Zeilen
- Geburtsdaten im Lebenslauf zeigen? (`presentation.show_birth_data`, Standard nein)
- Eigene Projekte im Lebenslauf und Grundschulen im Lebenslauf: siehe Block 5 und Block 3

Nicht erfragt werden die festen Vorgaben der Vorlage (Regel `design.fixed` in `references/template.md` und das Designsystem dort, z. B. keine Fußzeile, Skalen statt Prozentwerte, kein Firmenname auf dem Deckblatt). Wünscht der Nutzer etwas anderes, ist das eine Designänderung an den Quellen der Vorlage (`references/tencil.md`), kein Profilfeld.

Die Aufteilung des Lebenslaufs auf Seiten (`presentation.cv_layout`) wählt der Agent nach Regel `cv.layout` in `references/template.md`; der Nutzer sieht das Ergebnis in der Profilvorlage.

## Gesprächsregeln

<!-- rule: interview.conduct -->
- Nicht nach bereits bestätigten Angaben fragen.
- Widersprüche genau einmal ansprechen und die Entscheidung mit Quelle speichern.
- Zusammenfassen und bestätigen lassen; erst dann ins Profil schreiben.
- Eine Jahresangabe bleibt eine Jahresangabe. Plausible Näherungen nur nach ausdrücklicher Freigabe, dann `approx: true` und `inferred`.
- Unbekanntes bleibt `open` und erscheint als offener Punkt.

## Ergebnis

- `assets/profile/<name>_profile.json`, gültig gegen `assets/schemas/profile.schema.json`
- `assets/profile/<name>_profile.md` als lesbare Zusammenfassung
- `assets/documents/old/extracted_information.md`
- `profile_status: confirmed` erst, wenn der Nutzer die Zusammenfassung bestätigt hat und nichts Blockierendes oder Widersprüchliches offen ist.
