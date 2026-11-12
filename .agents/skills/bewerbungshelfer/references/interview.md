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
- Umzug oder Pendeln? (wichtig für die E-Mail bei Stellen über 50 km)

### Block 2: Person und Kontakt

- Name, Anrede im eigenen Absender (`person.salutation`): „Herr“, „Frau“ oder ohne. Standard ist ohne; die Anrede vor dem eigenen Namen ist im deutschen Geschäftsbrief unüblich und steht nur auf ausdrücklichen Wunsch.
- Anschrift: Straße ausgeschrieben („Straße“, nicht „Str.“), ohne Punkt und Komma am Ende, PLZ und Ort getrennt
- Telefon (so speichern, wie es erscheinen soll, z. B. „+49 …“), E-Mail für Bewerbungen
- Geburtsdatum und Geburtsort (optional; Ort in der vom Nutzer bestätigten deutschen Schreibweise, im Ausland mit Land; im Lebenslauf nur mit `presentation.show_birth_data: true`)
- Bewerbungsfoto: gültig, aktuell, zum Nutzer gehörend, ausdrücklich freigegeben? Mindestens 600 × 750 px. Den Ausschnitt (`photo.focus`) wählt der Agent mit dem Nutzer an der Vorschau.
- Unterschrift als Bild: gültig und freigegeben?

### Block 3: Schulbildung

Je Abschluss oder laufendem Bildungsgang: Einrichtung, Ort, offizieller Bildungsgang, Kurzform „Schulform · Profil“ (Ableitung in `references/profile-schema.md`), Abschluss oder Abschlussziel, Zeitraum, ob der Abschluss noch aussteht. Klassenbezeichnungen sind kein Bildungsgang.

Grundschulen: Liegt ein weiterführender Abschluss vor (z. B. Mittlere Reife), bleiben Grundschulen standardmäßig aus dem Lebenslauf. Der Agent schlägt das vor und lässt es bestätigen; die Antwort steht als `show_in_cv: false` am Eintrag, der Eintrag bleibt im Profil. Ohne weiterführenden Abschluss bleibt der Standard `true`.

### Block 4: Werdegang

Je Station: Art (Praktikum, Anstellung mit Vollzeit/Teilzeit, Ehrenamt, Sonstiges), Organisation, Rolle, Ort, Zeitraum, konkrete Aufgaben, belegbares Ergebnis. Keine Aufgabe erfinden, nur weil sie zum Beruf passt. Gibt der Nutzer typische Aufgaben ausdrücklich frei, werden sie `confirmed` gespeichert.

### Block 5: Projekte

Name, Zeitraum, Ziel, eigene Rolle, Werkzeuge, Ergebnis, Link, echtes Bild mit Freigabe. Nach Entscheidungen und Problemen fragen, nicht nach Werbesätzen.

Lebenslauf: Soll ein Projekt im Block „Eigene Projekte“ erscheinen? Das kostet ca. 12 mm Kopf plus ca. 18–20 mm je Eintrag, also meist eine zusätzliche Seitenaufteilung. Wenn ja: Reihenfolge, ein belegter Satz (`cv_summary`, höchstens 160 Zeichen), vier bis sechs Werkzeuge als Chips, Titel des Blocks (`presentation.cv_projects`). Details: `references/profile-schema.md`.

### Block 6: Fähigkeiten

- Sprachen mit Niveau
- Fachliche Kenntnisse in Gruppen (z. B. Systeme, Netzwerk, Entwicklung)
- je Zeile Technologien gleichen Themas und gleichen Niveaus zusammenfassen und das Niveau (`future`, `learning`, `basic`, `solid`, `advanced`, `native`) und die Skala 1–5 **je Zeile** erfragen, nicht je Technologie; Technologien als kommagetrennte Liste in `evidence`
- `future` ist ein Lernwunsch (noch nicht angewandt) und erscheint als Skala 1 ohne Zusatztext
- Führerschein und Mobilität

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

Nicht erfragt, sondern feste Vorgaben der Vorlage: keine Fußzeile, Seitenzahl im Registerreiter, Skalen statt Prozentwerte, kein Firmenname auf dem Deckblatt, kein Kurzprofil im Lebenslauf, Betreff in gemischter Schreibung, kein Rücksendezeilen-Block, keine Timeline-Linien (`references/template.md`). Wünscht der Nutzer etwas anderes, ist das eine Designänderung an der Skill-Vorlage, kein Profilfeld.

Die Aufteilung des Lebenslaufs auf Seiten (`presentation.cv_layout`) wählt der Agent nach der Regel in `references/template.md`; der Nutzer sieht das Ergebnis in der Profilvorlage.

## Gesprächsregeln

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
