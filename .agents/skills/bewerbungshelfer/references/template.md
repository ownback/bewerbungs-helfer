# Vorlage, Seiten und Design

Die Basisvorlage ist `assets/bewerbungsmappe.html` (Stand Runde 5, „Glisse“). Sie ist datenfrei, enthält Platzhalter in eckigen Klammern, erklärende HTML-Kommentare, die SVG-Bibliothek und den QA-Snippet. Sie ist die einzige Stelle für Designänderungen; visuell geprüft und geändert wird sie über Tencil (`references/tencil.md`).

`tools/build_mappe.py` übernimmt `<head>` (CSS, eingebettete Schrift) und SVG-Bibliothek der Vorlage unverändert und erzeugt die Seiten nach dem Datenvertrag unten. Daraus entstehen die Profilvorlage `<name>_template.html` und pro Stelle die Mappe. Generiertes HTML wird nie von Hand bearbeitet.

**Strukturänderungen an der Vorlage** (neue oder umbenannte Klassen, andere Verschachtelung, neue Seitenelemente) brauchen eine passende Änderung in `tools/build_mappe.py`. Reine CSS- und Symboländerungen wirken sofort beim nächsten Bau. Die QA meldet Klassen, die das Skript erzeugt, die Vorlage aber nicht kennt.

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
- Deckblatt: petrolfarbener Farbraum nur im oberen Teil (`#0f4753` → `#0d4250` → `#0a2c35`, seit Runde 5 heller) mit weichen Lichtflecken; Text darauf weiß bzw. 74 % Weiß (≥ 6,5:1). Darunter weißes Papier.

Den Akzent nur ändern, wenn Text darauf und daneben mindestens 4,5:1 erreicht.

### Typografie

- Eine Familie: **Inter 4.1** (SIL OFL 1.1), Stapel `"Inter", "Helvetica Neue", "Segoe UI", "Noto Sans", Arial`. Inter ist in der Vorlage eingebettet (Block `<style id="font-inter">` am Ende des Kopfs, data-URIs), keine externen Font-Requests, keine Systeminstallation nötig.
- Statische Schnitte 400, 500, 600, 700 (keine variable Schrift): Chromium bettet sie im PDF als TrueType (CID) ein, Text bleibt auswählbar und auswertbar. Nur diese vier Gewichte verwenden. Untermenge Latin + Latin Extended (deutsche Umlaute, ß, ș ț ă, typografische Anführungszeichen, Gedankenstrich).
- Quelldateien und Lizenz: `assets/fonts/` (`Inter-*.woff2`, `OFL.txt`, `README.md` mit dem Weg zum Neu-Einbetten).
- SF Pro bewusst nicht im Stapel (Lizenz erlaubt keine Einbettung in eigene Dokumente); `-apple-system`/`BlinkMacSystemFont` ebenfalls nicht (Chromium unter Linux löst sie zu Liberation Sans auf).
- Hierarchie über Größe und Gewicht: Name ca. 54 pt, Abschnittstitel 25 pt, Betreff 16,5 pt, Einstieg 15,5 pt, Fließtext 9,6 pt, Nebentext 8,5 pt, Chips 7,5 pt, Bildunterschriften 7,4 pt. Überschriften ab 12 pt in 700, kleine Titel und Hervorhebungen in 600, Akzentzeilen in 500. Keine Serifen, keine Großbuchstaben-Labels. Fließtext nie unter 9 pt.

### Seiten

- A4 210 × 297 mm, `@page { size: A4; margin: 0 }`, Satzspiegel 20 mm seitlich, 24 mm oben, 20 mm unten.
- **Keine Fußzeile.** Die Seitenzahl steht im Registerreiter (`.folio`), schlicht `1`, `2`, … ohne führende Null und ohne Gesamtzahl. Der Name steht auf Deckblatt, im Briefkopf und im Lebenslauf.
- Registratur: sechs Spalten über die Seitenbreite; `data-section="1…6"` setzt den Reiter in die Spalte seines Abschnitts. Folgeseiten bekommen automatisch einen hellen Reiter.
- Keine vertikalen Dekorlinien, keine Timeline-Verbindungslinien, kein Firmenname auf dem Deckblatt.

