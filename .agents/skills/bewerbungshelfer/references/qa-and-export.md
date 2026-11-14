# Bauen, prüfen, freigeben, exportieren

## Werkzeug

`tools/build_mappe.py` (Python-Standardbibliothek; Chromium für A4, optional `pdftoppm` für Seitenbilder und den Seitenvergleich). Übersicht: `python3 tools/build_mappe.py --help`.

| Befehl | Zweck |
|---|---|
| `master [--check]` | Master-Vorlage `assets/bewerbungsmappe.html` aus `assets/mappe/` bauen; `--check` vergleicht nur (`references/template.md`) |
| `profile-template <profil> [--qa[=fast]] [--pdf]` | Profilvorlage bauen; `--pdf` = A4-Vorschau `<name>_template.pdf` |
| `application <stelle> [--qa[=fast]] [--pdf]` | Mappe aus den Quellen bauen, Manifest und Ledger aktualisieren; `--pdf` nur nach Freigabe |
| `qa <html> [--fast]` | Prüfung einer beliebigen Mappe (liegt sie in `<stelle>/application/`, zusätzlich der E-Mail-Entwurf) |
| `preview <html> <ordner>` | A4-PDF und PNG-Seiten zum Ansehen, Ziel immer unter `.tmp/` |
| `snapshot --save\|--compare <html>…` | Seitenbilder sichern bzw. vergleichen (Abschnitt Seitenvergleich) |
| `rebuild --check <ziel>…` | gespeicherte Dateien gegen ihre Quellen prüfen (Abschnitt Reproduzierbarkeit) |
| `contract` | Vertrag zwischen View-Model, Partials und CSS ausgeben (`references/template.md`, Vertrag prüfen) |
| `validate <profil\|stelle>` | Schemaprüfung, Asset-Pfade des Profils, bei Bewerbungsweg `email` der E-Mail-Entwurf `application/email.md` und offene blockierende Fragen der Stellen (`references/job-search.md`, Abschnitt 8) |
| `status <profil>` | Übersicht aller Stellen mit nächstem Schritt |
| `ledger sync`, `status <stelle> <status>`, `check-duplicate`, `mark-sent`, `drop`, `restore`, `stats` | Stand, Ledger und Ablage, siehe `references/applications.md` |

Exit-Codes: 0 ok, 1 Fehler, 2 QA meldet Probleme bzw. ein Vergleich findet eine Abweichung (`snapshot --compare`, `rebuild --check`, `master --check`), 3 `same_posting` ohne Entscheidung (`check-duplicate`).

Die Schemaprüfung braucht keine Installation: `validate` nutzt `tools/schema_lite.py`. Das Werkzeug kennt genau die Schlüsselwörter, die die Schemas unter `assets/schemas/` verwenden, und bricht bei einem unbekannten ab, statt es zu übergehen; ein neues Schlüsselwort im Schema braucht deshalb zuerst die Ergänzung dort. Ist das Paket `jsonschema` zufällig vorhanden, prüft es zusätzlich mit und meldet eigene Funde mit „(jsonschema)“.

## Was `--qa` prüft

`--qa` ist die volle Prüfung. `--qa=fast` (bei `qa`: `--fast`) lässt das A4-PDF weg und damit den Vergleich der Seitenzahl; das ist die schnelle Schleife beim Ändern der Vorlage. Vor Freigabe und PDF zählt nur die volle Prüfung, `--pdf` verweigert den Export nach `--qa=fast`. Die Prüfung legt keine Dateien neben die Mappe: Chromium startet einmal für alle drei Bildschirmbreiten und einmal für das PDF, das in einem temporären Ordner entsteht.

