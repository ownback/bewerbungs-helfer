# Änderungsliste für den zweiten Workflow-Durchlauf

Stand: 11.11.2026

Diese Liste ist die Arbeitsgrundlage für die nächste Iteration. Sie beschreibt zuerst den Workflow und die Datenverträge. Die HTML-Bearbeitung folgt erst danach aus diesen Regeln. Punkte, die persönliche Daten enthalten, gehören ausschließlich in das lokale Profil oder den lokalen Bewerbungsordner.

## Leitentscheidung

Der nächste Durchlauf beginnt nicht mit einer neuen HTML-Fassung. Zuerst werden Profilerfassung, Datenverträge, Skill-Anweisungen, Basisvorlage und Prüfregeln korrigiert. Erst danach wird der Workflow mit demselben Profil und derselben Stelle erneut ausgeführt.

Das Anschreiben beantwortet: **Warum ist dieser Bewerber für diese Ausbildung geeignet und warum wird er sie wahrscheinlich erfolgreich abschließen?**

Das Motivationsschreiben beantwortet: **Warum will dieser Bewerber diesen Weg gehen, und warum beschäftigt ihn das Thema?**

Beide Texte dürfen dieselbe Tatsache nur verwenden, wenn sie damit eine andere Frage beantworten. Projektgeschichten und Formulierungen werden nicht doppelt erzählt.

## A. Profilinterview und Profilmodell

### A1. Profil als strukturierter Datenvertrag

**Problem:** Das aktuelle Markdown-Profil ist zu frei. Angaben wie Praktikumsart, genaue Aufgaben, Monate, Icon-Auswahl, Bildfreigabe und Quellen gehen verloren oder werden später falsch rekonstruiert.

**Änderung:**

- Eine strukturierte lokale Profildatei `profile/master-profile.json` als primäre Profilquelle einführen.
- Die bestehende Markdown-Datei bleibt als menschenlesbare Zusammenfassung, wird aber aus dem JSON erzeugt oder damit abgeglichen.
- Das JSON enthält eigene Objekte für Person, Ziel, Schulbildung, Werdegang, Projekte, Fähigkeiten, Nachweise, Motivation, Stimme und offene Punkte.
- Jede Angabe erhält einen Status: `confirmed`, `inferred`, `open` oder `conflict`.
- Jede Station enthält `kind` mit mindestens `internship`, `employment`, `education` oder `project`.
- Zeiträume werden als Start- und Endmonat gespeichert. Eine reine Jahresangabe bleibt als Jahresangabe erhalten und wird nicht stillschweigend zu einem Monat.
- Wenn der Nutzer eine plausible Näherung ausdrücklich freigibt, wird sie als `inferred` gespeichert und im Profil sichtbar markiert. Sie darf nicht als verifizierte Tatsache erscheinen.

**Betroffene Dateien:**

- `.agents/skills/bewerbungshelfer/references/profile-schema.md`
- `.agents/skills/bewerbungshelfer/assets/schemas/profile.schema.json`
- `.agents/skills/bewerbungshelfer/assets/templates/master-profile.json`
- `.agents/skills/bewerbungshelfer/assets/templates/master-profile.md`
- `docs/questionnaire.md`
- `docs/workflow.md`
- `docs/schemas.md`

**Abnahme:** Ein Profil kann gespeichert und gegen das Schema geprüft werden, ohne dass Praktikum, Anstellung, Schulzeit oder offene Angabe verwechselt werden.

### A2. Vorhandene Unterlagen zuerst vollständig auswerten

**Problem:** Die vorhandene PDF enthält relevante Stationen, die im Profil fehlten. Das PDF wurde zunächst nur als Text gelesen; entscheidende Angaben standen in einer Grafik.

**Änderung:**

