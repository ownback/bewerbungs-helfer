# Schreiben: Anschreiben, Motivationsschreiben, E-Mail, Kontaktdaten

<!-- rule: letters.evidence -->
Alle Texte sind deutsch und entstehen nur aus belegten Quellen: Aussagen über den Bewerber aus dem Profil (`<name>_profile.json`), Aussagen über Firma und Stelle aus `job_information/firma.md` (Regel `company.research` in `references/job-search.md`) und aus `job.json`. Jede Aussage über den Bewerber braucht einen Profilbeleg, jede Aussage über die Firma einen Eintrag in `firma.md`. Selbstauskünfte des Nutzers gelten nur in den Grenzen von Regel `profile.self-statements` in `references/profile-schema.md`. Unbelegte Sätze werden gestrichen, nicht geglättet. Fehlt `firma.md`, entsteht kein Anschreiben: erst recherchieren.

## Aufgabenteilung

<!-- rule: letters.separation -->

| Text | Leitfrage | Entsteht | Ton |
|---|---|---|---|
| Anschreiben | Warum diese Firma, warum dieser Beruf, und warum passt beides zu mir? | pro Stelle neu, in fünf Absätzen (Regel `letter.structure`) | sachlich, konkret |
| Motivationsschreiben | Was habe ich über die Jahre selbst gebaut, was habe ich dabei gelernt, was hat funktioniert und was nicht? | einmal pro Profil als Mastertext; pro Stelle ändern sich nur der erste und der letzte Satz (Regel `motivation.master`) | persönlich, erzählend |
| E-Mail | Worum bewerbe ich mich, und was hängt an? | fester Wortlaut (Regel `email.text`) | kurz, förmlich |

**Anschreiben = Firma und Eignung.** Es zeigt, dass der Bewerber die Firma verstanden hat, und begründet, warum er die Theorie und die Praxis des Berufs bewältigt.

**Motivationsschreiben = der eigene Weg.** Es erzählt die Projekte des Bewerbers in ihrer Reihenfolge: was er vorhatte, was gelang, was scheiterte, was er daraus gelernt hat und wie eines zum nächsten führte.

**Keine Geschichte zweimal.** Projekte werden im Motivationsschreiben erzählt. Im Anschreiben steht ein Projekt höchstens als Halbsatz, der eine Fähigkeit belegt (z. B. systematische Fehlersuche), ohne die Geschichte zu wiederholen.

## Anschreiben

<!-- rule: letter.structure -->
Der Aufbau ist eine Vorgabe des Nutzers: Anrede, fünf Absätze, Grußformel. Jeder Absatz bringt etwas Neues, keiner wiederholt einen anderen.

| Absatz | Inhalt | Quelle |
|---|---|---|
| Anrede | `contact.salutation` aus `job.json` mit Komma: „Sehr geehrte Frau Muster,“, „Sehr geehrter Herr Muster,“, ohne belegten Namen „Sehr geehrte Damen und Herren,“ (Regel `capture.contact` in `references/job-search.md`) | `job.json` |
| 1 Einleitung | ein Satz, kurz und direkt: Beruf mit Fachrichtung, Firma, Ausbildungsjahr | `occupation`, `company` und `start` aus `job.json` |
| 2 Warum diese Firma | zuerst in einem kurzen Satz die Quelle der Anzeige, dann konkrete Fakten zur Firma: was sie herstellt oder entwickelt, welche Technologien sie einsetzt, für welche Branchen und Kunden sie arbeitet, einzelne Produkte, Leistungen oder Projekte | `firma.md` |
| 3 Warum dieser Beruf | (a) Theorie: Mathematik, logisches und analytisches Denken, Verständnis für technische Zusammenhänge, und warum das für die theoretischen Inhalte der Ausbildung trägt; (b) Praxis: Arbeit mit den Händen, Hardware, Montage, Werkzeug | Profil |
| 4 Warum gerade diese Firma | die tägliche Arbeit der Firma, verbunden mit dem, was der Bewerber lernen und tun will | `firma.md` und Profil |
| 5 Schluss | Bitte um ein Vorstellungsgespräch; mit `goal.offer_internship` zusätzlich das Angebot eines Praktikums vorab | Profil |
| Grußformel | „Mit freundlichen Grüßen“; Name und Unterschrift setzt die Vorlage | – |

Gerüst mit den festen Sätzen. Was in eckigen Klammern steht, wird pro Stelle geschrieben:

