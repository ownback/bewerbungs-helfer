# Profil (Datenvertrag)

Ein Profil liegt unter `profile/<vorname.nachname>/assets/profile/`:

- `<name>_profile.json`: primäre, strukturierte Quelle. Schema `assets/schemas/profile.schema.json` (Version `1.1`).
- `<name>_profile.md`: lesbare Fassung für die gemeinsame Prüfung.

Startpunkte: `assets/templates/profile.json` und `profile.md`. Alles bleibt gitignoriert.

## Grundsätze

- Keine Angabe ohne Quelle oder ausdrückliche Bestätigung. Quellen stehen in `sources`, Einträge verweisen über `source_ids`.
- Status je Angabe: `confirmed`, `inferred`, `open`, `conflict`. Listeneinträge (Bildung, Erfahrung, Projekte, Fähigkeiten, Nachweise) nutzen `source_status`; die Blöcke `person`, `goal`, `motivation`, `voice` nutzen `field_status` mit einem Eintrag je ausgefülltem Feld.
- `inferred` ist eine vom Nutzer freigegebene Näherung, keine überprüfte Tatsache.
- Praktikum, Anstellung, Schulbildung und Projekt werden nie vermischt.
- Defekte Dateien werden nicht eingebunden.
- `profile_status: "confirmed"` nur nach Bestätigung durch den Nutzer und ohne offenen Punkt mit `severity: "blocking"` oder Eintrag mit `conflict`.
- Pfade zu Dateien sind repo-relativ (`profile/<name>/assets/…`). Das Build-Skript löst jeden Pfad auf (inklusive `..` und Symlinks) und verlangt, dass er unter `profile/<name>/assets/` des gewählten Profils liegt; absolute Pfade außerhalb, `..`-Ausbrüche und Symlinks aus dem Profil heraus brechen mit dem betroffenen Profilfeld ab (`person.photo.file`, `person.signature.file`, `evidence[<id>].file`, `projects[<id>].images[n].file`). Auch `validate` prüft das. In die Mappe kopierte Bilder behalten ihren Dateinamen in `application/assets/`; zwei verschiedene Dateien mit gleichem Namen aus verschiedenen Ordnern sind ein Fehler (eine umbenennen).

## Person

Name, `first_name` und `last_name` (sie steuern die Namensgröße auf dem Deckblatt, Schwellen in `references/template.md`), `salutation` (Anrede im eigenen Absender: `Herr`, `Frau` oder leer), Anschrift, Telefon, E-Mail.

- Straße ausgeschrieben mit Hausnummer („Musterstraße 6“), PLZ und Ort getrennt. Die Mappe setzt Straße und „PLZ Ort“ zweizeilig ohne Komma.
- Telefon speichern, wie es erscheinen soll („+49 …“); E-Mail ohne Zusatz.
- Geburtsdatum (Anzeige „TT.MM.JJJJ“) und -ort sind optional und erscheinen nur bei `presentation.show_birth_data: true`. Der Ort steht in der vom Nutzer bestätigten deutschen Schreibweise, im Ausland mit Land („Ort, Land“, z. B. „Krakau, Polen“). Der Lebenslauf trennt am letzten Komma: Ort und Land stehen untereinander, ohne Komma (Herkunft in der ersten Zeile der rechten Spalte). Ohne Komma bleibt der Ort einzeilig.
- `driving_license` (optional): Klasse als Text mit Präfix („Klasse B“). Der Lebenslauf zeigt „Führerschein Klasse B“ mit `i-car` in der Datenbox, nach den Geburtsdaten; leer oder fehlend = keine Zeile.
- `photo`: nur gültig, wenn die Datei lesbar ist, zum Nutzer gehört, `consent: true` gesetzt und ein Zuschnitt gewählt ist. `focus` steuert den Ausschnitt im 4:5-Rahmen (`x`, `y` als Prozent, `zoom` bis ca. 1,2). Leere oder defekte Datei: `valid: false` und offener Punkt.
- `signature`: Bild der Unterschrift mit `valid` und `consent`. Nur dann im Anschreiben.

## Ziel

`type` (`apprenticeships`, `jobs`, `internships`), `apprenticeship` (Zielberuf), Alternativen, Beginn (`JJJJ-MM-TT`), Orte, Umkreis, Umzug und Pendeln, `relocation_timing` (Zeitpunkt eines geplanten Umzugs, z. B. „Sommer 2027“). Der Umkreis ist die Vorgabe für die BA-Suche.

## Zeiträume

```json
{ "start": "YYYY-MM", "end": "YYYY-MM", "precision": "month|year|day|unknown", "is_current": false, "approx": false }
```