- PDFs, DOCX und Bilder beim Import immer visuell prüfen, nicht nur per Textextraktion.
- DOCX auf eingebettete Bilder prüfen.
- Alle Seiten und Grafiken erfassen, bevor das Interview beginnt.
- Erkannte Angaben nach `confirmed`, `inferred`, `open` und `conflict` sortieren.
- Bei widersprüchlichen Angaben den Nutzer genau einmal fragen und die Entscheidung mit Quelle speichern.
- Nicht lesbare oder defekte Dateien ausdrücklich als offen melden.
- Bei einem vorhandenen Lebenslauf einen Abgleich gegen das Profil verlangen: fehlende Stationen, unklare Art der Beschäftigung, fehlende Monate und zusätzliche Aufgaben.

**Abnahme:** Jede Station aus dem gelieferten Lebenslauf ist entweder im Profil vorhanden oder als bewusst ausgelassen belegt.

### A3. Bewerbungsfoto

**Problem:** Das vorhandene Foto war eine leere Datei. Eine leere oder fremde Datei darf niemals als Foto in die Mappe gelangen.

**Änderung:**

- Datei vor Einbindung technisch validieren.
- Prüfen, dass das Foto zum Nutzer gehört und ausdrücklich freigegeben ist.
- Bei ungültiger Datei das Foto nicht einbinden und einen offenen Punkt anlegen.
- Die Fotofläche im Deckblatt nur rendern, wenn ein valides, freigegebenes Bild vorliegt.
- Ein Platzhalter darf nicht wie ein echtes Bewerbungsfoto aussehen.
- Zuschnitt, Blickrichtung und Bildqualität visuell prüfen.

**Abnahme:** Kein defektes oder fremdes Bild kann ohne Warnung in HTML oder PDF gelangen.

### A4. Fähigkeiten als belegtes Niveau

**Problem:** Freie Listen und Prozentbalken erzeugen Scheingenauigkeit und lassen wichtige Kenntnisse weg.

**Änderung:**

- Kenntnisse in die Gruppen Systeme, Infrastruktur, Entwicklung, Tools und Sprachen gliedern.
- Niveaus nur mit vereinbarten Labels speichern, zum Beispiel `sicher`, `Grundkenntnisse`, `Lernstand`, `Lernwunsch`, `Muttersprache`.
- Keine Prozentangaben und keine erfundenen Selbsteinschätzungen.
- Ein Diagramm darf nur die gespeicherten Labels visualisieren, nicht eine feinere Genauigkeit vortäuschen.
- Jedes Niveau braucht einen Profilbeleg oder eine ausdrückliche Selbsteinschätzung.
- Betriebssysteme, Programmiersprachen, Netzwerkwerkzeuge, Git und Hardwarekenntnisse getrennt erfassen.

**Abnahme:** Jede dargestellte Fähigkeit lässt sich im Profil nachvollziehen, und die Darstellung behauptet nicht mehr als das gespeicherte Niveau.

### A5. Icon-Auswahl als Profilpräferenz

**Problem:** Icons wurden mehrfach passend zur Bedeutung, aber nicht passend zur gewünschten visuellen Sprache gewählt.

**Änderung:**

- Für wiederkehrende Kategorien feste Icon-IDs definieren.
- Der Nutzer kann pro Kategorie eine Icon-Präferenz im Profil speichern.
- Die Auswahl wird im Datenvertrag dokumentiert, nicht nur im HTML hartcodiert.
- Symbole werden optisch zentriert und auf einer gemeinsamen Strichstärke ausgegeben.
- Ein Icon darf nie die einzige Information tragen.

**Abnahme:** Eine erneute Ausgabe verwendet dieselben freigegebenen Icons und zentriert sie korrekt.

## B. Stellenanzeige und `job.json`

### B1. Kontaktblock vollständig modellieren

**Änderung:**

- Kontaktfelder getrennt erfassen: Ansprechpartner, Funktion, Abteilung, Unternehmen, Straße, PLZ, Ort, Telefon, E-Mail und Quelle.
- Persönliche und allgemeine Kontaktdaten getrennt halten.
- Fehlende Angaben als leer und `unknown` markieren.
- Keine Telefonnummer oder E-Mail aus einem ähnlichen Unternehmen übernehmen.

**Abnahme:** Der Briefkopf kann ausschließlich aus belegten `job.json`-Feldern erzeugt werden.

### B2. Unternehmensbezug belegen