### Deckblatt

Zwei Zonen (seit Runde 5, leichter im Druck):

- **Farbraum** `.cover-stage` oben (ca. drei Viertel der Seite, so hoch wie die Seite minus Papierzone): Kennung „Bewerbungsmappe“ oben links, Name unten links (Klasse nach dem längsten Namensteil: bis 10 Zeichen keine, 11–13 `is-long`, 14–17 `is-xlong`; bei Doppelnamen zählt der Teil mit Bindestrich), darunter der Beruf. Rechts unten die Glasleiste mit optionalem Foto (4:5), Kontakt und Inhaltsangabe; sie ist so hoch wie ihr Inhalt. Die Glasleiste ist leichter als in Runde 4 (weniger Füllung, feinere Kante, kürzerer Schatten).
- **Papierzone** `.cover-intro` unten (mindestens 76 mm): links das Kurzprofil in dunkler Schrift, rechts unter der Glasleiste der Beginn als Kapsel. Fließtext steht damit nie auf dunklem Grund.

Kontakt in der Leiste: Telefon, E-Mail, Anschrift (zweizeilig). Lange E-Mail-Adressen (über 24 Zeichen) bricht das Skript mit `<wbr>` nach „@“ und vor Punkten um, auch im Briefkopf und im Lebenslauf.

Foto nur mit `person.photo.valid` und `consent`; sonst entfällt der Block ersatzlos (kein Platzhalterrahmen). Ausschnitt über `--photo-x`, `--photo-y`, `--photo-zoom` (Profil `photo.focus`): Augen bei ca. 35–40 % der Rahmenhöhe, Zoom höchstens ca. 1,2, mindestens 600 × 750 px.

### Anschreiben

Geschäftsbrief nach DIN-5008-Zonen, angepasst für den E-Mail-Versand (keine Falzmarken, keine Rücksendezeile):

- Symmetrischer Briefkopf: links Empfänger, rechts Absender, je sechs Zeilen mit Icon auf einem gemeinsamen Raster: Firma (fett) · Anrede + Name · Straße · PLZ Ort · Telefon · E-Mail. Die Firmenzeile des Absenders bleibt leer. Die Anrede vor dem eigenen Namen kommt aus `person.salutation` (leer = nur Name); sie ist eine Entscheidung des Nutzers. Fehlt beim Empfänger eine belegte Angabe, bleibt eine leere Zeile (`is-empty`) stehen; nichts erfinden. Ohne Ansprechpartner steht die Abteilung in der Namenszeile.
- Straße ausgeschrieben („Straße“, nicht „Str.“), Straße und PLZ/Ort zweizeilig ohne Punkt und Komma, für Absender und Empfänger. Das Build-Skript warnt bei „Str.“ oder Satzzeichen am Ende.
- Ort (Wohnort) und Datum („11. November 2026“) rechtsbündig mit Kalender-Icon zwischen Briefkopf und Betreff.
- Betreff zweistufig in gemischter Schreibung (Entscheidung des Nutzers, Versalien wirken bei langen Berufsbezeichnungen laut): Einleitung klein in Akzentfarbe, darunter groß der Beruf, darunter optional die BA-Referenznummer. Die Variante `.letter-subject.is-caps` (Einleitung in Versalien) existiert in der Vorlage, das Build-Skript setzt sie aber nicht; sie wäre eine Skript- und Profiländerung.
- Brieftext bis ca. 250 Wörter normal, ca. 250–350 Wörter `.letter-copy.is-dense`, darüber kürzen.
- Unterschrift als Bild (12 mm hoch, höchstens 45 mm breit) nur mit gültiger, freigegebener Datei; darunter Name und Ort.

### Lebenslauf