- Format folgt `precision`: `YYYY`, `YYYY-MM`, `YYYY-MM-DD`; bei `unknown` dürfen beide Werte `null` sein.
- `end: null` nur bei laufender Station mit `is_current: true` (Anzeige „seit MM/JJJJ“).
- `approx: true` nur nach Freigabe einer Näherung; dann `source_status: "inferred"` (Schema erzwingt das). Anzeige mit „ca.“, z. B. „ca. 03/2023“.
- Gleicher Start- und Endmonat erscheint als ein Monat („05/2024“).

## Schulbildung

Einrichtung, Ort, Land, offizieller Bildungsgang (`program`), Kurzform für den Lebenslauf (`program_short`), Abschluss (`qualification`), Zeitraum, `expected: true` bei ausstehendem Abschluss (Anzeige „Abschluss: …, voraussichtlich MM/JJJJ“), optional Details (erscheinen nicht in der Mappe). Ort im Ausland erscheint als „Ort (Land)“.

- `program_short` leitet der Agent aus `program` ab: „Schulform · Profil“, ohne Zusätze wie „zur Fachschulreife führende“ oder „gewerblich-technischer Bereich“ (z. B. „Zweijährige Berufsfachschule · Profil Metalltechnik“). Ohne Profil steht nur die Schulform; fehlt `program_short`, erscheint `program`. Klassen und Zeugnisdetails gehören nicht in den Lebenslauf.
- `show_in_cv` (optional, Standard `true`): `false` blendet den Eintrag im Lebenslauf aus, er bleibt im Profil. Gilt für Grundschulen, sobald ein weiterführender Abschluss (z. B. Mittlere Reife) vorliegt: der Agent schlägt das vor, der Nutzer bestätigt (`references/interview.md`, Block 3).
- Reihenfolge im Lebenslauf: neueste zuerst nach Beginn; das Build-Skript sortiert so.

## Erfahrung

Organisation, Ort, `kind` (`internship`, `employment`, `volunteer`, `other`), Rolle, bei Anstellungen `employment_type` („Vollzeit“, „Teilzeit“), Zeitraum, Aufgaben, optional Ergebnis. Die Rollenzeile lautet z. B. „Produktionsmitarbeiter · Anstellung (Vollzeit)“; Aufgaben werden mit Semikolon verbunden. Sortierung wie bei der Schulbildung: neueste zuerst.

Aufgaben: zwei bis drei kurze Satzglieder ohne Punkt (Infinitiv oder Nominalstil, z. B. „Maschinen einrichten“), zusammen höchstens zwei Zeilen im Lebenslauf. Nur belegte oder vom Nutzer freigegebene Aufgaben (`references/interview.md`, Block 4).

## Projekte

Name, Zeitraum, Ziel, eigene Rolle, Werkzeuge, Ergebnis, optional Link, nur echte Bilder mit `consent` und `valid`. Projekte liefern Stoff für die Briefe und die Belege-Spalte im Motivationsschreiben.

**Projektfotos (Runde 6, feste Regel):**

- Datei unter `profile/<name>/assets/photos/project/` (repo-relativ `profile/<name>/assets/photos/project/…`), eingetragen in `projects[].images[]` mit `file`, `consent: true` (Nutzer hat zugestimmt) und `valid: true` (Datei lesbar, eigenes Bild).
- Zuordnung: Ein Beleg im Motivationsschreiben bekommt das Projektfoto, wenn sein Titel (`- <icon> | <Titel> | …`) gleich `projects[].name` ist (ohne Groß-/Kleinschreibung). Es wird das erste Bild mit `consent` und `valid` gezeigt, 4:3 unter dem Belegtext.
- Fallback (fest, kein Ermessen): Gibt es kein passendes Projekt, kein Bild, `consent: false` oder `valid: false`, erscheint kein Foto und kein Platzhalter. Der Belegtext bleibt. Die Mappe baut ohne Projektfotos.
- Ein Bild, das im Profil eingetragen ist, aber fehlt, bricht den Bau mit Fehler ab (`check_profile_assets`); es wird nie still ersetzt.
- Keine fremden Personen, keine generierten Bilder, keine Platzhalterfotos.

Optional erscheinen ausgewählte Projekte im Lebenslauf-Block „Eigene Projekte“ (z. B. Homelab, Open-Source-Beitrag):