- **Überlauf** mit der Sonde `assets/mappe/qa.js` (einzige Quelle der Messung; `qa.html` lädt sie mit der Mappe in einem iframe je Breite), bei 1440 × 900 nach dem Laden aller Bilder und Schriften: Seite läuft über, Element ragt in den unteren Rand, Element seitlich aus dem Satzspiegel (außer Deckblatt), Wort zu lang für seinen Block. Ergebnis muss leer sein. Von Hand: die Datei in die Browser-Konsole kopieren und `mappeProbe(window)` aufrufen.
- **Seitenzahl:** Anzahl der `.page`-Abschnitte = Seiten im A4-PDF (sonst bricht etwas um).
- **Füllgrad der Lebenslauf-Seiten:** nur Information (Richtwert 90–98 %), Grundlage für `presentation.cv_layout` (`references/template.md`, Lebenslauf).
- **Bildschirmbreiten:** kein horizontaler Überlauf bei 1440 (Desktop, Fenster 1440 × 900), 390 (390 × 844) und 375 px (375 × 812). Die Ausgabe nennt immer alle drei Werte: `Horizontaler Überlauf (px): 1440: 0 · 390: 0 · 375: 0`; im Manifest steht `validation.hscroll` je Breite, `hscroll_mobile` ist der größere der beiden Mobilwerte. Headless-Chromium erzwingt mindestens ca. 500 px Fensterbreite, deshalb misst das Skript jede Breite in einem iframe exakter Größe (Media-Queries gelten dort für die Iframe-Breite); stimmt die gemessene Breite nicht, gilt die Messung als Fehler.
- **E-Mail-Entwurf:** ist der Bewerbungsweg in `job.json` (`application.method`) `email`, muss `application/email.md` existieren, darf nicht leer sein und keine offenen `[Platzhalter]` enthalten (Vorlage `assets/templates/email.md`). Sonst meldet `application --qa` (und `qa <html>` im Bewerbungsordner) einen FEHLER mit Exit-Code 2, `validate` meldet FEHLER, sobald die Mappe gebaut ist (ab Status `draft`; bei `captured` ist der Entwurf noch nicht fällig), und `application --pdf` verweigert den Export. Das HTML wird trotzdem gebaut (Entwürfe bleiben möglich); die Freigabe (`status … html_approved`) warnt, bis der Entwurf vorliegt. Bei `post`, `portal` und `unknown` ist kein Entwurf nötig. Ergebnis im Manifest: `validation.email_draft` (`ok`, `missing`, `empty`, `placeholders`, `not_required`).
- **Platzhalter:** keine `[GROSSBUCHSTABEN …]` außerhalb von Kommentaren. In der Profilvorlage sind genau die Platzhalter aus `assets/mappe/master.json` (`slots`: Anschreiben und Motivationsschreiben) gewollt; jeder andere zählt als Befund.
- **Bilder:** alle lokalen Bilder vorhanden.
- **Klassen:** Hinweis auf Klassen in der Mappe, die weder eine CSS-Regel noch ein Partial kennt (`references/template.md`, Vertrag prüfen).
- **Wörter:** Anschreiben und Motivationsschreiben mit Richtwerten.

Das Ergebnis steht im Manifest unter `validation`. Die automatische Prüfung ersetzt nicht den Blick auf die Seiten: Elemente, die innerhalb der Seite aus ihrem Block ragen (z. B. ein langer Name in die Glasleiste), erkennt sie nicht. Deshalb immer:

```bash
python3 tools/build_mappe.py preview "<html>" .tmp/previews/<stelle>
```

und jede PNG-Seite ansehen.

## Bei Problemen

- Überlauf im Anschreiben oder Motivationsschreiben: Text in der `.md` kürzen oder `dichte: dicht` setzen, neu bauen.
- Überlauf im Lebenslauf: `presentation.cv_layout` im Profil anpassen (`references/template.md`, Lebenslauf), Profilvorlage neu bauen und vom Nutzer prüfen lassen.
- Darstellungsfehler, die jede Mappe betreffen: Quellen unter `assets/mappe/` ändern (`references/template.md`, visuell über Tencil), dann Master-Vorlage, Profilvorlage und Mappen neu bauen.
- Nie das generierte HTML bearbeiten.

## Seitenvergleich

```bash
python3 tools/build_mappe.py snapshot --save "<html>"       # vor der Änderung
python3 tools/build_mappe.py snapshot --compare "<html>"    # nach dem Neubau
```