- Reihenfolge der Blöcke: Praktische Erfahrung, Schulbildung, Fähigkeiten, Sprachen (Sprachen immer zuletzt, auch beim Umbrechen auf die Fortsetzung). Optionaler Block „Eigene Projekte“ irgendwo nach der Erfahrung, wo er auf die Seite passt.
- Kopf: Name, „Ausbildungsziel: …“, persönliche Daten zweispaltig (Anschrift, E-Mail, Telefon, Geburtsdatum mit `i-cake`, Geburtsort mit `i-map`, optional „Führerschein Klasse B“ mit `i-car` aus `person.driving_license`, immer nach den Geburtsdaten; mit allen Angaben sind es 3 + 3 Zeilen). Kein Kurzprofil im Lebenslauf (steht auf dem Deckblatt).
- Praktische Erfahrung: neueste zuerst; Datum links in eigener Spalte, rechts Organisation, Ort, Rolle · Art, Aufgaben. Näherungen mit „ca.“.
- Schulbildung: Einrichtung, Ort, „Schulform · Profil“, Detailzeile nur „Abschluss: …“ bzw. „Abschluss: …, voraussichtlich MM/JJJJ“. Keine Zeugnis- oder Klassendetails. Neueste zuerst. Grundschulen entfallen standardmäßig, sobald ein weiterführender Abschluss vorliegt (`education[].show_in_cv: false`, Nutzer bestätigt; der Eintrag bleibt im Profil, das Skript meldet die ausgeblendeten Einträge).
- Sprachen: Balken mit Niveauwort darunter, keine Belegzeile.
- Fähigkeiten: Gruppen untereinander, Gruppentitel mit Linien-Icon; jede Zeile = Kategorie (optional kleiner Zusatz), Technik-Chips, Skala. Bis ca. 6 Chips je Zeile passen bei üblichen Namen in eine Zeile; längere Reihen brechen ruhig in eine zweite Zeile um (kostet ca. 4–5 mm Höhe). Keine Prozentwerte.
- Skalen-Legende unter den Fähigkeiten: fünf gleich breite Spalten, oben die Musterleiste in Originalgröße, darunter die Bezeichnung (8,5 pt, gedämpft): Lernwunsch, Grundkenntnisse, sicher, routiniert, sehr sicher.
- Eigene Projekte / Homelab (optional, Block `projects`): nur Projekte mit `show_in_cv: true`, Reihenfolge wie im Profil. Zeile wie bei der Erfahrung: Zeitraum links (leer, wenn unbekannt; „laufend“ bei `is_current` ohne Datum), Projektname, ein Satz aus `cv_summary` (sonst `own_role`), darunter die Werkzeuge als Chips (`chips`, sonst Text-Chips aus `tools`). Titel und Icon aus `presentation.cv_projects` (Standard „Eigene Projekte“, `i-layers`). Platzbedarf: ca. 12 mm Kopf plus ca. 18–20 mm je Eintrag mit einer Zeile Text und einer Chipzeile; höchstens zwei bis drei Einträge.
- Aufteilung auf Seiten (`presentation.cv_layout`): Die QA meldet den Füllgrad jeder Lebenslauf-Seite („Füllgrad Lebenslauf: S3 95 % (+13.9 mm) · …“, Anteil des Satzspiegels, Rest in mm; negativ = Überlauf). Vorgehen:
  1. Standard ist eine Seite mit allen Blöcken. Läuft sie über, ganze Blöcke auf eine Fortsetzungsseite verschieben (Reihenfolge beibehalten, Sprachen zuletzt) und die Seiten etwa gleich füllen (Richtwert 90–98 %).
  2. Bei sehr vielen Stationen einen Block teilen.
  3. Verdichten (`cv_layout.compact`) nur auf einer Seite, die sonst überläuft: auf der volleren Seite (`[false, true]`) oder auf allen (`true`). Eine Seite, die ohne Verdichtung passt, bleibt unverdichtet.
  4. Zuletzt Beschreibungen im Profil kürzen.
  Ändert sich der Inhalt (Eintrag ein- oder ausgeblendet, Projekt, Fähigkeit), die Aufteilung neu prüfen. Ist der Richtwert nicht erreichbar (die zweite Seite bleibt deutlich leerer, weil ein Block nicht auf die erste passt), ist das in Ordnung; die freie Höhe dient dann dem nächsten Block (z. B. „Eigene Projekte“).

### Motivationsschreiben

Redaktioneller Einstieg (ein Satz, groß), daneben die Belege-Spalte mit drei Einträgen (Icon, Titel, Text). Kein Zitat-Icon, keine doppelte Projektgeschichte. Bis ca. 300 Wörter normal, bis ca. 370 Wörter `.motivation-copy.is-dense`. Abschluss mit Name und Ort, ohne Unterschriftsbild.

