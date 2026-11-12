# Bauen, prüfen, freigeben, exportieren

## Werkzeug

`tools/build_mappe.py` (Python-Standardbibliothek; Chromium für A4, optional `pdftoppm` für Seitenbilder). Übersicht: `python3 tools/build_mappe.py --help`.

| Befehl | Zweck |
|---|---|
| `profile-template <profil> [--qa] [--pdf]` | Profilvorlage bauen; `--pdf` = A4-Vorschau `<name>_template.pdf` |
| `application <stelle> [--qa] [--pdf]` | Mappe bauen, Manifest und Ledger aktualisieren; `--pdf` nur nach Freigabe |
| `qa <html>` | Prüfung einer beliebigen Mappe (liegt sie in `<stelle>/application/`, zusätzlich der E-Mail-Entwurf) |
| `preview <html> <ordner>` | A4-PDF und PNG-Seiten zum Ansehen, Ziel immer unter `.tmp/` |
| `validate <profil|stelle>` | Schemaprüfung (braucht `jsonschema`), Asset-Pfade des Profils und bei Bewerbungsweg `email` der E-Mail-Entwurf `application/email.md` |
| `check-duplicate`, `status`, `mark-sent`, `stats` | Ledger, siehe `references/applications.md`; `status sent` gibt es nicht, nur `mark-sent` |

Exit-Codes: 0 ok, 1 Fehler, 2 QA meldet Probleme, 3 Duplikat bzw. `jsonschema` fehlt.

Schemaprüfung ohne installiertes Paket:

```bash
python3 -m venv .tmp/venv && .tmp/venv/bin/pip install jsonschema
.tmp/venv/bin/python tools/build_mappe.py validate profile/<name>
```

## Was `--qa` prüft

- **Überlauf** mit dem QA-Snippet aus der Vorlage (Kommentar `QA-SNIPPET`), bei 1440 × 900 nach dem Laden aller Bilder: Seite läuft über, Element ragt in den unteren Rand, Element seitlich aus dem Satzspiegel (außer Deckblatt), Wort zu lang für seinen Block. Ergebnis muss leer sein.
- **Seitenzahl:** Anzahl der `.page`-Abschnitte = Seiten im A4-PDF (sonst bricht etwas um).
- **Füllgrad der Lebenslauf-Seiten:** nur Information (Richtwert 90–98 %), Grundlage für `presentation.cv_layout` (`references/template.md`, Lebenslauf).
- **Bildschirmbreiten:** kein horizontaler Überlauf bei 1440 (Desktop, Fenster 1440 × 900), 390 (390 × 844) und 375 px (375 × 812). Die Ausgabe nennt immer alle drei Werte: `Horizontaler Überlauf (px): 1440: 0 · 390: 0 · 375: 0`; im Manifest steht `validation.hscroll` je Breite, `hscroll_mobile` ist der größere der beiden Mobilwerte. Headless-Chromium erzwingt mindestens ca. 500 px Fensterbreite, deshalb misst das Skript die beiden Mobilbreiten in einem iframe exakter Breite (Media-Queries gelten dort für die Iframe-Breite); stimmt die gemessene Breite nicht, gilt die Messung als Fehler.
- **E-Mail-Entwurf:** ist der Bewerbungsweg in `job.json` (`application.method`) `email`, muss `application/email.md` existieren, darf nicht leer sein und keine offenen `[Platzhalter]` enthalten (Vorlage `assets/templates/email.md`). Sonst meldet `application --qa` (und `qa <html>` im Bewerbungsordner) einen FEHLER mit Exit-Code 2, `validate` meldet FEHLER, und `application --pdf` verweigert den Export. Das HTML wird trotzdem gebaut (Entwürfe bleiben möglich); die Freigabe (`status … html_approved`) warnt, bis der Entwurf vorliegt. Bei `post`, `portal` und `unknown` ist kein Entwurf nötig. Ergebnis im Manifest: `validation.email_draft` (`ok`, `missing`, `empty`, `placeholders`, `not_required`).
- **Platzhalter:** keine `[GROSSBUCHSTABEN …]` außerhalb von Kommentaren (in der Profilvorlage sind die Platzhalter in Anschreiben und Motivationsschreiben gewollt).
- **Bilder:** alle lokalen Bilder vorhanden.
- **Datenvertrag:** Hinweis auf Klassen, die die Vorlage nicht kennt.
- **Wörter:** Anschreiben und Motivationsschreiben mit Richtwerten.

Das Ergebnis steht im Manifest unter `validation`. Die automatische Prüfung ersetzt nicht den Blick auf die Seiten: Elemente, die innerhalb der Seite aus ihrem Block ragen (z. B. ein langer Name in die Glasleiste), erkennt sie nicht. Deshalb immer:

```bash
python3 tools/build_mappe.py preview "<html>" .tmp/previews/<stelle>
```

und jede PNG-Seite ansehen.

## Bei Problemen

- Überlauf im Anschreiben oder Motivationsschreiben: Text in der `.md` kürzen oder `dichte: dicht` setzen, neu bauen.
- Überlauf im Lebenslauf: `presentation.cv_layout` im Profil anpassen (`references/template.md`, Lebenslauf), Profilvorlage neu bauen und vom Nutzer prüfen lassen.
- Darstellungsfehler, die jede Mappe betreffen: Skill-Vorlage über Tencil ändern, dann Profilvorlage und Mappen neu bauen.
- Nie das generierte HTML bearbeiten.