```text
Sehr geehrte Frau Muster,

hiermit bewerbe ich mich um Ihre Ausbildungsstelle als [Beruf mit Fachrichtung] bei [Firma] für das Ausbildungsjahr [Jahr].

Auf Ihre Stellenausschreibung bin ich über die Jobsuche der Bundesagentur für Arbeit aufmerksam geworden. Dadurch wurde mein Interesse an Ihrem Unternehmen geweckt. [Zwei bis vier Sätze mit Fakten aus firma.md: Produkte, Technologien, Branchen, Kunden, Projekte.]

Ein wesentlicher Grund, weshalb ich mich für diesen Ausbildungsberuf entschieden habe, ist [die Verbindung aus Theorie und Praxis, in eigenen Worten]. [Theorie mit Profilbeleg und mit dem Bezug zum Beruf.] [Praxis mit Profilbeleg.]

Besonders angesprochen hat mich dabei [ein Bereich aus dem Alltag der Firma]. Besonders wichtig ist mir [Tätigkeit oder Thema], ebenso [Tätigkeit oder Thema]. [Ein Satz, der beides mit der Arbeit der Firma verbindet.]

Über eine Einladung zu einem persönlichen Vorstellungsgespräch würde ich mich sehr freuen. [Nur mit goal.offer_internship:] Auch ein Praktikum vorab in Ihrem Unternehmen würde mir viel bedeuten.

Mit freundlichen Grüßen
```

Zu den Absätzen:

- **Absatz 1:** Der Beruf ist `occupation`, die Firma steht exakt wie in der Anzeige und mit passendem Artikel („bei der Muster GmbH“), das Jahr ist das Jahr des Beginns (`start` in `job.json`, sonst `goal.start`). Bei Jobs heißt es „um Ihre Stelle als … bei …“, bei Praktika „um einen Praktikumsplatz als … bei …“, beides ohne Ausbildungsjahr.
- **Absatz 2:** Die Quelle ist immer die Jobsuche der Bundesagentur für Arbeit (Regel `hard.source` in `CLAUDE.md`). Die Begriffe der Anzeige (Schlüsselwörter in `firma.md`) stehen in ganzen Sätzen, die Verständnis zeigen, nie als Aufzählung von Schlagwörtern.
- **Absatz 3, Theorie:** begründen, woher die Sicherheit kommt, und die Mathematik mit dem Beruf verbinden (technische Zusammenhänge verstehen, Fehler eingrenzen, systematisch vorgehen). Nie schreiben, dass die Theorie oder die Berufsschule „kein Problem“ sei. Als Belege dienen Selbstauskünfte (`voice.self_statements`), `voice.strengths`, `voice.solved_problem` und Projekte.
- **Absatz 3, Praxis:** Belege aus `education`, `experience`, `skills` und `projects` (z. B. ein technischer Bildungsgang, ein Praktikum in der Fertigung, selbst montierte Hardware).
- **Absatz 4:** geht über Absatz 2 hinaus. Absatz 2 sagt, was den Bewerber an der Firma interessiert; Absatz 4 sagt, warum ihre tägliche Arbeit zu dem passt, was er lernen und tun will. Kein Fakt aus Absatz 2 kommt wieder.
- **Absatz 5:** Der Praktikumssatz steht nur, wenn `goal.offer_internship` `true` ist, und nie bei einer Bewerbung um ein Praktikum.
- Konkret schlägt allgemein. Der Brief darf nicht wie eine Vorlage klingen, in der nur der Firmenname getauscht wurde. Schwach: „Ich interessiere mich für technische Zusammenhänge und arbeite gerne analytisch sowie praktisch.“ Stärker: „Besonders interessant finde ich die Verbindung zwischen theoretischer Analyse und praktischer Umsetzung: Ich möchte technische Zusammenhänge mathematisch verstehen und ihre Funktionsweise direkt an der Hardware nachvollziehen.“
- Anrede in der Höflichkeitsform groß: Sie, Ihr, Ihre, Ihnen.

<!-- rule: letter.phrases -->
Formulierungen. Die linke Spalte steht nie in einem Brief, die rechte ersetzt sie:

| nie | stattdessen |
|---|---|
| „Gestolpert bin ich auf …“ | „Auf Ihre Stellenausschreibung bin ich über … aufmerksam geworden.“ |
| „interessiert an Ihrem Unternehmen“ | „Dadurch wurde mein Interesse an Ihrem Unternehmen geweckt.“ |
| „Ein guter Grund, weshalb …“ | „Ein wesentlicher Grund, weshalb ich mich für diesen Ausbildungsberuf entschieden habe, ist …“ |
| „Theorie“ oder „Berufsschule“ als Hürde | „die theoretischen Inhalte der Ausbildung“ |
| „Ich habe bereits erwähnt …“ | „Besonders angesprochen hat mich dabei …“ |
| „Für mich wichtig ist …“ | „Besonders wichtig ist mir …“ |