`snapshot` druckt die Mappe als A4-PDF und legt jede Seite als Graustufenbild (50 dpi, `pdftoppm`) unter `.tmp/snapshots/<name>/` ab; `--name` vergibt den Namen selbst, mehrere Dateien in einem Aufruf sind möglich. `--compare` nennt je Seite den Anteil geänderter Fläche und den Bereich in Millimetern und endet mit Exit 2, sobald sich eine Seite geändert hat (`--tolerance 0–255` lässt kleine Helligkeitsunterschiede zu). Die Bilder sind ein Vorher-Nachher-Vergleich und liegen nicht im Repository.

Einsatz:

- Änderung an Aufbau oder Technik, die nichts am Aussehen ändern darf: 0 geänderte Seiten für Master-Vorlage, Profilvorlage und eine Mappe.
- Änderung an einer Stelle des Designs: Nur die gemeinten Seiten und Bereiche dürfen erscheinen. Jede weitere Seite ist ein Nebeneffekt und wird geklärt, bevor der Nutzer die Seiten ansieht.

## Reproduzierbarkeit

Dieselben Quellen ergeben dieselbe Datei, Byte für Byte. Das Skript setzt dafür kein Tagesdatum und keinen Zeitstempel in die Mappe.

```bash
python3 tools/build_mappe.py rebuild --check master profile/<name>
```

Der Befehl baut im Speicher und vergleicht mit den gespeicherten Dateien, ohne zu schreiben: `master` für die Master-Vorlage, ein Profilordner für die Profilvorlage und alle gebauten Mappen (samt Bildern unter `application/assets/`), ein Stellenordner für eine Mappe. „WEICHT AB“ heißt: Seit dem Bau wurde eine Quelle geändert oder die Datei von Hand bearbeitet; neu bauen und, wenn die Mappe freigegeben war, erneut freigeben lassen.

Der Test am frischen Klon geht einen Schritt weiter und beweist, dass nichts an lokalen Resten hängt (`.tmp/`, installierte Pakete, nicht versionierte Dateien):

```bash
python3 tools/fresh_clone_test.py [profile/<name>] [--working-tree] [--keep]
```

Er klont das Repository nach `.tmp/fresh-clone/`, kopiert den Profilordner hinein und führt dort mit isoliertem Python `check_repo.py all`, `master --check`, `validate`, `profile-template --qa` und für jede gebaute Mappe `application --qa` aus. Bestanden ist er, wenn `validate` dasselbe meldet wie im Arbeitsordner, jede HTML-Datei byteidentisch ist, HTML- und A4-Seitenzahl übereinstimmen und die Seitenbilder keine Abweichung zeigen. Ohne Schalter prüft er den Stand von `HEAD`; `--working-tree` nimmt alle Dateien dazu, die ein Commit jetzt aufnehmen würde (Prüfung vor dem Commit). Das ist Stufe 1, ohne Modell. Stufe 2 (das Profil mit einem Agenten aus den Interview-Antworten neu aufbauen und vergleichen) gibt es noch nicht.

## Prüfliste vor der HTML-Freigabe

### Daten

- [ ] Profil, `job.json`, Manifest und Ledger gültig, keine blockierende Frage der Stelle `open` (`validate`)
- [ ] Profil vom Nutzer bestätigt, nichts Blockierendes offen
- [ ] Profilvorlage aktuell: `application` meldet nicht „Die Profilvorlage ist nicht aktuell“. Die Mappe entsteht immer aus den Quellen; die Meldung heißt, dass der Nutzer den Stand von Deckblatt, Lebenslauf und Nachweisen noch nicht in der Profilvorlage gesehen hat.
- [ ] Kein ungeklärtes Duplikat: `check-duplicate` endet ohne Exit-Code 3 (`references/applications.md`, Duplikate)
- [ ] Näherungen als `inferred` gespeichert und mit „ca.“ dargestellt
- [ ] Adressen ausgeschrieben („Straße“), zweizeilig, ohne Punkt und Komma (das Skript warnt bei „Str.“)
- [ ] Lebenslauf: nur Einträge mit `show_in_cv` ungleich `false`; Seiten ausgewogen (Füllgrad), Verdichtung nur wo nötig
- [ ] Foto gültig und freigegeben oder der Fotoblock fehlt ganz
- [ ] Asset-Pfade im Profil liegen unter `profile/<name>/assets/` (kein `..`, kein Symlink hinaus, keine gleichen Dateinamen in verschiedenen Ordnern); das Skript bricht sonst mit dem Profilfeld ab