**Änderung:**

- Unternehmensbezug im Anschreiben und Motivationsschreiben auf Stellenanzeige oder öffentliche Unternehmensseite stützen.
- Jede unternehmensspezifische Aussage mit Quell-URL im Arbeitsstand belegen.
- Keine Kultur- oder Kundenversprechen aus dem Bauch formulieren.
- Zwischen Anforderung, Unternehmensfakt und eigener Interpretation unterscheiden.

**Abnahme:** Jeder Satz über das Unternehmen ist prüfbar.

### B3. Pflichtfelder und offene Punkte trennen

**Änderung:**

- Pflichtfelder für die Mappe klar definieren.
- Optionale Angaben nicht als fehlend behandeln.
- Offene Punkte mit Auswirkung speichern: `blocking`, `non_blocking`, `research_needed`.
- Der Workflow stoppt nur bei blockierenden Lücken.

**Abnahme:** Eine fehlende persönliche Ansprechperson blockiert nicht, eine unklare Schulbildung oder ein fehlendes Pflichtfoto schon.

## C. Skill und Schreibworkflow

### C1. Reihenfolge des Workflows

**Neue Reihenfolge:**

0. Einmalig: datenfreie Basisvorlage gestalten und freigeben (entfällt, wenn bereits freigegeben).
1. Bestehende Unterlagen visuell und strukturell auswerten.
2. Profilinterview nur für Lücken und Widersprüche.
3. Profil strukturiert speichern und bestätigen.
4. Bewerbungsmappe aus Basisvorlage und bestätigtem Profil vorbereiten.
5. Genau eine Stelle bei der Bundesagentur auswählen und belegen.
6. Passung und Unternehmensbezug prüfen.
7. Anschreiben und Motivationsschreiben getrennt entwerfen.
8. Wiederholungen und unbelegte Aussagen prüfen.
9. HTML bauen und auf Desktop, Mobil und A4 prüfen.
10. HTML freigeben.
11. PDF, Kontaktübersicht und E-Mail-Entwurf erstellen.

**Abnahme:** Kein Schritt beginnt, bevor die benötigten Angaben aus dem vorherigen Schritt bestätigt sind.

### C2. Anschreiben und Motivationsschreiben trennen

**Anschreiben:**

- Eignung und Passung zur konkreten Ausbildung.
- Belegte Stärken mit kurzen Beispielen.
- Warum der Bewerber die Ausbildung voraussichtlich erfolgreich abschließen kann.
- Warum dieses Unternehmen und diese Stelle.
- Ehrliche Lücke nur, wenn sie für die Entscheidung relevant ist.
- Keine vollständige Biografie und keine lange Projektnacherzählung.

**Motivationsschreiben:**

- Persönlicher Antrieb und Ausgangspunkt des Interesses.
- Warum der Beruf gewählt wird.
- Eine oder zwei prägende Erfahrungen mit eigener Rolle und Ergebnis.
- Warum das Thema auch außerhalb der Pflicht beschäftigt.
- Warum dieser Weg bei diesem Unternehmen weiterführt.
- Keine Wiederholung der Eignungsargumente aus dem Anschreiben.

**Gemeinsame Regel:** Vor der Freigabe wird eine Wiederholungsprüfung durchgeführt: gleiche Anekdote, gleiches Projekt, gleiche Stärke und gleiche Formulierung dürfen nicht in beiden Briefen als Hauptargument erscheinen.

**Abnahme:** Beide Texte beantworten nachweisbar unterschiedliche Fragen.

### C3. Schreibstil

**Änderung:**

- Kurze und lange Sätze bewusst mischen.
- Konkrete Beispiele statt Werbeadjektive.
- Keine Floskeln, keine erfundenen Superlative, keine künstlichen Gegensatzpaare.
- Keine Story in beiden Briefen wiederholen.
- Deutsche Rechtschreibung und korrekte Anrede.
- Vor der Freigabe laut lesen und AI-typische Muster entfernen.

**Abnahme:** Der Text klingt wie ein sorgfältiger Bewerber und nicht wie eine allgemeine Motivationsvorlage.

