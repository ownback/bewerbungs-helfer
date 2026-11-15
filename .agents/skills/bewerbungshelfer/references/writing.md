# Schreiben: Anschreiben, Motivationsschreiben, E-Mail, Kontaktdaten

<!-- rule: letters.evidence -->
Alle Texte entstehen pro Stelle neu, auf Deutsch, nur aus Profil (`<name>_profile.json`) und Anzeige (`job.json`, `ba_scrape.md`). Jede Aussage über den Bewerber braucht einen Profilbeleg, jede Aussage über die Firma einen Eintrag in `company_facts`. Unbelegte Sätze werden gestrichen, nicht geglättet.

## Aufgabenteilung

<!-- rule: letters.separation -->

| Text | Leitfrage | Ton |
|---|---|---|
| Anschreiben | Warum sollte die Firma mich nehmen? | sachlich, konkret |
| Motivationsschreiben | Warum begeistert mich dieses Fach? | persönlich, erzählend |
| E-Mail | Was liegt bei, an wen, warum diese Stelle? | kurz, höflich |

**Anschreiben = Fähigkeiten, nicht Leidenschaft.** Es zeigt, was der Bewerber versteht und wie er denkt: „Ich verstehe x, y und z“, „Ich kann in a, b und c denken“, belegt mit einem kurzen Beispiel. Begeisterung ist dort kein Argument.

**Motivationsschreiben = Leidenschaft für das Fach.** Woher das Interesse kommt, was es verstärkt hat, welches Problem den Bewerber nicht losgelassen hat, wohin er will.

**Keine Geschichte zweimal.** Ein Projekt, eine Anekdote oder eine Stärke ist in genau einem der beiden Texte Hauptargument. Im anderen darf sie höchstens als Halbsatz vorkommen, wenn sie dort eine andere Frage beantwortet.

## Anschreiben

Struktur:

1. belegte Anrede aus `contact.salutation`, mit Komma
2. Einstieg mit belegtem Bezug zu Stelle und Firma (aus `company_facts`)
3. zwei oder drei Fähigkeiten mit kurzem Beispiel: was der Bewerber versteht und kann
4. Arbeitserfahrung, die Verlässlichkeit zeigt (falls vorhanden)
5. Bildungsstand und Start
6. ehrliche Lücke oder Lernziel, wenn relevant
7. klarer Schluss (Bitte um Gespräch), dann „Mit freundlichen Grüßen“

<!-- rule: letter.length -->
Umfang: ca. 230 Wörter (`limits:letter.words.normal`); der Brieftext steht dann in 10 pt. Mit `dichte: dicht` (9 pt, engerer Satz) bis ca. 350 Wörter (`limits:letter.words.dicht`), darüber kürzen. Erst kürzen, dann verdichten: `dicht` ist die Ausnahme für Briefe, die sich nicht kürzen lassen. Das sind Richtwerte, die der Bau meldet; maßgeblich ist die Überlaufprüfung.

## Motivationsschreiben

Struktur:

1. **Einstieg:** ein persönlicher Satz, woher das Interesse kommt (erscheint groß über dem Text)
2. Ausgangspunkt und Weg
3. prägende Erfahrung oder ein Problem mit eigener Rolle und Ergebnis
4. warum das Thema auch außerhalb der Pflicht beschäftigt
5. belegter Bezug zu Stelle und Firma
6. Ausblick, ruhiger Schluss, „Mit freundlichen Grüßen“
7. **Belege:** drei kurze Einträge für die Seitenspalte (Projekt, eigene Rolle oder Ergebnis, Lernstand); Format unter Dateiformate.

<!-- rule: motivation.length -->
Umfang: bis ca. 300 Wörter (`limits:motivation.words.normal`), mit `dichte: dicht` bis ca. 370 Wörter (`limits:motivation.words.dicht`).

## Stimme