### Inhalt

- [ ] Firma, Titel, Referenznummer stimmen mit der Anzeige überein
- [ ] Ansprechpartner belegt oder bewusst neutrale Anrede; Briefkopf-Zeilen nicht erfunden
- [ ] jede Aussage über den Bewerber im Profil belegt, jede über die Firma in `company_facts`
- [ ] Anschreiben zeigt Fähigkeiten, Motivationsschreiben zeigt Begeisterung; keine Geschichte doppelt
- [ ] Humanizer auf Anschreiben, Motivationsschreiben und E-Mail angewendet (oder Fehlen gemeldet)
- [ ] Wortgrenzen eingehalten bzw. passende Dichte gewählt
- [ ] E-Mail bei Bewerbungsweg `email`: `application/email.md` vorhanden, nicht leer, ohne Platzhalter (QA und `validate` schlagen sonst fehl); richtige Adresse, Betreff mit Referenznummer, Umzugssatz nur, wenn der Suchort nicht der Wohnort ist (`references/writing.md`)
- [ ] Bewerbungsweg und Frist stimmen; Kontaktdaten überall identisch

### Seiten

- [ ] sechs Abschnitte in der richtigen Reihenfolge, Folgeseiten nur für Lebenslauf oder Nachweise
- [ ] QA ohne Befund, alle Seiten als Bild angesehen
- [ ] Inhaltsangabe und Reiter-Seitenzahlen stimmen
- [ ] keine Fußzeile, keine Dekorlinie, keine Timeline-Linien, kein Firmenname auf dem Deckblatt
- [ ] Fähigkeiten nur mit gespeicherten Skalen; nur Technologien aus dem Profil; alle Logos lokal
- [ ] Nachweise lesbar; Nachweis-Paar nur bei kurzen Dokumenten
- [ ] Desktop- und Mobilansicht (1440, 390, 375 px) von der QA ohne Überlauf; die Bildschirmansicht ist nicht die Druckfassung

### Deckblatt, Lebenslauf und Belege

- [ ] Deckblatt: Kurzprofil und Beginn kompakt unter der Farbfläche, kein großer weißer Rest unten
- [ ] Deckblatt: Kapsel „Ausbildung ab …“ steht mittig in ihrer Spalte und im Papierstreifen, nicht bündig unter der Glasleiste
- [ ] Persönliche Daten: zwei Spalten nach Inhalt breit (`repeat(2, auto)`), der Block mittig in der grauen Box, Symbole mittig zur Zeile; Herkunft steht in der ersten Zeile der rechten Spalte neben dem Wohnort, Ort und Land untereinander ohne Komma; Anschrift, E-Mail, Telefon und, falls gesetzt, Herkunft, Geburtsdatum und Führerschein vollständig
- [ ] Chips: jedes Symbol entspricht der Zuordnung in `assets/icons/README.md`; eine Id (`i-…`, `dv-…`, `si-…`), die in `assets/mappe/icons.svg` fehlt, bricht den Bau ab
- [ ] Skala: Block steht direkt unter „Fähigkeiten“, vor der ersten Gruppe; der Titel „Skala 1–5“ steht links und ist vertikal mittig auf der Höhe der Leisten (nicht oben bündig); die fünf Spalten bleiben gleich breit
- [ ] Belege: Projektfoto nur bei Titel gleich `projects[].name` und Bild mit `consent` und `valid`; sonst kein Foto. In der fertigen Mappe steht kein `[PROJEKTFOTO]`
- [ ] Ohne Projektfotos baut die Mappe fehlerfrei (Fallback); die Belege bleiben mit Text

## Freigabe

Mappe im Browser zeigen (HTML) und die A4-Seiten als Bilder oder Vorschau-PDF aus `.tmp/`. Dann einzeln fragen:

> Ist die HTML-Fassung für <Firma> inhaltlich und optisch freigegeben? Erst danach erzeuge ich das PDF.