### C4. Freigabepunkte

**Änderung:**

- Nach Profil und Stelle: kompakte Faktenübersicht zur Bestätigung.
- Nach den Briefen: getrennte Freigabe von Inhalt und Ton.
- Nach HTML: ausdrückliche Freigabe von Inhalt und Optik.
- Nach PDF: Sichtprüfung aller Seiten.
- Keine automatische Freigabe durch bloßes Schweigen.

**Abnahme:** Jeder Außenwirkungsschritt hat einen dokumentierten Freigabestatus.

## D. Basisvorlage und Designsystem

### D1. Basisvorlage synchronisieren

**Problem:** Die Basisvorlage und die ausgearbeitete Bewerbung unterscheiden sich grundlegend. Ein neuer Durchlauf würde die alte, nicht freigegebene Fassung reproduzieren.

**Änderung:**

- Die aktuelle, freigegebene Unternehmensmappe als Grundlage der neuen Basisvorlage verwenden.
- Unternehmensspezifische Texte und Daten entfernen.
- Alle sechs Seiten und das gemeinsame Komponentensystem erhalten.
- CSS-Tokens, Icons, Abstände, Typografie und PDF-Regeln zentral halten.
- Keine unternehmensspezifischen Inhalte in die Basisvorlage übernehmen.

**Abnahme:** Ein neuer Lauf erzeugt dieselbe Designsprache, ohne die vorherige Bewerbung zu kopieren.

### D2. Deckblatt

**Änderung:**

- Waagerechte Linie zwischen „Bewerbungsmappe“ und Jahr entfernen.
- „Dossier · 01“ und den Punkt entfernen.
- Seitenzahlen im Inhaltsverzeichnis als `1` bis `6` darstellen, nicht `01` bis `06`.
- Keine Gesamtseitenzahl `/06` auf Inhaltsseiten.
- Rechte Sidebar klar als Sidebar abtrennen und mehr Ruhe in der Mitte lassen.
- Ein echtes, freigegebenes Bewerbungsfoto in der dafür vorgesehenen Fläche zeigen.
- Kein Bildplatzhalter, wenn kein valides Foto vorliegt.
- Kurzprofil natürlich formulieren: Alter, aktueller Bildungsweg, Interesse an IT und Ziel.
- Keine generische Ich-bin-motiviert-Formulierung.
- Ziel „Ausbildung <Abschlussjahr>“ horizontal und ohne unnötigen Icon-Stapel gestalten.
- Keinen Unternehmensnamen auf das Deckblatt setzen.
- Inhaltsverzeichnis beibehalten.

**Abnahme:** Das Deckblatt funktioniert mit und ohne Foto, ohne leer oder unfertig zu wirken.

### D3. Gemeinsame Seitenelemente

**Änderung:**

- Vertikale Goldlinie am rechten Rand aller Seiten entfernen.
- Seitenzahl nur als einfache Zahl anzeigen.
- Kopfbereich pro Seitentyp konsistent halten.
- Icons optisch zentrieren und in einer gemeinsamen Größe ausgeben.
- Fußzeilen enthalten nur den Namen, keine vollständige Kontaktzeile.
- Keine dekorativen Elemente ohne Funktion.

**Abnahme:** Keine Seite zeigt überflüssige Linien, falsche Seitenzahlen oder verschobene Icons.

### D4. Anschreiben-Layout

**Änderung:**

- Name des Bewerbers eine Typstufe kleiner.
- Empfängerunternehmen fett.
- Empfänger links, Absender rechts.
- Beide Blöcke symmetrisch aufbauen.
- Empfängerblock: Unternehmen, Ansprechpartner oder Abteilung, Straße, PLZ/Ort, Telefon und E-Mail, sofern belegt.
- Absenderblock: Name, Straße, PLZ/Ort, Telefon und E-Mail.
- Datum mit Kalendericon beibehalten.
- Betreff zweistufig: kleine Zeile „Bewerbung um einen Ausbildungsplatz zum“, darunter deutlich größer „Fachinformatiker für Systemintegration“.
- Bewusst Weißraum als Gestaltungsmittel einsetzen.
- Fußzeile enthält nur den Namen.

