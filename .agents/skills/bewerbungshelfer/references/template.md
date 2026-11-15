# Vorlage, Seiten und Design

Das Design heißt „Glisse“. Aussehen und Markup der Mappe stehen an genau einer Stelle: in den Quellen unter `assets/mappe/`. Daraus baut `tools/build_mappe.py` drei Arten von Dateien, jede eine eigenständige HTML-Datei ohne externe Ressourcen:

| Datei | Befehl | Inhalt |
|---|---|---|
| Master-Vorlage `assets/bewerbungsmappe.html` | `build_mappe.py master` | nur Platzhalter in eckigen Klammern, keine Daten; liegt im Repository für Tencil und die Vorschau |
| Profilvorlage `profile/<name>/assets/profile/<name>_template.html` | `build_mappe.py profile-template` | echtes Profil; Anschreiben und Motivationsschreiben als Platzhalter |
| Mappe `<stelle>/application/bewerbungsmappe - <name>.html` | `build_mappe.py application` | Profil, `job.json` und die Texte der Stelle |

Alle drei sind Bauergebnisse und werden nie von Hand bearbeitet, auch die Master-Vorlage nicht. Visuell geprüft wird über Tencil (`references/tencil.md`).

## Quellen der Vorlage

```
assets/mappe/
  tokens.css     Farben, Maße, Schriftgrößen, Glasrezepte (nur :root)
  mappe.css      Papier: Grundregeln, ein Block je Seite, zuletzt @media print
  screen.css     Bildschirm: Leiste, Navigation, schmale Fenster; nie im PDF
  fonts.css      @font-face für Inter; die Dateien aus assets/fonts/ setzt der Bau als Base64 ein
  icons.svg      alle Symbole, eines pro Zeile; der Bau bettet nur die verwendeten ein
  master.json    Platzhalter-Modell: pages = Master-Vorlage, slots = Platzhalter der Profilvorlage
  limits.json    Zahlen und Grenzen, die das Skript liest (Wortzahlen, Fenstergrößen, Schwellen)
  qa.js, qa.html Überlauf- und Füllgradprüfung (references/qa-and-export.md)
  partials/      Markup, ein Partial pro Datei
```

<!-- rule: template.sources -->
| Was soll sich ändern? | Wo |
|---|---|
| Farbe, Schriftgröße, Abstand, Maß | `tokens.css`; fehlt ein Token, der Block des Partials in `mappe.css` |
| Zahl, nach der das Skript entscheidet oder die es meldet (Wortzahl, Schwelle, Fenstergröße) | `limits.json`; die Doku nennt den Schlüssel als `limits:<pfad>` |
| Aufbau einer Seite oder eines Elements | das Partial in `partials/` und sein Block in `mappe.css` |
| Verhalten auf dem Bildschirm (mobil, Leiste) | `screen.css` |
| Neues Symbol | `icons.svg` (Ablauf in `assets/icons/README.md`) |
| Platzhaltertext der Master- oder Profilvorlage | `master.json` |
| Was auf einer Seite steht (Daten, Reihenfolge, Sichtbarkeit) | Profil, `job.json`, Texte; neue Regel: View-Model in `tools/build_mappe.py` |

Jede Änderung an den Quellen läuft über die Warteschlange (Regel `pins.one-writer` in `references/tencil.md`). Danach: `python3 tools/build_mappe.py master`, dann Profilvorlage und betroffene Mappen neu bauen. `tools/check_repo.py` (Prüfung `template`) schlägt fehl, solange die Master-Vorlage nicht dem Bau aus den Quellen entspricht; das fängt auch eine direkte Änderung an `assets/bewerbungsmappe.html` ab.

### Partials und View-Model