Ohne eindeutiges Ja kein PDF. Schweigen oder „sieht gut aus, aber …“ ist kein Ja. Nach dem Ja:

```bash
python3 tools/build_mappe.py status <stelle> html_approved
```

Der Befehl hält im Manifest fest, was freigegeben wurde: `approved_sha256` ist die Prüfsumme über die HTML-Datei und jedes eingebundene Bild. Freigegeben ist genau dieser Stand. Entspricht die gespeicherte Mappe nicht mehr ihren Quellen (nach dem Bau wurde etwas geändert), lehnt der Befehl ab: erst neu bauen, zeigen, erneut fragen. Ändert sich danach ein Text, das Profil, die Vorlage oder ein Bild, hat der nächste Bau eine andere Prüfsumme: Der Status fällt auf `draft` zurück, und die Freigabe ist neu einzuholen. Eine Freigabe ohne Prüfsumme (ältere Manifeste) gilt nicht als Freigabe.

## PDF

```bash
python3 tools/build_mappe.py application <stelle> --qa --pdf
```

Chromium druckt A4 ohne Kopf- und Fußzeile mit Hintergründen nach `application/bewerbungsmappe - <name>.pdf`, mit Lesezeichen aus den Überschriften, wo die Chromium-Version das kann; das Manifest wechselt auf `pdf_exported`. Das Skript baut die Mappe vorher neu aus den Quellen und verweigert den Export:

- ohne Freigabe, oder wenn die neu gebaute Mappe nicht der Prüfsumme der Freigabe entspricht
- mit QA-Befund oder nach `--qa=fast`
- bei Bewerbungsweg `email` ohne gültigen `email.md`-Entwurf
- wenn das Briefdatum (`datum` in `anschreiben.md`) älter als 7 Tage ist. Dann `datum` auf den Versandtag setzen, neu bauen und erneut freigeben lassen; das geänderte Datum ändert die Mappe.

Danach prüfen:

- [ ] Seitenzahl wie im Manifest (`pages`), keine leeren oder abgeschnittenen Seiten
- [ ] Text auswählbar, Bilder scharf, Reihenfolge korrekt
- [ ] Schrift eingebettet als TrueType, nicht Type 3: `pdffonts "<pdf>"` zeigt nur `Inter-…` mit Typ `CID TrueType`; `pdftotext "<pdf>" - | head` liefert lesbaren Text
- [ ] `email.md` nennt den richtigen Anhang

Inter ist statisch in jeder Mappe eingebettet; Chromium schreibt die Schrift als TrueType (CID) ins PDF, Text bleibt auswählbar und für ATS auswertbar. Taucht `Type 3` auf, wurde eine andere Schrift (variable Systemschrift) verwendet: `assets/mappe/fonts.css` und `tokens.css` prüfen.

Die Scans tragen im Druck einen weichen Schatten (`filter: drop-shadow` an `.document-stage img`). Chromium rastert sie deshalb mit 300 dpi ins PDF. Der Filter bleibt vorerst: Ohne ihn bettet Chromium die Scans in Originalauflösung ein, das PDF wächst bei zwei Scans von ca. 1,2 MB auf ca. 3 MB, und die Seiten sehen anders aus. Wer ihn entfernt, verkleinert die Scans zugleich beim Import.

## Abschlussbericht pro Durchlauf

Für jede Stelle: Firma, Titel, Referenznummer, Ordner, Status, nicht belegte Anforderungen, offene Punkte, Pfade zu HTML, PDF, `email.md` und `kontaktdaten.md`, und der Satz, dass nichts gesendet wurde.

## Datenschutzprüfung

Persönliche Daten bleiben in `profile/` und `.tmp/` (beide gitignoriert). Der Bewerbungshelfer darf öffentliche Anzeigen lesen, öffentliche Firmenkontakte recherchieren und Entwürfe vorbereiten. Er darf nicht ohne ausdrückliche Freigabe senden, Portale ausfüllen, Dateien hochladen oder persönliche Daten an weitere Dienste geben.

Vor jedem Commit:

```bash
python3 tools/check_repo.py all
```

Der Befehl braucht nur die Python-Standardbibliothek. Jeder Befund blockiert den Commit. Commit und Push nur mit Zustimmung des Nutzers.