**Abnahme:** Der Briefkopf wirkt wie ein formeller Brief und nicht wie zwei Karten.

### D5. Lebenslauf-Layout

**Änderung:**

- Keine vertikalen Verbindungslinien zwischen Timeline-Icons.
- Schulorte unter dem Schulnamen führen, nicht in der Beschreibung verstecken.
- Grundschulen als eigene Einträge darstellen.
- Berufsfachschule mit offiziellem Bildungsgang und voraussichtlichem Abschlussjahr gemäß Profil beschreiben.
- Klassenbezeichnungen nicht als Bildungsgang ausgeben.
- Unter dem Namen kein bereits erreichtes Berufsbild behaupten. Stattdessen „Ausbildungsziel: Fachinformatiker für Systemintegration“.
- Geburtsort in der im Profil bestätigten Schreibweise darstellen.
- Praktika und Anstellungen klar unterscheiden.
- Zusätzliche Praktika aus dem Original-Lebenslauf aufnehmen.
- Typische Aufgaben nur verwenden, wenn der Nutzer sie freigegeben hat.
- Eine frühere Fertigungsstation um bestätigte Produkt- und Tätigkeitsdetails ergänzen und mit passendem Fertigungsicon darstellen.
- Eine frühere Handels-/Logistikstation mit passendem Icon darstellen.
- Fähigkeiten als kompakte, lesbare Diagramme darstellen. Die vorhandene visuelle Skala darf weiterentwickelt werden, muss aber an gespeicherte Niveaus gebunden bleiben.
- Keine Prozentbalken und keine Scheingenauigkeit.

**Abnahme:** Alle Stationen sind vollständig, zeitlich plausibel und als Praktikum oder Anstellung erkennbar.

### D6. Motivationsschreiben-Layout

**Änderung:**

- Wiederholtes Zitat-Icon unter der großen Lead-Zeile entfernen.
- Lead auf den einen Satz kürzen: „Mein Interesse an IT begann mit einem Rechner, den ich selbst zusammengebaut habe.“
- Belege-Sidebar beibehalten.
- Icons in der Belege-Sidebar optisch zentrieren.
- Erste drei Absätze als unternehmensunabhängige Geschichte beibehalten.
- Vierter Absatz unternehmensspezifisch formulieren.
- Fünften Absatz ruhig und allgemein halten.
- Keine Projektgeschichte doppeln, die bereits im Anschreiben steht.

**Abnahme:** Die Seite erklärt Antrieb und persönlichen Weg; sie wiederholt nicht das Anschreiben.

### D7. Zertifikate und Zeugnisse

**Änderung:**

- Keine Wiederholung von Schule, Klasse und Schuljahr unter dem Titel.
- Kein „Zertifikat“- oder „Zeugnis“-Badge, solange dieselbe Badge-Logik nicht konsequent auf allen Seiten verwendet wird.
- Zertifikate und Zeugnisse verwenden dasselbe Nachweis-Icon.
- Unten links nur „Original-Scan“.
- Unten rechts statt `01 / 01` das Ausstellungsdatum.
- Keine Wiederholung des voraussichtlichen Abschlussjahres auf der Zeugnisseite.
- Scan-Symbol auch bei Zeugnissen verwenden.
- Nachweise lesbar und vollständig zeigen.

**Abnahme:** Jede Nachweisseite enthält nur die nötigen Metadaten und das echte Dokument.

## E. QA und Export

### E1. Pflichtprüfungen vor HTML-Freigabe

- [ ] Profil gegen Schema geprüft
- [ ] alle offenen blockierenden Punkte geklärt
- [ ] alle Stationen als Praktikum, Anstellung, Schulbildung oder Projekt klassifiziert
- [ ] alle Jahres- und Monatsangaben auf Plausibilität geprüft
- [ ] Foto technisch gültig und freigegeben
- [ ] Icons vorhanden, zentriert und semantisch passend
- [ ] keine unbelegten Unternehmensaussagen
- [ ] Anschreiben und Motivationsschreiben wiederholen keine Hauptargumente
- [ ] Seitenzahlen ohne führende Nullen und ohne Gesamtseitenzahl
- [ ] keine vertikale Dekorlinie
- [ ] Desktop bei 1440 × 900 geprüft
- [ ] Mobil bei 390 × 844 und 375 × 812 geprüft
- [ ] A4 separat geprüft
- [ ] keine externen Ressourcen
- [ ] echte Nachweise sichtbar oder ausdrücklich als fehlend markiert