- Die Partials sind Mustache in einer kleinen Teilmenge (`tools/mustache_lite.py`): `{{x}}` Wert (HTML-escaped), `{{{x}}}` roh (nur CSS, Schrift, Symbole), `{{#x}}…{{/x}}` Abschnitt, `{{^x}}…{{/x}}` Abschnitt bei leerem Wert, `{{> name}}` anderes Partial, `{{! … }}` Kommentar.
- `tools/build_mappe.py` baut pro Seite ein dict (View-Model, Funktionen `…_view`) und enthält kein HTML. `document.html` ist der Rahmen, `body.html` reiht die Seiten: `cover`, `letter`, `cv`, `motivation`, `evidence`. Kleinere Partials: `section-head`, `letter-line`, `timeline-item`, `chip`, `bars`, `text`, `chrome`.
- Strenge Schlüssel: Ein Name wird nur im aktuellen Abschnitt gesucht, nie in einer äußeren Ebene. Nennt ein Partial einen Schlüssel, den das View-Model nicht setzt, bricht der Bau mit Partial, Zeile und Schlüssel ab. Jeder Schlüssel ist deshalb immer gesetzt, notfalls mit `null`.
- Die Master-Vorlage entsteht aus denselben Partials mit `master.json`. Markup gibt es damit nur einmal; Master-Vorlage und gebaute Mappen können nicht auseinanderlaufen.
- Ein neuer Schlüssel braucht drei Stellen im selben Durchgang: das Partial, die `…_view`-Funktion und `master.json`.

### Attribute für Pins

Jede gebaute Datei trägt zwei Attribute, die einen Pin zur richtigen Quelle führen. Sie ändern nichts am Aussehen.

| Attribut | Bedeutung | Steht an |
|---|---|---|
| `data-part="<name>"` | Partial `assets/mappe/partials/<name>.html`, das das Element zeichnet: Quelle für das **Aussehen** | Wurzelelement jedes Partials |
| `data-origin="<quelle>"` | Herkunft des **Inhalts** | Elemente mit Inhalt aus Daten |

Werte von `data-origin`:

| Wert | Quelle |
|---|---|
| `profile:<pfad>` | `<name>_profile.json`, z. B. `profile:person.phone`, `profile:experience[<id>]`, `profile:skills.groups[0].items[2]` |
| `job:<pfad>` | `job_information/job.json` der Stelle, z. B. `job:contact` |
| `text:<datei>#<stelle>` | `text_generation/<datei>`: Kopffeld (`#datum`, `#betreff`), Absatz (`#p3`), `#einstieg`, Beleg (`#beleg2`) |
| `master:<pfad>` | `assets/mappe/master.json` (Platzhalter) |
| `build:<name>` | Funktion oder Konstante in `tools/build_mappe.py` (berechnete Angaben, z. B. Seitenzahlen der Inhaltsangabe) |

Für ein Element gilt das nächste Attribut an ihm selbst oder an einem Vorfahren. Der Vorschau-Server (`tools/serve_template.py`) löst beide zu Datei und Zeile auf (`references/tencil.md`).

### Vertrag prüfen

```bash
python3 tools/build_mappe.py contract
```

Der Befehl leitet den Vertrag aus den Dateien ab: je Partial `data-part`, die Schlüssel, die es vom View-Model erwartet, seine Klassen und eingebundenen Partials; dazu Klassen ohne CSS-Regel und CSS-Klassen, die kein Partial fest nennt. Er ersetzt jede von Hand gepflegte Klassenliste. Exit 1, wenn ein Partial sein `data-part` nicht trägt oder ein eingebundenes Partial fehlt. Die QA meldet zusätzlich Klassen in einer gebauten Mappe, die weder eine CSS-Regel noch ein Partial kennt.

## Aufbau der Mappe

Sechs Abschnitte, jeder beginnt auf einer eigenen A4-Seite:

| Nr. | Abschnitt | Herkunft | pro Stelle neu? |
|---|---|---|---|
| 1 | Deckblatt | Profil (`portfolio`, `person`, `goal`) | nein |
| 2 | Anschreiben | `anschreiben.md`, `job.json`, Absender aus dem Profil | ja |
| 3 | Lebenslauf | Profil | nein |
| 4 | Motivationsschreiben | `motivationsschreiben.md` | ja |
| 5 | Zertifikate | Profil `evidence` (`certificate`) | nein |
| 6 | Zeugnisse | Profil `evidence` (`school_report`, `work_reference`) | nein |

Folgeseiten nur für eine Lebenslauf-Fortsetzung oder weitere Nachweise. Sie tragen den Abschnittstitel mit „Fortsetzung“, dieselbe `data-section`-Zahl und eine fortlaufende Seitenzahl. Inhaltsangabe auf dem Deckblatt und Bildschirmnavigation nennen die Startseite jedes Abschnitts; das Skript rechnet das aus.

Die Seiten haben feste A4-Höhe mit `overflow: hidden`. Zu langer Inhalt verschwindet still, deshalb ist die Überlaufprüfung Pflicht (`references/qa-and-export.md`).

## Designsystem

### Haltung

Modern, ruhig, Apple-nah. Weißes Papier, ein Akzent, klare Typografie, viel Weißraum, echte Nachweise statt Dekoration. Die A4-Fassung ist die Abnahmefläche; das responsive Bildschirmlayout darf nie ins PDF durchschlagen.

### Zwei Ebenen