## Prüfliste vor der HTML-Freigabe

### Daten

- [ ] Profil, `job.json`, Manifest und Ledger gültig (`validate`)
- [ ] Profil vom Nutzer bestätigt, nichts Blockierendes offen
- [ ] Profilvorlage aktuell (kein Hinweis „Profil ist neuer als die Profilvorlage“)
- [ ] Kein Duplikat im Ledger oder vom Nutzer ausdrücklich gewollt
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
- [ ] E-Mail bei Bewerbungsweg `email`: `application/email.md` vorhanden, nicht leer, ohne Platzhalter (QA und `validate` schlagen sonst fehl); richtige Adresse, Betreff mit Referenznummer, Umzugssatz nur bei über 50 km
- [ ] Bewerbungsweg und Frist stimmen; Kontaktdaten überall identisch

### Seiten

- [ ] sechs Abschnitte in der richtigen Reihenfolge, Folgeseiten nur für Lebenslauf oder Nachweise
- [ ] QA ohne Befund, alle Seiten als Bild angesehen
- [ ] Inhaltsangabe und Reiter-Seitenzahlen stimmen
- [ ] keine Fußzeile, keine Dekorlinie, keine Timeline-Linien, kein Firmenname auf dem Deckblatt
- [ ] Fähigkeiten nur mit gespeicherten Skalen; nur Technologien aus dem Profil; alle Logos lokal
- [ ] Nachweise lesbar; Nachweis-Paar nur bei kurzen Dokumenten
- [ ] Desktop- und Mobilansicht (1440, 390, 375 px) von der QA ohne Überlauf; die Bildschirmansicht ist nicht die Druckfassung

## Freigabe

Mappe im Browser zeigen (HTML) und die A4-Seiten als Bilder oder Vorschau-PDF aus `.tmp/`. Dann einzeln fragen:

> Ist die HTML-Fassung für <Firma> inhaltlich und optisch freigegeben? Erst danach erzeuge ich das PDF.

Ohne eindeutiges Ja kein PDF. Schweigen oder „sieht gut aus, aber …“ ist kein Ja. Nach dem Ja:

```bash
python3 tools/build_mappe.py status <stelle> html_approved
```

## PDF

```bash
python3 tools/build_mappe.py application <stelle> --qa --pdf
```

Chromium druckt A4 ohne Kopf- und Fußzeile mit Hintergründen nach `application/bewerbungsmappe - <name>.pdf`; das Manifest wechselt auf `pdf_exported`. Das Skript verweigert den Export ohne Freigabe, mit QA-Befund oder bei Bewerbungsweg `email` ohne gültigen `email.md`-Entwurf. Danach prüfen:

- [ ] Seitenzahl wie im Manifest (`pages`), keine leeren oder abgeschnittenen Seiten
- [ ] Text auswählbar, Bilder scharf, Reihenfolge korrekt
- [ ] Schrift eingebettet als TrueType, nicht Type 3: `pdffonts "<pdf>"` zeigt nur `Inter-…` mit Typ `CID TrueType`; `pdftotext "<pdf>" - | head` liefert lesbaren Text
- [ ] `email.md` nennt den richtigen Anhang

Seit Runde 5 ist Inter statisch in der Vorlage eingebettet; Chromium schreibt die Schrift als TrueType (CID) ins PDF, Text bleibt auswählbar und für ATS auswertbar. Taucht `Type 3` auf, wurde eine andere Schrift (variable Systemschrift) verwendet: Vorlage prüfen.

## Abschlussbericht pro Durchlauf

Für jede Stelle: Firma, Titel, Referenznummer, Ordner, Status, nicht belegte Anforderungen, offene Punkte, Pfade zu HTML, PDF, `email.md` und `kontaktdaten.md`, und der Satz, dass nichts gesendet wurde.

## Datenschutzprüfung

Persönliche Daten bleiben in `profile/` und `.tmp/` (beide gitignoriert). Der Bewerbungshelfer darf öffentliche Anzeigen lesen, öffentliche Firmenkontakte recherchieren und Entwürfe vorbereiten. Er darf nicht ohne ausdrückliche Freigabe senden, Portale ausfüllen, Dateien hochladen oder persönliche Daten an weitere Dienste geben.

Vor jedem Commit:

```bash
git status --short
git ls-files profile/            # nur profile/README.md und .gitkeep
git ls-files | xargs grep -n -i -e '<nachname>' -e '<telefon>' -e '<e-mail>' -e '<straße>'
```

Platzhalter durch die echten Werte des Nutzers ersetzen (aus dem Profil lesen, nicht in eine Datei schreiben). Jeder Treffer blockiert den Commit. Commit und Push nur mit Zustimmung des Nutzers.

## Repository-Prüfung

- keine Profil-, Stellen- oder Bewerbungsdaten im Git; `.tmp/` nicht getrackt
- alle JSON-Dateien im Skill gültig: `python3 -m json.tool <datei>`
- alle Schemas gültig (Draft 2020-12): `python3 -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('<schema>')))"`
- `python3 tools/build_mappe.py --help` läuft
- Symbole der Vorlage reproduzierbar: `python3 tools/devicon_symbols.py` auf den Quellen aus `assets/icons/README.md` liefert die 33 Symbole der SVG-Bibliothek Byte für Byte
- Verweise zwischen SKILL.md, Referenzen und Vorlagen stimmen