<!-- rule: letter.length -->
Umfang: Es gibt kein Wortziel. Der Brief muss auf eine Seite passen, und das entscheidet allein die Überlaufprüfung von `application --qa`. Zuerst mit `dichte: normal` bauen (Brieftext in 10 pt). Meldet die Prüfung einen Überlauf, `dichte: dicht` setzen (9 pt, engerer Satz). Läuft der Brief auch dann über, kürzen. Die Wortzahl nennt der Bau nur zur Information.

## Motivationsschreiben

<!-- rule: motivation.master -->
Das Motivationsschreiben ist **ein Mastertext pro Profil**. Er liegt in `profile/<name>/assets/profile/<name>_motivation.md` und hat dasselbe Format wie `motivationsschreiben.md` (Dateiformate; Vorlage `assets/templates/motivation_master.md`).

Inhalt, nach der Vorgabe des Nutzers: alle eigenen Projekte in der Reihenfolge, in der sie entstanden sind. Je Projekt, was der Bewerber vorhatte, was er getan hat, was funktioniert hat, was nicht funktioniert hat und was er daraus gelernt hat; dazu, wie eines zum nächsten geführt hat.

1. **Einstieg:** ein persönlicher Satz, womit alles anfing (erscheint groß über dem Text).
2. **Text:** die Projekte der Reihe nach. Der erste Satz und der letzte Satz vor der Grußformel sind die beiden Sätze, die sich auf Beruf und Firma beziehen; im Mastertext stehen sie neutral, so dass sie zu jeder Stelle des Zielberufs passen.
3. **Belege:** drei kurze Einträge für die Seitenspalte (Regel `motivation.proofs`).

Quellen sind `projects[]` (`goal`, `own_role`, `tools`, `result`, `learned`, `worked`, `did_not_work`, `connection`) und der Block `motivation` im Profil. Erzählt wird nur, was dort steht. Ein leeres Feld wird nicht ausgefüllt, sondern erfragt (Regel `interview.projects` in `references/interview.md`); bis dahin fehlt dieser Teil der Geschichte.

Den Mastertext schreibt der Hauptagent nach dem Interview, wendet den Humanizer an und legt ihn dem Nutzer vor. Er gilt erst nach dessen ausdrücklicher Freigabe. Ändert sich ein Projekt im Profil, wird der Mastertext angepasst und neu freigegeben.

Pro Stelle:

1. Den Mastertext unverändert nach `text_generation/motivationsschreiben.md` kopieren.
2. Nur den ersten und den letzten Satz von `## Text` anpassen: Sie nennen die Firma oder ihr Arbeitsgebiet mit einem Fakt aus `firma.md`. Einstieg, alle übrigen Sätze, Grußformel und Belege bleiben wörtlich.
3. Der Bau vergleicht beide Dateien und warnt, wenn die Stelle an einer anderen Stelle abweicht (`references/qa-and-export.md`, Was `--qa` prüft).

Fehlt der Mastertext, schreibt niemand ein Motivationsschreiben für eine Stelle: Der Schreib-Subagent meldet es, der Hauptagent holt Interview und Freigabe nach. Nach einer Änderung am Mastertext werden die Kopien aller Stellen, die noch nicht gesendet sind, neu erzeugt.

<!-- rule: motivation.length -->
Kein Wortrichtwert für den Mastertext (Entscheidung des Nutzers vom 2026-11-15): Er muss auf eine Seite passen, erst normal, dann mit `dichte: dicht`, sonst kürzen. Die Wortzahl im Build ist nur Information.

## Stimme

<!-- rule: letters.voice -->
- Kurze und lange Sätze mischen. Konkrete Beispiele statt Adjektive.
- Nicht verwenden: „mit großem Interesse“, „ich bin sehr motiviert“, „Teamplayer“, unbelegte Superlative, erfundene Anekdoten, künstliche Gegensatzpaare („nicht X, sondern Y“), Dreierketten als Stilmittel, Floskeln wie „Darüber hinaus“ am Satzanfang.
- Die festen Sätze aus Regel `letter.structure` und Regel `email.text` sind Vorgaben des Nutzers und bleiben wörtlich, auch wenn sie förmlich klingen.
- `voice.avoid` und `motivation.boundaries` aus dem Profil beachten (persönliche Verbote, vom Nutzer im Interview genannt).
- Alter nur als exakte Zahl und nur, wenn der Nutzer es wünscht; keine Näherungen wie „bald 21“. Praktika nie als Anstellung darstellen, Zeiträume mit „ca.“ nur, wo das Profil `approx` führt.
- Name und Kontaktdaten exakt wie im Profil, Firmenname exakt wie in der Anzeige.