### E2. PDF und Versand

- [ ] PDF erst nach ausdrücklicher HTML-Freigabe
- [ ] sechs A4-Seiten
- [ ] keine leeren oder abgeschnittenen Seiten
- [ ] Kontaktübersicht
- [ ] E-Mail-Entwurf
- [ ] nichts gesendet
- [ ] kein Portal ausgefüllt

## F. Bereits entschieden

- Deutsch als Sprache für Nutzerkommunikation und Dokumente.
- Nur Ausbildung.
- Nur Bundesagentur für Arbeit als Jobquelle.
- Eine Stelle pro Durchlauf.
- Skill statt Skripte.
- Sechs Seiten in der Reihenfolge Deckblatt, Anschreiben, Lebenslauf, Motivationsschreiben, Zertifikate, Zeugnisse.
- HTML zuerst, PDF erst nach Freigabe.
- Kein automatisches Absenden und kein automatisches Portalausfüllen.
- Keine erfundenen Qualifikationen, Kontakte oder Nachweise.
- Keine Demo-Daten im Repository.
- Profil- und Bewerbungsdaten bleiben lokal und gitignoriert.
- Claude-spezifische Dateien sollen nicht erforderlich sein.
- Stencil ist optionales visuelles Bearbeitungswerkzeug.

## G. Entscheidungen aus der Klärungsrunde

### G1. Praktikumsaufgaben

Typische Aufgaben dürfen ohne zusätzliche Kennzeichnung erscheinen, nachdem der Nutzer sie freigegeben hat. Die Freigabe wird im Profil als `confirmed` gespeichert. Eine angezeigte `inferred`-Markierung in der finalen Mappe ist nicht nötig.

### G2. Diagramme

Der Nutzer wünscht ausdrücklich mehr Diagramme. Die 5-Balken-Logik darf als kompakte visuelle Skala weiterentwickelt werden, solange die Balken an gespeicherte Niveaus gebunden sind und keine Prozentgenauigkeit vortäuschen. Diagrammtyp, Farbe, Abstände und Beschriftung werden nach den Design-Skills und dem Glisse-System entschieden.

### G3. Fußzeilen

In den Fußzeilen steht nur der Name. Vollständige Kontaktdaten bleiben im Briefkopf und im Lebenslauf.

### G4. Deckblatt-Sidebar

Die Sidebar wird durch eine ruhige, leicht abgesetzte Fläche und mehr Abstand getrennt. Keine zusätzliche harte Trennlinie.

### G5. Unternehmensname auf dem Deckblatt

Das Deckblatt bleibt unternehmensunabhängig und enthält keinen Unternehmensnamen. Unternehmensbezug erscheint nur in Anschreiben und Motivationsschreiben.

## H. Definition of Done für die nächste Iteration

Die Iteration ist abgeschlossen, wenn:

1. die Änderungen an Profil, Schemas, Fragen, Skill und Dokumentation umgesetzt sind,
2. die Basisvorlage aus der freigegebenen Designsprache neu aufgebaut ist,
3. das lokale Profil vollständig und gegen das Schema gültig ist,
4. dieselbe Ausbildungsstelle erneut durch den Workflow läuft,
5. Anschreiben und Motivationsschreiben klar getrennte Aufgaben erfüllen,
6. die HTML-Fassung auf Desktop, Mobil und A4 geprüft ist,
7. der Nutzer Inhalt und Optik ausdrücklich freigibt,
8. erst danach PDF, Kontaktübersicht und E-Mail-Entwurf entstehen.

Bis dahin wird kein PDF erzeugt und nichts versendet.