- `show_in_cv: true` am Projekt und der Block `projects` in `presentation.cv_layout.pages`
- `cv_summary`: ein kurzer, belegter Satz (höchstens 160 Zeichen); fehlt er, erscheint `own_role`
- `chips`: Werkzeuge als Technik-Chips (ca. 4–6, Format wie bei Fähigkeiten), nur Werkzeuge aus `tools`; fehlt es, werden `tools` als Text-Chips gezeigt
- Titel und Icon des Blocks: `presentation.cv_projects` (`title`, `icon`), Standard „Eigene Projekte“ mit `i-layers`

Nur mit dem Nutzer abgestimmte Projekte zeigen; der Block braucht ca. 12 mm plus ca. 18–20 mm je Eintrag.

## Fähigkeiten

`skills.groups[]` mit `name`, `icon` (Linien-Icon der Vorlage, z. B. `i-monitor`, `i-network`, `i-code`) und `items[]`; `skills.languages[]`.

Jedes Item:

- `name`, `level`, `scale` (1–5), `evidence` (Technologien als kommagetrennte Liste, nie das Niveauwort), `source_status`
- optional `label`, `note`, `chips`:
  - `label`: kurze Kategorie als Zeilenname im Lebenslauf (ein bis zwei Wörter, höchstens ca. 16 Zeichen, sonst bricht die Zeile um), z. B. „Frontend“, „Tools“; ohne Angabe gilt `name`.
  - `note`: kleiner Zusatz unter dem Zeilennamen. Bei `level: learning` setzt das Build-Skript ohne Angabe „Lernstand“ (leerer String unterdrückt es); sonst nur ein knapper Beleg wie „eigene Projekte“. Bei `future` nie ein Zusatz.
  - `chips`: Technik-Chips mit `name`, optional `logo` (`dv-…` Devicon oder `si-…` Simple Icons, Liste in `references/template.md`) oder `icon` (Linien-Icon `i-…`). Reihenfolge wie genannt, höchstens ca. 6 je Zeile. Ohne `chips` bildet das Build-Skript Chips aus `evidence`; deshalb enthält `evidence` nur Technologien. Ein vorhandenes Logo ist kein Grund, eine Technik aufzunehmen. Welches Symbol zu welchem Begriff gehört, steht in `assets/icons/README.md` unter „Zuordnung Begriff → Symbol“.
- Eine Zeile = ein Thema mit genau einem Niveau; mehrere Technologien gleichen Niveaus teilen sich die Zeile und die Skala.
- Gruppen: zwei bis vier, Name und Icon aus der Themenlage, z. B. „Systeme“ (`i-monitor`), „Netzwerk“ (`i-network`), „Entwicklung“ (`i-code`); weitere Icons stehen in `references/template.md`. Bei „Entwicklung“ trennen die Zeilenbezeichnungen Frontend, Backend und Mobile.

Kopplung von Niveau und Skala (Schema):

| `level` | Bedeutung | `scale` |
|---|---|---|
| `future` | Lernwunsch | 1 |
| `learning` | Lernstand | 1–2 |
| `basic` | Grundkenntnisse | 2–3 |
| `solid` | sicher | 3–4 |
| `advanced` | routiniert | 4–5 |
| `native` | Muttersprache | 3–5 (Standard 5; weniger nur auf ausdrücklichen Wunsch, z. B. schwächere Schriftsprache; das Wort bleibt „Muttersprache“) |

Die Mappe zeigt die Skala mit der Legende 1 Lernwunsch · 2 Grundkenntnisse · 3 sicher · 4 routiniert · 5 sehr sicher; bei Sprachen steht das Wort zur Skala darunter, bei `native` „Muttersprache“. Keine Prozentangaben, keine geratenen Niveaus, nur Technologien aus dem Profil.

## Nachweise

`id`, Titel, Aussteller, Datum, Datei (Bild), `kind` (`certificate` → Seite Zertifikate; `school_report`, `work_reference` → Seite Zeugnisse; `other` nur nach Absprache), `show_in_portfolio`, `original` (`scan`, `copy`, `digital_original`), `valid`, `source_status`, optional `pair` (zwei aufeinanderfolgende kurze Nachweise teilen sich eine Seite). Die Reihenfolge in der Mappe folgt der Reihenfolge im Profil (je Abschnitt). Fehlende Nachweise bleiben offen; es werden keine Ersatzdokumente erzeugt.

## Portfolio-Texte

`portfolio` enthält freigegebene Texte der stabilen Seiten:

- `cover_role`: Berufsbezeichnung auf dem Deckblatt, eine Zeile je Eintrag. Ist sie länger als ca. 18 Zeichen, bricht der Agent vor der Fachrichtung um (`["Fachinformatiker", "für Systemintegration"]`); sonst eine Zeile. Maximal drei Zeilen.
- `cover_bio`: Kurzprofil in der Ich-Form, zwei bis drei natürliche Sätze (aktueller Bildungsweg, Zugang zum Beruf, Ziel), nur belegte Fakten aus dem Profil, keine Floskeln. Das Alter nur als exakte Zahl und nur auf Wunsch, nie als Näherung („bald 21“). Der Agent schlägt den Text vor, der Nutzer gibt ihn frei; er steht nur auf dem Deckblatt, nicht im Lebenslauf.
- optional `cover_start` (sonst „Ausbildung ab <Monat Jahr>“ aus `goal.start`) und `cv_goal` (sonst „Ausbildungsziel: <Beruf>“, nie ein noch nicht erreichtes Berufsbild unter dem Namen). Bei `goal.type` `jobs` oder `internships` beide Texte ausdrücklich setzen, die Standardtexte sprechen von Ausbildung.

Fehlt ein Text, setzt das Build-Skript einen Platzhalter, den die QA meldet.

## Darstellung

`presentation` speichert wiederkehrende Entscheidungen. Feste Vorgaben (Konstanten im Schema, nicht erfragt) und frei wählbare Werte:

- `footer: "none"` (keine Fußzeile; Seitenzahl im Registerreiter)
- `cover_company_name: false`, `skill_display: "bars"`, `timeline_connectors: false`, `page_number_style: "plain_without_total"`
- `show_birth_data`
- `cv_layout`: `pages` (Blöcke je A4-Seite in Lesereihenfolge `experience`, `education`, `skills`, `languages`; optional `projects` irgendwo nach `experience`) und `compact` (`true` für alle Lebenslaufseiten oder eine Liste je Seite, z. B. `[false, true]`). Standard ist eine Seite mit `experience`, `education`, `skills`, `languages`; läuft sie über, ganze Blöcke auf eine Fortsetzungsseite verschieben, Reihenfolge beibehalten (`references/template.md`, Lebenslauf). Das Build-Skript warnt, wenn Sprachen vor Schulbildung oder Fähigkeiten stehen.
- `cv_projects` (optional): `title` und `icon` des Blocks „Eigene Projekte“.
- `icons`: ohne Wirkung (veraltet); Icons stehen je Gruppe (`icon`) und je Chip.

### Woher kommen die Anzeigewerte?

Alle Werte, die die Mappe zeigt, stehen im Profil. Ein neuer Durchlauf leitet sie so ab; der Nutzer sieht das Ergebnis in der Profilvorlage und gibt es frei:

| Wert | Wirkung | Wahl durch den Agenten |
|---|---|---|
| `portfolio.cover_role`, `cover_bio` | Deckblatt | Regeln oben, Freigabe durch den Nutzer |
| `portfolio.cover_start`, `cv_goal` | Kapsel auf dem Deckblatt, Zeile unter dem Namen im Lebenslauf | Standardtexte aus `goal`, nur bei Abweichung setzen |
| `education[].program_short` | zweite Zeile je Schule | Ableitung aus `program` (Schulbildung) |
| `education[].show_in_cv` | Eintrag im Lebenslauf | Grundschulen nach weiterführendem Abschluss: Vorschlag, Nutzer bestätigt |
| `experience[].employment_type` | „Anstellung (Vollzeit)“ | Antwort des Nutzers |
| `skills…label`, `note`, `chips` | Zeilenname, Zusatz, Chips | Regeln unter Fähigkeiten; Logos nur aus der Liste in `references/template.md` |
| `skills.groups[].name`, `icon` | Gruppentitel | Regeln unter Fähigkeiten |
| `person.salutation` | „Herr“/„Frau“ im Absender | Antwort des Nutzers, Standard leer |
| `person.driving_license` | Zeile „Führerschein …“ in der Datenbox des Lebenslaufs | Antwort des Nutzers, leer = nicht gezeigt |
| `presentation.show_birth_data` | Geburtsdaten im Lebenslauf | Antwort des Nutzers, Standard `false` |
| `presentation.cv_layout` | Blöcke je Lebenslauf-Seite, Verdichtung | Regel in `references/template.md` (Lebenslauf); das Build-Skript meldet den Füllgrad |
| `presentation.cv_projects` | Titel und Icon des Projektblocks | nur mit Projekten im Lebenslauf; Antwort des Nutzers |

## Offene Punkte

Je Punkt `id`, Frage, `status` (`open`, `resolved`, mit `answer`) und Auswirkung:

- `blocking`: Workflow stoppt
- `non_blocking`: Ausgabe kann weitergehen
- `research_needed`: öffentlich recherchieren

Vor der Profilvorlage sieht der Nutzer eine kompakte Liste aller offenen Punkte.