### Zertifikate und Zeugnisse

Titel und Aussteller über dem Scan, der Scan füllt die Resthöhe, darunter „Original-Scan“ (bzw. „Kopie“, „Digitales Original“) und „Ausgestellt am TT.MM.JJJJ“. Kein Badge, kein Zähler, keine Wiederholung von Schule oder Klasse.

- Ein Nachweis pro Seite im Regelfall. Reihenfolge wie im Profil.
- Zwei Nachweise nebeneinander (`.evidence-grid.is-pair`, Profil `pair: true`) nur für kurze, gut lesbare Dokumente (je ca. 80 mm breit), nie für textreiche Zeugnisse.
- Weitere Nachweise auf Folgeseiten.
- Fehlt ein Nachweis, steht „Liegt noch nicht vor“.

### Icons und Logos

- Linien-Icons (`<svg class="icon"><use href="#i-…"/></svg>`): `i-phone`, `i-mail`, `i-pin`, `i-calendar`, `i-user`, `i-folder`, `i-graduation`, `i-briefcase`, `i-terminal`, `i-server`, `i-network`, `i-scan`, `i-list`, `i-badge`, `i-globe`, `i-branch`, `i-layers`, `i-wrench`, `i-building`, `i-home`, `i-cake`, `i-map`, `i-monitor`, `i-code`, `i-cpu`. Ein Icon trägt nie allein eine Information.
- Technologie-Logos lokal als einfarbige `<symbol>` eingebettet (`<svg class="logo"><use href="#dv-…"/></svg>`), im Chip immer neben dem Namen. Verfügbar:

  | id | Technik | Quelle |
  |---|---|---|
  | `dv-windows11`, `dv-apple`, `dv-linux`, `dv-archlinux`, `dv-debian`, `dv-android` | Betriebssysteme (auch iOS über `dv-apple`) | Devicon |
  | `dv-docker`, `dv-podman`, `dv-kubernetes`, `dv-ansible` | Container, Automatisierung | Devicon |
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

  Quellen: Devicon 2.17.0 (MIT) und Simple Icons 15.0.0 (CC0 1.0). Simple Icons nur, wo Devicon kein brauchbares einfarbiges Logo hat (nginx und Proxmox sind bei Devicon Schriftzüge, das Devicon-SSH-Logo zerfällt einfarbig). Für SSH/OpenSSH gibt es kein freies einfarbiges Logo: Linien-Icon `i-terminal`. Quelldatei je Symbol, Lizenztexte und Ablauf: `assets/icons/`.
- Ein Logo im Vorrat ist keine Aussage über den Bewerber. Welche Technik mit welcher Skala erscheint, steht nur im Profil. Neue Logos sind eine Designänderung an der Vorlage: Devicon zuerst, sonst Simple Icons, mit `tools/devicon_symbols.py` einfarbig umwandeln (Ablauf in `assets/icons/README.md`; das Werkzeug prüft XML, `viewBox`, Dateiname/Id, erlaubte Elemente und Attribute und weist Verweise, Skripte, `foreignObject`, `style`-Elemente und Strichfarben mit einer Fehlermeldung je Datei ab), diese Tabelle nachtragen.

### Bildschirm

Desktop zeigt Papierseiten mit Schatten, Bildschirmleiste und Seitennavigation; mobil fließt der Inhalt ohne feste Seitenhöhe und ohne Verdichtung. Beides ist nur Prüffläche: Desktop 1440 × 900 oder 1280 × 800, mobil 390 × 844 und 375 × 812 ohne horizontalen Überlauf. `--qa` prüft genau 1440 × 900, 390 × 844 und 375 × 812 und nennt alle drei Werte (`references/qa-and-export.md`); weitere Breiten (z. B. 1280) nur von Hand. Bildschirmleiste und Navigation sind im Druck ausgeblendet.

### Verboten

Glas hinter Fließtext oder Scans, Stockfotos oder generierte Bilder als Projekte oder Porträts, Prozentbalken, externe Fonts, Bilder oder Skripte, überladene Deckblätter, Linien ohne Funktion, falsche Seitenzahlen.