## Humanizer

<!-- rule: letters.humanizer -->
Nach dem Entwurf den Skill `humanizer` (blader/humanizer, Version 3.1.0, MIT; installiert unter `~/.agents/skills/humanizer/`) im Standardmodus „humanize“ anwenden: auf `anschreiben.md`, auf den Mastertext des Motivationsschreibens (einmal, vor der Freigabe) und pro Stelle auf dessen zwei angepasste Sätze. Nicht auf `email.md` (fester Wortlaut) und nicht auf `kontaktdaten.md`. Die festen Sätze des Anschreibens (Regel `letter.structure`) stehen danach wieder wörtlich da. Nicht das gleichnamige Claude-Code-Plugin `humanizer:humanizer` verwenden: Der Nutzer hat am 2026-11-15 beide an demselben deutschen Probetext verglichen und diese Fassung gewählt (schlichter, fügt keine Schlussfolgerungen hinzu). Fehlt der Skill, ihn aus `github:blader/humanizer` in dieser Version nach `~/.agents/skills/humanizer/` installieren oder den Nutzer fragen. Im Bericht der Stelle Name und Version des verwendeten Humanizers nennen. Der Skill darf Formulierungen ändern, aber keine Fakten hinzufügen; danach erneut gegen Profil und `firma.md` prüfen.

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

hiermit bewerbe ich mich um Ihre Ausbildungsstelle als …

Mit freundlichen Grüßen
```

- `datum`: Briefdatum (JJJJ-MM-TT, wird als „11. November 2026“ gesetzt). Pflicht: Ohne gültiges `datum` baut das Skript nicht, und es setzt nie selbst das Tagesdatum ein, damit dieselben Quellen dieselbe Mappe ergeben. Für das PDF darf es höchstens 7 Tage (`limits:letter.max_age_days`) alt sein; sonst `datum` auf den Versandtag setzen, neu bauen und erneut freigeben lassen. Dasselbe Datum steht mit dem Ort unter dem Lebenslauf (Regel `cv.sign-off` in `references/template.md`). <!-- rule: letter.date -->
- `ort`: Wohnort aus dem Profil.
- `betreff_einleitung` und `betreff` ergeben den zweistufigen Betreff. Der Agent setzt die Einleitung ausdrücklich: bei Ausbildung „Bewerbung um einen Ausbildungsplatz zum/zur“ (passend zur Berufsbezeichnung), sonst „Bewerbung als“ bzw. „Bewerbung um einen Praktikumsplatz als“; `betreff` ist `occupation` aus `job.json`. Ohne Angabe nutzt das Skript die neutrale Form mit „als“. <!-- rule: letter.subject -->
- Die Referenzzeile „Ihre Anzeige bei der Bundesagentur für Arbeit, Ref.-Nr. …“ setzt das Skript aus `job.json`.
- `dichte`: `normal` oder `dicht` (Regel `letter.length`).
- Absätze durch Leerzeilen trennen. Erster Absatz = Anrede, dann die fünf Absätze aus Regel `letter.structure`, letzter = Grußformel. Kein Markdown-Formatieren im Text.

### `motivationsschreiben.md` und der Mastertext

```markdown
---
dichte: normal
---

## Einstieg

Ein Satz.

## Text

Erster Satz mit Bezug zu Beruf oder Firma. Danach die Projekte …

… Letzter Satz mit Bezug zu Beruf oder Firma.

Mit freundlichen Grüßen

## Belege