<!-- rule: letters.voice -->
- Kurze und lange Sätze mischen. Konkrete Beispiele statt Adjektive.
- Nicht verwenden: „hiermit bewerbe ich mich“, „mit großem Interesse“, „ich bin sehr motiviert“, „Teamplayer“, unbelegte Superlative, erfundene Anekdoten, künstliche Gegensatzpaare („nicht X, sondern Y“), Dreierketten als Stilmittel, Floskeln wie „Darüber hinaus“ am Satzanfang.
- `voice.avoid` und `motivation.boundaries` aus dem Profil beachten (persönliche Verbote, vom Nutzer im Interview genannt).
- Alter nur als exakte Zahl und nur, wenn der Nutzer es wünscht; keine Näherungen wie „bald 21“. Praktika nie als Anstellung darstellen, Zeiträume mit „ca.“ nur, wo das Profil `approx` führt.
- Name und Kontaktdaten exakt wie im Profil, Firmenname exakt wie in der Anzeige.

## Humanizer

<!-- rule: letters.humanizer -->
Nach dem Entwurf den Skill `humanizer` (blader/humanizer, Version 3.1.0, MIT; installiert unter `~/.agents/skills/humanizer/`) im Standardmodus „humanize“ auf `anschreiben.md`, `motivationsschreiben.md` und `email.md` anwenden, nicht auf `kontaktdaten.md`. Nicht das gleichnamige Claude-Code-Plugin `humanizer:humanizer` verwenden: Der Nutzer hat am 2026-11-15 beide an demselben deutschen Probetext verglichen und diese Fassung gewählt (schlichter, fügt keine Schlussfolgerungen hinzu). Fehlt der Skill, ihn aus `github:blader/humanizer` in dieser Version nach `~/.agents/skills/humanizer/` installieren oder den Nutzer fragen. Im Bericht der Stelle Name und Version des verwendeten Humanizers nennen. Der Skill darf Formulierungen ändern, aber keine Fakten hinzufügen; danach erneut gegen Profil und Anzeige prüfen.

Ist der Skill im Harness nicht verfügbar, das dem Nutzer sagen und seine Grundsätze selbst anwenden: keine aufgeblähte Bedeutung, keine Werbesprache, keine vagen Zuschreibungen, keine Dreierketten und Gegensatzpaare, keine Gedankenstrich-Häufung, keine Synonymwechsel um ihrer selbst willen, keine generischen Schlusssätze, keine Füllwörter. Lieber ein schlichter, genauer Satz.

## Dateiformate

Die Dateien liegen in `text_generation/` bzw. `application/` und werden vom Build-Skript gelesen. Vorlagen: `assets/templates/`.

### `anschreiben.md`

```markdown
---
datum: 2026-11-11
ort: Musterstadt
betreff_einleitung: Bewerbung um einen Ausbildungsplatz zum
betreff: Fachinformatiker für Systemintegration
dichte: normal
---

Sehr geehrte Frau Muster,

Erster Absatz …

Mit freundlichen Grüßen
```

- `datum`: Briefdatum (JJJJ-MM-TT, wird als „11. November 2026“ gesetzt). Pflicht: Ohne gültiges `datum` baut das Skript nicht, und es setzt nie selbst das Tagesdatum ein, damit dieselben Quellen dieselbe Mappe ergeben. Für das PDF darf es höchstens 7 Tage (`limits:letter.max_age_days`) alt sein; sonst `datum` auf den Versandtag setzen, neu bauen und erneut freigeben lassen. Dasselbe Datum steht mit dem Ort unter dem Lebenslauf (Regel `cv.sign-off` in `references/template.md`). <!-- rule: letter.date -->
- `ort`: Wohnort aus dem Profil.
- `betreff_einleitung` und `betreff` ergeben den zweistufigen Betreff. Der Agent setzt die Einleitung ausdrücklich: bei Ausbildung „Bewerbung um einen Ausbildungsplatz zum/zur“ (passend zur Berufsbezeichnung), sonst „Bewerbung als“ bzw. „Bewerbung um einen Praktikumsplatz als“; `betreff` ist `occupation` aus `job.json`. Ohne Angabe nutzt das Skript die neutrale Form mit „als“. <!-- rule: letter.subject -->
- Die Referenzzeile „Ihre Anzeige bei der Bundesagentur für Arbeit, Ref.-Nr. …“ setzt das Skript aus `job.json`.
- `dichte`: `normal` oder `dicht`.
- Absätze durch Leerzeilen trennen. Erster Absatz = Anrede, letzter = Grußformel. Kein Markdown-Formatieren im Text.