## Datenvertrag (Klassen)

Das Build-Skript erzeugt diese Struktur; Designänderungen müssen sie erhalten oder das Skript mitziehen.

- Seiten: `.page`, `.cover-page`, `.letter-page`, `.cv-compact`, `data-section`, `data-slot="letter|motivation"` (Austauschbereiche der Profilvorlage, ohne Wirkung auf das Aussehen), `.section-head`, `.continued`, `.folio`, `.page[data-overflow]`
- Bildschirm: `.screen-bar`, `.screen-nav`, `.viewport-proof`, `.glass`, `.glass-dark`, `.glass-light`
- Deckblatt: `.cover-layout` > `.cover-stage` (> `.cover-main`, `.cover-panel`) + `.cover-intro` (> `.cover-bio`, `.cover-start`); `.cover-mark`, `.cover-hero` (`h1.is-long`, `h1.is-xlong`, `.cover-role`), `.cover-panel`, `.cover-photo`, `.contact-list`, `.contact-item`, `.panel-spacer`, `.toc-list`, `.toc-row`, `.toc-page`, `.label`
- Anschreiben: `.letter-head`, `.letter-party`, `.letter-line` (`.is-org`, `.is-name`, `.is-empty`), `.letter-date`, `.letter-subject` (`.is-caps`), `.subject-kicker`, `.subject-title`, `.subject-ref`, `.letter-copy` (`.is-dense`), `.signature`, `.signature-img`, `.signature-name`
- Lebenslauf: `.cv-hero`, `.cv-name`, `.cv-goal`, `.cv-facts`, `.cv-section`, `.cv-section-head`, `.timeline-item`, `.timeline-date`, `.timeline-content`, `.timeline-place`, `.timeline-role`, `.timeline-text`, `.timeline-chips` (Chipzeile in Projekten, zusammen mit `.skill-chips`), `.language-list`, `.language`, `.language-name`, `.language-level`, `.skills-band`, `.skill-group`, `.skill-head`, `.skill-row`, `.skill-name`, `.skill-chips`, `.tech`, `.logo`, `.bars.s1…s5`, `.bars.is-future`, `.skill-legend`, `.scale-item`
- Motivationsschreiben: `.motivation-lead`, `.motivation-layout`, `.motivation-copy` (`.is-dense`), `.motivation-aside`, `.proof-item`
- Nachweise: `.evidence-grid` (`.is-pair`), `.evidence-card`, `.evidence-meta`, `.document-stage`, `.document-placeholder`, `.document-caption`, `.caption-note`, `.caption-date`
- Lebenslauf-Blöcke in `cv_layout.pages`: `experience`, `education`, `projects`, `skills`, `languages`; Überschriften-IDs `experience-title`, `education-title`, `projects-title`, `skills-title`, `languages-title`.
- Veraltet, ohne Wirkung: `.skills-band.is-four`. Entfallen seit Runde 4: `.page-footer`, `.letter-window`, `.letter-info`, `.return-line`, `.cv-role`. Seit Runde 5 sitzen `.cover-bio` und `.cover-start` in `.cover-intro` statt in `.cover-main`.

## Nachweise und Bilder

- Zeugnisse und Zertifikate sind echte, vom Nutzer bereitgestellte Dokumente. Keine Ersatzdokumente, keine dekorativen Platzhalter, die wie Scans aussehen.
- Eingang: PNG, JPEG, WebP direkt; PDF als PNG gerendert (Original daneben, separat beilegen, wenn die Anzeige es verlangt); DOCX nur als Quelle für Angaben und eingebettete Bilder.
- Vor dem Einbinden prüfen: lesbar, gehört zum Nutzer, Ausstellungsdatum erkennbar, Art (Zertifikat oder Zeugnis), darf erscheinen.
- Das Build-Skript kopiert die benötigten Bilder in `application/assets/` des Stellenordners und trägt sie mit Quelle im Manifest ein.
- Keine Nachweise in Git, keine Uploads in externe Dienste. Vor dem Versand prüft der Nutzer, ob Geburtsdatum, Adresse oder andere sensible Angaben sichtbar sein sollen.