- `privacy` baut seine Suchmuster aus jedem Profil unter `profile/`: Vor- und Nachname, Telefon in jeder Schreibweise, E-Mail, eigene Domain der E-Mail-Adresse (nicht bei großen Anbietern), Straße, PLZ mit Ort, Geburtsdatum, Geburtsort. Weitere Suchtexte (z. B. zusätzliche Domains) stehen zeilenweise in der gitignorierten Datei `profile/privacy-needles.txt`.
- Geprüft werden alle Dateien, die Git aufnimmt (getrackt oder neu und nicht ignoriert), ihre Pfade und der Staging-Diff. Dateien unter `profile/` (außer `README.md` und `.gitkeep`) und `.tmp/` dürfen nie dabei sein.
- Die Ausgabe nennt Datei, Zeile und Art des Treffers, nie den Wert.
- Ausnahmen stehen ausschließlich in der Liste `ALLOW` in `tools/check_repo.py` und brauchen die Zustimmung des Nutzers.
- Beispiele in Dokumentation und Vorlagen bleiben neutral: „Max Mustermann“, „Musterstraße 6“, „Krakau, Polen“.

Die Prüfung läuft an zwei Stellen von selbst:

- **Git:** `tools/hooks/pre-commit`, einmal pro Klon eingeschaltet mit `git config core.hooksPath tools/hooks`.
- **Claude Code:** als Hook `PostToolUse` für `Edit|Write` in `.claude/settings.json` mit dem Befehl `python3 "$CLAUDE_PROJECT_DIR/tools/check_repo.py" hook`. Er prüft nur die gerade geschriebene Datei, schweigt ohne Befund und meldet einen Befund sofort an den Agenten. Dateien unter `profile/<name>/` und `.tmp/` überspringt er. Nach einer Änderung unter `assets/mappe/`, `assets/fonts/` oder an `assets/bewerbungsmappe.html` läuft zusätzlich `template`: Der Hook meldet, bis `build_mappe.py master` die Master-Vorlage neu gebaut hat.

## Repository-Prüfung

`python3 tools/check_repo.py all` deckt ab:

- `privacy`: siehe Datenschutzprüfung
- `stray`: jede Datei liegt an einem erlaubten Ort (Liste `ALLOWED` in `tools/check_repo.py`), keine leeren Dateien, keine Reste wie `*.orig`, `*.bak`, `EOF` oder Namen mit Leerzeichen. Eine neue Dateiart im Repository braucht zuerst einen Eintrag in `ALLOWED`.
- `schemas`: alle JSON-Dateien lesbar; Schemas in sich stimmig (Verweise, Pflichtfelder, Aufzählungen, Muster); die Vorlagen in `assets/templates/` passen in Feldern, Typen und Aufzählungen zu ihrem Schema
- `template`: die Master-Vorlage `assets/bewerbungsmappe.html` entspricht Byte für Byte dem Bau aus `assets/mappe/` (sonst: Quellen ändern, nie die Datei, dann `build_mappe.py master`); jedes Partial trägt sein `data-part` und bindet nur vorhandene Partials ein (`build_mappe.py contract`)

Dazu von Hand:

- vor einem Commit, der Vorlage, Build-Skript oder Schemas berührt: `python3 tools/fresh_clone_test.py --working-tree` (Abschnitt Reproduzierbarkeit)
- alle Schemas gültig nach Draft 2020-12 (nur mit dem optionalen Paket `jsonschema`): `.tmp/venv/bin/python -c "import json,sys,jsonschema; [jsonschema.Draft202012Validator.check_schema(json.load(open(f))) for f in sys.argv[1:]]" .agents/skills/bewerbungshelfer/assets/schemas/*.json`
- `python3 tools/build_mappe.py --help` läuft
- Symbole reproduzierbar: `python3 tools/devicon_symbols.py` auf den Quellen aus `assets/icons/README.md` liefert die 34 Logo-Symbole (25 Devicon, 9 Simple Icons) in `assets/mappe/icons.svg` Byte für Byte
- Verweise zwischen SKILL.md, Referenzen und Vorlagen stimmen