### `motivationsschreiben.md`

```markdown
---
dichte: normal
---

## Einstieg

Ein Satz.

## Text

Absatz …

Mit freundlichen Grüßen

## Belege

- i-branch | Projektname | eigene Rolle und Ergebnis
- i-terminal | Werkzeug | Einsatz seit …
- i-layers | Lernthema | aktueller Lernstand
```

<!-- rule: motivation.proofs -->
Belege: `- <Linien-Icon> | <Titel> | <kurzer Text>`. Verfügbare Icons: Regel `icons.list` in `references/template.md`. Bei einem Projekt ist der Titel der Projektname aus dem Profil (`projects[].name`), nie ein Ersatz; davon hängt das Projektfoto ab (Regel `project.photo` in `references/profile-schema.md`).

### `kontaktdaten.md`

Aus `job.json` nach `assets/templates/kontaktdaten.md`: Stelle, Ansprechpartner, Postanschrift, Bewerbungsweg, Frist, geforderte Unterlagen, Anrede, offene Punkte. Nur belegte Angaben; keine Bearbeitung durch den Humanizer.

### `email.md`

In `application/`, nach `assets/templates/email.md`:

- **Pflicht** bei Bewerbungsweg `email` (`job.json` → `application.method`): Der Entwurf liegt vor der Abschlussmeldung vor, ist nicht leer, enthält keine offenen `[Platzhalter]` und ist humanisiert. Fehlen belegte Angaben (z. B. Anrede, Ansprechpartner), fragen statt raten. Die QA prüft das, und ohne gültigen Entwurf gibt es kein PDF (`references/qa-and-export.md`, Was `--qa` prüft). <!-- rule: email.required -->
- **An:** Bewerbungsadresse aus `application.email`, sonst die belegte Adresse des Ansprechpartners. Bei Portal oder Post: kein E-Mail-Entwurf, stattdessen kurzer Hinweis auf den Weg.
- **Betreff:** z. B. „Bewerbung um einen Ausbildungsplatz als Fachinformatiker für Systemintegration (Ref.-Nr. …)“
- **Text:** Anrede wie im Anschreiben, zwei bis vier kurze Sätze: was beiliegt, ein konkreter Grund für diese Stelle, Bitte um Rückmeldung, Grußformel, Name, Telefon.
- **Einstieg:** sinngemäß „anbei sende ich Ihnen meine Bewerbungsmappe für die Ausbildungsstelle als <Beruf> (Referenznummer <Ref.-Nr.>).“ (bei Jobs/Praktika „für die Stelle als …“ bzw. „für das Praktikum als …“).
- **Umzug:** Maßgeblich ist der **Suchort** (Ordner `<suchort>/`, `job.json` → `search.city`), nicht der Ort der Firma. Ist der Suchort nicht der Wohnort (`person.address.city`), steht er in `goal.locations` und ist `goal.relocation` `yes`, folgt ein Satz wie „Ein Umzug nach <Suchort> ist für <goal.relocation_timing> geplant.“ Liegt der Suchort am Wohnort, entfällt der Satz. Kein Satz über Pendeln, keine Entfernungsangabe. Fehlt `goal.relocation_timing`, den Nutzer fragen. <!-- rule: email.relocation -->
- **Anhang:** Pfad `application/bewerbungsmappe - <name>.pdf` (entsteht erst nach Freigabe) und geforderte Unterlagen aus `application.required_documents`, nur wenn sie existieren.
- Hinweis am Ende: Entwurf, nicht gesendet.

## Trennung prüfen

Vor dem Bau beide Briefe nebeneinanderlegen:

- Steht der Hauptbeleg für die Eignung im Anschreiben?
- Erklärt das Motivationsschreiben den Antrieb, ohne die Fähigkeiten zu wiederholen?
- Kommt eine Anekdote, ein Projekt oder eine Stärke in beiden als Hauptargument vor?
- Passt ein Satz auf jede beliebige Stelle? Dann streichen oder konkret machen.

Ist eine Antwort falsch, beide Texte überarbeiten.