- i-branch | Projektname | eigene Rolle und Ergebnis
- i-terminal | Werkzeug | Einsatz seit …
- i-layers | Lernthema | aktueller Lernstand
```

Dasselbe Format gilt für den Mastertext `<name>_motivation.md` und für die Kopie der Stelle (Regel `motivation.master`).

<!-- rule: motivation.proofs -->
Belege: `- <Linien-Icon> | <Titel> | <kurzer Text>`. Verfügbare Icons: Regel `icons.list` in `references/template.md`. Bei einem Projekt ist der Titel der Projektname aus dem Profil (`projects[].name`), nie ein Ersatz; davon hängt das Projektfoto ab (Regel `project.photo` in `references/profile-schema.md`).

### `kontaktdaten.md`

Aus `job.json` nach `assets/templates/kontaktdaten.md`: Stelle, Ansprechpartner, Postanschrift, Bewerbungsweg, Frist, geforderte Unterlagen, Anrede, offene Punkte. Nur belegte Angaben; keine Bearbeitung durch den Humanizer.

### `email.md`

In `application/`, nach `assets/templates/email.md`:

- **Pflicht** bei Bewerbungsweg `email` (`job.json` → `application.method`): Der Entwurf liegt vor der Abschlussmeldung vor, ist nicht leer und enthält keine offenen `[Platzhalter]`. Fehlen belegte Angaben (z. B. Anrede, Ansprechpartner), fragen statt raten. Die QA prüft das, und ohne gültigen Entwurf gibt es kein PDF (`references/qa-and-export.md`, Was `--qa` prüft). <!-- rule: email.required -->
- **An:** Bewerbungsadresse aus `application.email`, sonst die belegte Adresse des Ansprechpartners. Bei Portal oder Post: kein E-Mail-Entwurf, stattdessen kurzer Hinweis auf den Weg.
- **Betreff:** z. B. „Bewerbung um einen Ausbildungsplatz als Fachinformatiker für Systemintegration (Ref.-Nr. …)“
- **Text:** fester Wortlaut nach der Vorgabe des Nutzers, ohne weitere Sätze: <!-- rule: email.text -->

  ```text
  Sehr geehrte Frau Muster,

  hiermit bewerbe ich mich um Ihre Ausbildungsstelle als [Beruf mit Fachrichtung] bei [Firma] für das Ausbildungsjahr [Jahr].

  Derzeit wohne ich in [Wohnort], plane aber, [Zeitpunkt] nach [Suchort] umzuziehen.

  Im Anhang finden Sie meine Bewerbungsmappe mit allen Unterlagen.

  Über eine Eingangsbestätigung würde ich mich freuen.

  Mit freundlichen Grüßen
  [Vorname Nachname]
  [Telefon]
  ```

  Anrede und erster Satz sind dieselben wie im Anschreiben (Regel `letter.structure`, Anrede und Absatz 1, auch für Jobs und Praktika). Name und Telefonnummer stehen wie in `person.name` und `person.phone` (Signatur mit Telefon: Entscheidung des Nutzers vom 2026-11-15). Der zweite Absatz steht nur nach Regel `email.relocation`.
- **Umzug:** Maßgeblich ist der **Suchort** (Ordner `<suchort>/`, `job.json` → `search.city`), nicht der Ort der Firma. Ist der Suchort nicht der Wohnort (`person.address.city`), steht er in `goal.locations` und ist `goal.relocation` `yes`, steht der Satz „Derzeit wohne ich in <Wohnort>, plane aber, <Zeitpunkt> nach <Suchort> umzuziehen.“ Der Zeitpunkt kommt aus `goal.relocation_timing`, grammatisch eingepasst („im Sommer 2027“); steht im Profil ein Abschluss mit `education[].expected: true`, der vor dem Umzug endet, heißt es „nach meinem Abschluss im Sommer 2027“. Liegt der Suchort am Wohnort, entfällt der ganze Absatz. Kein Satz über Pendeln, keine Entfernungsangabe. Fehlt `goal.relocation_timing`, den Nutzer fragen. <!-- rule: email.relocation -->
- **Anhang:** Pfad `application/bewerbungsmappe - <name>.pdf` (entsteht erst nach Freigabe) und geforderte Unterlagen aus `application.required_documents`, nur wenn sie existieren.
- Hinweis am Ende: Entwurf, nicht gesendet.

## Vor dem Bau prüfen

- Anschreiben: fünf Absätze in der Reihenfolge von Regel `letter.structure`, die festen Sätze wörtlich, keine Formulierung aus der linken Spalte von Regel `letter.phrases`.
- Hat jeder Satz über die Firma einen Eintrag in `firma.md` und jeder Satz über den Bewerber einen Profilbeleg?
- Wiederholt Absatz 4 einen Fakt aus Absatz 2? Dann einen von beiden ersetzen.
- Passt ein Satz der Absätze 2 bis 4 auf jede beliebige Firma? Dann streichen oder konkret machen.
- Erzählt das Anschreiben ein Projekt, das im Motivationsschreiben steht, als Geschichte nach? Dann auf einen Halbsatz kürzen.
- Motivationsschreiben: Weicht die Kopie nur im ersten und im letzten Satz vom Mastertext ab?
- E-Mail: Wortlaut nach Regel `email.text`, Umzugsabsatz nur nach Regel `email.relocation`.