- **Inhaltsebene:** weißes Papier, Text, Scans, helle Fläche `--surface` (#f5f5f7). Nie Glas.
- **Funktionsebene (Glisse):** Deckblatt-Leiste (Kontakt, optional Foto, Inhalt), Registerreiter mit Seitenzahl, Bildschirmleiste, Seitennavigation am Bildschirmrand.

Glas nur auf der Funktionsebene, höchstens eine große Glasfläche pro Seite, nie hinter Fließtext oder Scans. Druckfest: Verlaufsfüllung, helle Innenkante, Haarlinie, weicher Schatten; `backdrop-filter` nur zusätzlich auf dem Bildschirm. Fallbacks für `prefers-reduced-transparency` (deckende Fläche) und `prefers-contrast: more` (kräftigere Kanten).

### Farben

- Papier `#ffffff`, Text `#1d1d1f` (16,8:1), gedämpft `#424245`, leise `#6e6e73` (5,1:1)
- Akzent Petrol `#0b4f5c` (9,2:1), Fläche `#f5f5f7`
- Deckblatt: petrolfarbener Farbraum nur im oberen Teil (`#0f4753` → `#0d4250` → `#0a2c35`) mit weichen Lichtflecken; Text darauf weiß bzw. 74 % Weiß (≥ 6,5:1). Darunter weißes Papier: Kurzprofil links, Beginn als Kapsel (siehe Papierzone unten); oben 8 mm, unten 9 mm Innenabstand. Die Farbfläche nimmt den restlichen Platz, es bleibt kein großer weißer Rest unter dem Kurzprofil.

Den Akzent nur ändern, wenn Text darauf und daneben mindestens 4,5:1 erreicht.

### Typografie

- Eine Familie: **Inter 4.1** (SIL OFL 1.1), Stapel `"Inter", "Helvetica Neue", "Segoe UI", "Noto Sans", Arial`. Inter ist in jeder gebauten Datei eingebettet (`assets/mappe/fonts.css`, Block `<style id="font-inter">` am Ende des Kopfs, data-URIs), keine externen Font-Requests, keine Systeminstallation nötig.
- Statische Schnitte 400, 500, 600, 700 (keine variable Schrift): Chromium bettet sie im PDF als TrueType (CID) ein, Text bleibt auswählbar und auswertbar. Nur diese vier Gewichte verwenden. Untermenge Latin + Latin Extended (deutsche Umlaute, ß, ș ț ă, typografische Anführungszeichen, Gedankenstrich).
- Quelldateien und Lizenz: `assets/fonts/` (`Inter-*.woff2`, `OFL.txt`, `README.md`).
- SF Pro bewusst nicht im Stapel (Lizenz erlaubt keine Einbettung in eigene Dokumente); `-apple-system`/`BlinkMacSystemFont` ebenfalls nicht (Chromium unter Linux löst sie zu Liberation Sans auf).
- Hierarchie über Größe und Gewicht: Name ca. 54 pt, Abschnittstitel 25 pt, Betreff 16,5 pt, Einstieg 15,5 pt, Fließtext 9,6 pt, Nebentext 8,5 pt, Chips 7,5 pt, Bildunterschriften 7,4 pt. Überschriften ab 12 pt in 700, kleine Titel und Hervorhebungen in 600, Akzentzeilen in 500. Keine Serifen, keine Großbuchstaben-Labels. Fließtext nie unter 9 pt.

### Seiten

<!-- rule: design.fixed -->
- A4 210 × 297 mm, `@page { size: A4; margin: 0 }`, Satzspiegel 20 mm seitlich, 24 mm oben, 20 mm unten.
- **Keine Fußzeile.** Die Seitenzahl steht im Registerreiter (`.folio`), schlicht `1`, `2`, … ohne führende Null und ohne Gesamtzahl. Der Name steht auf Deckblatt, im Briefkopf und im Lebenslauf.
- Registratur: sechs Spalten über die Seitenbreite; `data-section="1…6"` setzt den Reiter in die Spalte seines Abschnitts. Folgeseiten bekommen automatisch einen hellen Reiter.
- Keine vertikalen Dekorlinien, keine Timeline-Verbindungslinien, kein Firmenname auf dem Deckblatt.

### Deckblatt

Zwei Zonen:

- **Farbraum** `.cover-stage` oben (ca. drei Viertel der Seite, so hoch wie die Seite minus Papierzone): Kennung „Bewerbungsmappe“ oben links, Name unten links, darunter der Beruf. Rechts unten die Glasleiste mit optionalem Foto (4:5), Kontakt und Inhaltsangabe; sie ist so hoch wie ihr Inhalt. Die Glasleiste ist leicht gehalten (wenig Füllung, feine Kante, kurzer Schatten).
- **Papierzone** `.cover-intro` unten, ohne feste Mindesthöhe (Höhe = Inhalt, oben 8 mm, unten 9 mm): links das Kurzprofil in dunkler Schrift, rechts der Beginn „Ausbildung ab …“ als Kapsel. Die Kapsel steht mittig in ihrer Spalte und mittig im Papierstreifen (`.cover-start { justify-self: center; align-self: center; }`), nicht bündig unter der Glasleiste. Fließtext steht damit nie auf dunklem Grund.

<!-- rule: cover.name-size -->
Namensgröße: Die Klasse am Namen richtet sich nach dem längsten Namensteil. Ab 11 Zeichen (`limits:cover.name_long_from_chars`) setzt das Skript `is-long`, ab 14 Zeichen (`limits:cover.name_xlong_from_chars`) `is-xlong`, darunter keine Klasse. Bei Doppelnamen zählt jeder Teil für sich, der vordere mit seinem Bindestrich.

<!-- rule: contact.email-wrap -->
Kontakt in der Leiste: Telefon, E-Mail, Anschrift (zweizeilig). E-Mail-Adressen mit mehr als 24 Zeichen (`limits:contact.email_wrap_above_chars`) bricht das Skript mit `<wbr>` nach „@“ und vor Punkten um, auch im Briefkopf und im Lebenslauf.

<!-- rule: cover.photo-crop -->
Foto nur, wenn es gültig und freigegeben ist (Regel `person.photo` in `references/profile-schema.md`); sonst entfällt der Block ersatzlos (kein Platzhalterrahmen). Rahmen 4:5, Ausschnitt über `--photo-x`, `--photo-y`, `--photo-zoom` (Profil `photo.focus`): Augen bei ca. 35–40 % der Rahmenhöhe, Zoom höchstens ca. 1,2, Bild mindestens 600 × 750 px.

### Anschreiben

Geschäftsbrief nach DIN-5008-Zonen, angepasst für den E-Mail-Versand (keine Falzmarken, keine Rücksendezeile):

- Symmetrischer Briefkopf: links Empfänger, rechts Absender, je sechs Zeilen mit Icon auf einem gemeinsamen Raster: Firma (fett) · Anrede + Name · Straße · PLZ Ort · Telefon · E-Mail. Die Firmenzeile des Absenders bleibt leer. Die Anrede vor dem eigenen Namen kommt aus `person.salutation` (leer = nur Name); sie ist eine Entscheidung des Nutzers. Fehlt beim Empfänger eine belegte Angabe, bleibt eine leere Zeile (`is-empty`) stehen; nichts erfinden. Ohne Ansprechpartner steht die Abteilung in der Namenszeile.
- Straße ausgeschrieben („Straße“, nicht „Str.“), Straße und PLZ/Ort zweizeilig ohne Punkt und Komma, für Absender und Empfänger, in Profil und `job.json` schon so gespeichert. Das Build-Skript warnt bei „Str.“ oder Satzzeichen am Ende. <!-- rule: address.format -->
- Ort (Wohnort) und Datum („11. November 2026“) rechtsbündig mit Kalender-Icon zwischen Briefkopf und Betreff.
- Betreff zweistufig in gemischter Schreibung (Entscheidung des Nutzers, Versalien wirken bei langen Berufsbezeichnungen laut): Einleitung klein in Akzentfarbe, darunter groß der Beruf, darunter optional die BA-Referenznummer. Die Variante `.letter-subject.is-caps` (Einleitung in Versalien) existiert im CSS, das View-Model setzt sie aber nicht; sie wäre eine Änderung an Partial, Skript und Profil.
- Brieftext: Umfang nach Regel `letter.length` in `references/writing.md`; mit `dichte: dicht` setzt das Skript `.letter-copy.is-dense`.
- Unterschrift als Bild (12 mm hoch, höchstens 45 mm breit) nur mit gültiger, freigegebener Datei; darunter Name und Ort.

### Lebenslauf

- Reihenfolge der Blöcke: Praktische Erfahrung, Schulbildung, Fähigkeiten, Sprachen (Sprachen immer zuletzt, auch beim Umbrechen auf die Fortsetzung). Optionaler Block „Eigene Projekte“ irgendwo nach der Erfahrung, wo er auf die Seite passt.
- Kopf: Name, „Ausbildungsziel: …“, persönliche Daten zweispaltig (Spalten nach Inhalt breit, `repeat(2, auto)`), der Block horizontal und vertikal mittig in der grauen Box, Symbol und Text je Zeile mittig. Linke Spalte: Anschrift (zweizeilig), E-Mail, Telefon. Rechte Spalte: Herkunft mit `i-map` (aus `person.birth_place`, Ort und Land untereinander nach Regel `person.birth-place` in `references/profile-schema.md`) in der ersten Zeile neben dem Wohnort, darunter Geburtsdatum mit `i-cake`, optional „Führerschein Klasse B“ mit `i-car` aus `person.driving_license`; mit allen Angaben sind es 3 + 3 Zeilen. Kein Kurzprofil im Lebenslauf (steht auf dem Deckblatt). <!-- rule: cv.personal-data -->
- Praktische Erfahrung: neueste zuerst; Datum links in eigener Spalte, rechts Organisation, Ort, Rolle · Art, Aufgaben. Näherungen mit „ca.“.
- Schulbildung: Einrichtung, Ort, „Schulform · Profil“, Detailzeile nur „Abschluss: …“ bzw. „Abschluss: …, voraussichtlich MM/JJJJ“. Keine Zeugnis- oder Klassendetails. Neueste zuerst. Einträge mit `education[].show_in_cv: false` entfallen (Grundschulen: Regel `education.primary-school` in `references/profile-schema.md`); das Skript meldet die ausgeblendeten Einträge.
- Sprachen: Balken mit Niveauwort darunter, keine Belegzeile.
- Fähigkeiten: Gruppen untereinander, Gruppentitel mit Linien-Icon; jede Zeile = Kategorie (optional kleiner Zusatz), Technik-Chips, Skala. Bis ca. 6 Chips je Zeile passen bei üblichen Namen in eine Zeile; längere Reihen brechen ruhig in eine zweite Zeile um (kostet ca. 4–5 mm Höhe). Keine Prozentwerte.
- Skala oben im Block Fähigkeiten, direkt unter der Überschrift: Die Skalen-Legende beginnt links mit dem Titel „Skala 1–5“. Der Titel ist vertikal mittig zu den Skalenleisten ausgerichtet (`.skill-legend-title { align-self: center; margin: 0; }`), weil das Grid `align-items: start` hat und der Titel sonst oben hängt. Daneben fünf gleich breite Spalten mit Musterleiste in Originalgröße und Bezeichnung (8,5 pt, gedämpft): Lernwunsch, Grundkenntnisse, sicher, routiniert, sehr sicher. <!-- rule: cv.scale-legend -->
- Eigene Projekte / Homelab (optional, Block `projects`): nur Projekte mit `show_in_cv: true`, Reihenfolge wie im Profil. Zeile wie bei der Erfahrung: Zeitraum links (leer, wenn unbekannt; „laufend“ bei `is_current` ohne Datum), Projektname, ein Satz aus `cv_summary` (sonst `own_role`), darunter die Werkzeuge als Chips (`chips`, sonst Text-Chips aus `tools`). Titel und Icon aus `presentation.cv_projects` (Standard „Eigene Projekte“, `i-layers`). Platzbedarf: ca. 12 mm Kopf plus ca. 18–20 mm je Eintrag mit einer Zeile Text und einer Chipzeile; höchstens zwei bis drei Einträge. <!-- rule: cv.projects-block -->
- Aufteilung auf Seiten (`presentation.cv_layout`, Blocknamen `experience`, `education`, `projects`, `skills`, `languages`): Die QA meldet den Füllgrad jeder Lebenslauf-Seite („Füllgrad Lebenslauf: S3 95 % (+13.9 mm) · …“, Anteil des Satzspiegels, Rest in mm; negativ = Überlauf). Vorgehen: <!-- rule: cv.layout -->
  1. Standard ist eine Seite mit allen Blöcken. Läuft sie über, ganze Blöcke auf eine Fortsetzungsseite verschieben (Reihenfolge beibehalten, Sprachen zuletzt) und die Seiten etwa gleich füllen, Richtwert 90–98 % (`limits:cv.fill_target_percent`).
  2. Bei sehr vielen Stationen einen Block teilen.
  3. Verdichten (`cv_layout.compact`) nur auf einer Seite, die sonst überläuft: auf der volleren Seite (`[false, true]`) oder auf allen (`true`). Eine Seite, die ohne Verdichtung passt, bleibt unverdichtet.
  4. Zuletzt Beschreibungen im Profil kürzen.
  Ändert sich der Inhalt (Eintrag ein- oder ausgeblendet, Projekt, Fähigkeit), die Aufteilung neu prüfen. Ist der Richtwert nicht erreichbar (die zweite Seite bleibt deutlich leerer, weil ein Block nicht auf die erste passt), ist das in Ordnung; die freie Höhe dient dann dem nächsten Block (z. B. „Eigene Projekte“).

### Motivationsschreiben

Redaktioneller Einstieg (ein Satz, groß), daneben die Belege-Spalte (66 mm breit) mit drei Einträgen. Jeder Beleg: Icon und Titel, Text, darunter das Projektfoto im Format 4:3 in voller Breite. Reihenfolge je Beleg: Projekt → Details → Projektfoto. Ob ein Foto erscheint, bestimmt Regel `project.photo` in `references/profile-schema.md`; ohne Foto bleibt der Beleg ohne Bild und ohne Platzhalter. Kein Zitat-Icon. Umfang nach Regel `motivation.length` in `references/writing.md`; mit `dichte: dicht` setzt das Skript `.motivation-copy.is-dense`. Abschluss mit Name und Ort, ohne Unterschriftsbild.

### Zertifikate und Zeugnisse

Titel und Aussteller über dem Scan, der Scan füllt die Resthöhe, darunter „Original-Scan“ (bzw. „Kopie“, „Digitales Original“) und „Ausgestellt am TT.MM.JJJJ“. Kein Badge, kein Zähler, keine Wiederholung von Schule oder Klasse.

- Ein Nachweis pro Seite im Regelfall. Reihenfolge wie im Profil.
- Zwei Nachweise nebeneinander (`.evidence-grid.is-pair`, Profil `pair: true`) nur für kurze, gut lesbare Dokumente (je ca. 80 mm breit), nie für textreiche Zeugnisse. <!-- rule: evidence.pair -->
- Weitere Nachweise auf Folgeseiten.
- Fehlt ein Nachweis, steht „Liegt noch nicht vor“.

### Icons und Logos

<!-- rule: icons.list -->
- Linien-Icons (`<svg class="icon"><use href="#i-…"/></svg>`): `i-phone`, `i-mail`, `i-pin`, `i-calendar`, `i-user`, `i-folder`, `i-graduation`, `i-briefcase`, `i-terminal`, `i-server`, `i-network`, `i-scan`, `i-list`, `i-badge`, `i-globe`, `i-branch`, `i-layers`, `i-wrench`, `i-building`, `i-home`, `i-cake`, `i-map`, `i-car` (Führerschein), `i-monitor`, `i-code`, `i-cpu`, `i-cable` (LAN/WAN), `i-router` (Cisco IOS CLI), `i-shield` (Firewall), `i-waypoints` (TCP/IP). `i-cable`, `i-router`, `i-shield` und `i-waypoints` stammen aus Lucide (ISC, Version 0.469.0, Lizenz in `assets/icons/LICENSES.md`). Ein Icon trägt nie allein eine Information.
- Technologie-Logos lokal als einfarbige `<symbol>` eingebettet (`<svg class="logo"><use href="#dv-…"/></svg>`), im Chip immer neben dem Namen. Verfügbar:

  | id | Technik | Quelle |
  |---|---|---|
  | `dv-windows11`, `dv-apple`, `dv-linux`, `dv-archlinux`, `dv-debian`, `dv-android` | Betriebssysteme (auch iOS über `dv-apple`) | Devicon |
  | `dv-docker`, `dv-podman`, `dv-kubernetes`, `dv-ansible` | Container, Automatisierung (Dockform über `dv-docker`) | Devicon |
  | `dv-nixos` | NixOS/Nix | Devicon (plain) |
  | `dv-git`, `dv-github`, `dv-bash` | Versionierung, Shell | Devicon |
  | `dv-cloudflare` | Cloudflare (auch Tunnel) | Devicon |
  | `dv-html5`, `dv-css3`, `dv-javascript`, `dv-typescript`, `dv-rust`, `dv-python`, `dv-nodejs`, `dv-flutter`, `dv-swift`, `dv-react` | Entwicklung (auch React Native über `dv-react`) | Devicon |
  | `si-wireshark` | Wireshark | Simple Icons |
  | `si-wireguard` | WireGuard | Simple Icons |
  | `si-tailscale` | Tailscale | Simple Icons |
  | `si-cisco` | Cisco (z. B. Packet Tracer) | Simple Icons |
  | `si-proxmox` | Proxmox VE | Simple Icons |
  | `si-nginx` | nginx | Simple Icons |
  | `si-homeassistant` | Home Assistant | Simple Icons |
  | `si-nextcloud` | Nextcloud | Simple Icons |
  | `si-bluetooth` | Bluetooth (z. B. BlueZ) | Simple Icons |

  Welcher Chip welches Symbol bekommt (z. B. VLAN, Firewall, Dockform): Regel `icons.mapping` in `assets/icons/README.md`. Die Ids stehen hier, die Begriffe dort. Nennt ein Profil oder ein Beleg ein Symbol, das in `assets/mappe/icons.svg` fehlt, bricht der Bau mit der Id ab. Jede gebaute Datei enthält nur die Symbole, die sie verwendet.

  Quellen: Devicon 2.17.0 (MIT) und Simple Icons 15.0.0 (CC0 1.0). Lucide 0.469.0 (ISC/Feather, MIT) für die Linien-Icons `i-cable`, `i-router`, `i-shield`, `i-waypoints`; Lizenz in `assets/icons/LICENSES.md`. Simple Icons nur, wo Devicon kein brauchbares einfarbiges Logo hat (nginx und Proxmox sind bei Devicon Schriftzüge, das Devicon-SSH-Logo zerfällt einfarbig). Für SSH/OpenSSH gibt es kein freies einfarbiges Logo: Linien-Icon `i-terminal`. Quelldatei je Symbol, Lizenztexte und Ablauf: `assets/icons/`.
- Ein Logo im Vorrat ist keine Aussage über den Bewerber. Welche Technik mit welcher Skala erscheint, steht nur im Profil. Neue Logos sind eine Designänderung an `assets/mappe/icons.svg`: Devicon zuerst, sonst Simple Icons, mit `tools/devicon_symbols.py` einfarbig umwandeln (Ablauf in `assets/icons/README.md`; das Werkzeug prüft XML, `viewBox`, Dateiname/Id, erlaubte Elemente und Attribute und weist Verweise, Skripte, `foreignObject`, `style`-Elemente und Strichfarben mit einer Fehlermeldung je Datei ab), diese Tabelle nachtragen.

### Bildschirm

Desktop zeigt Papierseiten mit Schatten, Bildschirmleiste und Seitennavigation; mobil fließt der Inhalt ohne feste Seitenhöhe und ohne Verdichtung. Beides ist nur Prüffläche und darf nicht horizontal überlaufen. `--qa` prüft die Fenstergrößen aus Regel `qa.viewports` in `references/qa-and-export.md`; weitere Breiten nur von Hand. Bildschirmleiste und Navigation sind im Druck ausgeblendet.

### Verboten

Glas hinter Fließtext oder Scans, Stockfotos oder generierte Bilder als Projekte oder Porträts, Prozentbalken, externe Fonts, Bilder oder Skripte, überladene Deckblätter, Linien ohne Funktion, falsche Seitenzahlen.

## Nachweise und Bilder

- Zeugnisse und Zertifikate sind echte, vom Nutzer bereitgestellte Dokumente. Keine Ersatzdokumente, keine dekorativen Platzhalter, die wie Scans aussehen.
- Eingang: PNG, JPEG, WebP direkt; PDF als PNG gerendert (Original daneben, separat beilegen, wenn die Anzeige es verlangt); DOCX nur als Quelle für Angaben und eingebettete Bilder.
- Vor dem Einbinden prüfen: lesbar, gehört zum Nutzer, Ausstellungsdatum erkennbar, Art (Zertifikat oder Zeugnis), darf erscheinen.
- Das Build-Skript kopiert die benötigten Bilder in `application/assets/` des Stellenordners und trägt sie mit Quelle im Manifest ein.
- Projektfotos (Rolle `project_image`, Abschnitt `motivationsschreiben`) stehen im Manifest; sie werden nur gebaut, wenn ein Beleg dazu passt (siehe Motivationsschreiben).
- Keine Nachweise in Git, keine Uploads in externe Dienste. Vor dem Versand prüft der Nutzer, ob Geburtsdatum, Adresse oder andere sensible Angaben sichtbar sein sollen.
