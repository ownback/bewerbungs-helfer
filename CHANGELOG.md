# Änderungen

Hier steht, was sich wann geändert hat. Die Referenzen unter `.agents/skills/bewerbungshelfer/references/` beschreiben nur den heutigen Stand.

## 2026-11-17: Recherche-Subagent, Sammelfreigabe, Mastertext abgleichen

Damit ein neuer Durchlauf ohne die Arbeitsnotizen in `.tmp/` gleich arbeitet:

- **Recherche-Subagent** `.claude/agents/bewerbung-recherche.md` auf Claude Haiku (vorher nur eine Zeile in `fan-out.md`; der Auftrag stand in einer Notiz unter `.tmp/`). Neu `tools/research.py`: `fetch` holt Firmenseiten als Text nach `.tmp/research/`, `verify` prüft jeden Beleg in `firma.md` wörtlich gegen die gelesenen Quellen (vorher Hilfsskripte unter `.tmp/`). Der Subagent prüft auch Portal-Link und Bewerbungsadressen.
- **Sammelfreigabe** (Regel `approval.batch` in `references/qa-and-export.md`): Der Nutzer darf mehrere Mappen auf einmal freigeben; vorher hieß es „einzeln pro Mappe“. Prüfsumme weiter pro Mappe.
- **`build_mappe.py motivation-sync`**: übernimmt einen geänderten Mastertext in die Motivationsschreiben der offenen Stellen, erster und letzter Satz der Stelle bleiben (vorher Skript unter `.tmp/` oder alle Briefe neu schreiben). „Co.“ beendet für die Satzerkennung keinen Satz mehr.

## 2026-11-16: Bewerbungsweg aus der Anzeige, Antworten sortieren

- **Regel `apply.channel` geändert:** Nennt die Anzeige ein Portal oder Online-Formular, gilt das Portal. Vorher ging E-Mail vor, sobald irgendeine Bewerbungsadresse bekannt war. Drei Firmen (KTE, KIT, E-Werk Mittelbaden) haben E-Mail-Bewerbungen deshalb abgelehnt und auf ihr Portal verwiesen. Nennt die Anzeige nur die Post, geht E-Mail weiter vor.
- **Antworten sortieren:** `send_mail.py inbox` listet den Posteingang mit UID, `send_mail.py move <uid>… --to <ordner>` verschiebt Nachrichten. Ablage nach Regel `mail.sort` in `references/applications.md`.

## 2026-11-16: E-Mail-Versand stapelweise nach Freigabe

- **Neu:** `tools/send_mail.py` (Standardbibliothek): `setup`, `check`, `preview`, `test`, `send`, `replies`. Versand über SMTP mit App-spezifischem Passwort, Kopie in „Gesendet“ per IMAP, danach `mark-sent`; `replies` listet Antworten der Firmen-Domains, nur lesend (Regel `send.batch` in `references/applications.md`).
- **Regel `hard.no-send` geändert:** vorher „nichts automatisch senden“, der Nutzer schickte jede E-Mail selbst. Jetzt sendet der Agent E-Mails stapelweise, aber nur nach einem ausdrücklichen Ja des Nutzers zu genau diesem Stapel. Portale und Post bleiben beim Nutzer.
- **Zugangsdaten** liegen außerhalb des Repos unter `~/.config/bewerbungs-helfer/` (0600) und kommen über die sichere Eingabe des Harness, nie über den Chat.

## 2026-11-15: Leitfäden des Nutzers für Anschreiben, E-Mail und Motivationsschreiben

Der Nutzer hat festgelegt, wie seine Texte aufgebaut sind. Das Aussehen der Mappe ist unverändert.

- **Anschreiben:** fester Aufbau aus Anrede, fünf Absätzen und Grußformel (Einleitung, warum diese Firma, warum dieser Beruf, warum gerade diese Firma, Schluss) mit festen Sätzen und einer Tabelle von Formulierungen, die ersetzt werden (Regeln `letter.structure` und `letter.phrases` in `references/writing.md`). Vorher: Einstieg, zwei oder drei Fähigkeiten, Arbeitserfahrung, Bildungsstand, Lücke, Schluss. „hiermit bewerbe ich mich“ ist jetzt der vorgegebene erste Satz und steht nicht mehr auf der Verbotsliste.
- **Kein Wortziel für das Anschreiben:** Es zählt nur, dass der Brief auf eine Seite passt: zuerst `dichte: normal`, bei Überlauf `dicht`, dann kürzen (vorher Richtwert ca. 230 Wörter, „erst kürzen, dann verdichten“). `limits.json` hat `letter.words` nicht mehr; der Bau nennt die Wortzahl des Anschreibens nur noch zur Information.
- **Firmenrecherche:** Neu ist `job_information/firma.md` (Vorlage `assets/templates/firma.md`): Fakten zur Firma aus Anzeige, Portalseite und ihrer eigenen Website, jeder mit wörtlichem Beleg, Quelle und Abrufdatum. Die Briefe stützen sich nur darauf (Regel `company.research` in `references/job-search.md`, Abschnitt 9; vorher direkt auf `company_facts[]` in `job.json`). Der Schritt steht im Ablauf vor dem Schreiben; `status` nennt ihn als nächsten Schritt, `application` warnt, solange die Datei fehlt.
- **E-Mail:** fester Wortlaut des Nutzers (Regel `email.text` in `references/writing.md`): Bewerbungssatz, bei Suchort ungleich Wohnort der Umzugssatz „Derzeit wohne ich in …, plane aber, … nach … umzuziehen.“, Hinweis auf den Anhang, Bitte um Eingangsbestätigung, Name ohne Telefon. Vorher zwei bis vier freie Sätze mit „anbei sende ich Ihnen …“ und einem Grund für die Stelle. Der Humanizer läuft nicht mehr über die E-Mail.
- **Motivationsschreiben:** ein Mastertext pro Profil in `assets/profile/<name>_motivation.md` (Vorlage `assets/templates/motivation_master.md`), der die eigenen Projekte der Reihe nach erzählt und den der Nutzer einmal freigibt. Pro Stelle wird er kopiert, und nur der erste und der letzte Satz von `## Text` ändern sich (Regel `motivation.master` in `references/writing.md`). Vorher entstand der Text pro Stelle neu. `application` warnt, wenn der Mastertext fehlt oder die Kopie an anderer Stelle abweicht.
- **Profil:** neue optionale Felder `projects[].learned`, `worked`, `did_not_work`, `connection` (mit sechs Interviewfragen je Projekt, Regel `interview.projects` in `references/interview.md`), `goal.offer_internship` (Praktikumssatz am Schluss des Anschreibens) und `voice.self_statements` (Selbstauskünfte wie „Ich bin gut in Mathematik.“, die Briefe nur allgemein wiedergeben; Regel `profile.self-statements` in `references/profile-schema.md`).
- **Subagenten:** Der Schreib-Subagent liest zusätzlich `firma.md` und den Mastertext und schreibt keinen der beiden selbst; die Firmenrecherche darf an einen Recherche-Subagenten mit Browser gehen.

## 2026-11-15: Ausgewählte Gestaltung aus dem Entwurf (Reiter, Lebenslauf, Chips, Brief)

Der Nutzer hat aus einem Gegenentwurf einzelne Teile übernommen. Unverändert bleiben das dunkle Deckblatt samt Inhaltsangabe, der symmetrische Briefkopf, die Sprachen, die Belege-Spalte und die Regel „kein Firmenname auf dem Deckblatt“.

- **Registerreiter:** Der Reiter zeigt den Kurznamen des eigenen Abschnitts und die Seitenzahl („Lebenslauf 3“), vorher nur die Zahl. Die Inhaltsangabe aller Abschnitte steht weiter nur auf dem Deckblatt. Auf schmalen Bildschirmen steht der Reiter links.
- **Lebenslauf, Blöcke und Einträge:** Blocküberschriften sind fett ohne Icon mit einer durchgezogenen Linie in Textfarbe (vorher Icon und Haarlinie). Der Ort steht hinter der Organisation in derselben Zeile, zwischen zwei Einträgen steht eine Haarlinie. Die Lesereihenfolge beginnt mit der Schulbildung (`education`, `experience`, `skills`, `languages`; vorher Erfahrung zuerst), das ist auch der Standard von `presentation.cv_layout`. `presentation.cv_projects.icon` hat keine Wirkung mehr. Im View-Model hat `timeline-item` die Schlüssel `place` und `role` statt `meta`.
- **Fähigkeiten:** Eine Haarlinie trennt nur noch die Gruppen, nicht mehr jede Zeile. Legende „Skala 1–5“ und Blockname bleiben.
- **Abschluss des Lebenslaufs:** Die letzte Lebenslauf-Seite endet mit Ort, Datum (Briefdatum der Stelle), Unterschriftsbild und Name. Die Einwilligung `person.signature.consent` gilt damit für Anschreiben und Lebenslauf; das Interview fragt ausdrücklich nach beiden Stellen. `master.json` hat dafür den Platzhalter `slots.cv_sign`.
- **Logos in Markenfarbe:** Die Technik-Chips zeigen ihre Logos farbig (vorher einfarbig grau). Die Chips bleiben hell, der Name dunkel; Linien-Icons bleiben einfarbig. Neu ist `assets/icons/sources.json` mit Quelldatei und Farbe je Logo-Symbol; `tools/devicon_symbols.py` liest sie (`fill: "file"` behält die Farben der Datei, `fill: "#rrggbb"` färbt das ganze Logo), gibt mit `--urls` die Ladebefehle aus und lehnt Symbole ohne Eintrag ab. `tools/check_repo.py docs` vergleicht die Datei mit `icons.svg`. Die Tabelle „Symbol → Quelldatei“ in `assets/icons/README.md` ist dadurch ersetzt.
- **Neue Symbole:** `dv-gitlab`, `dv-jenkins`, `dv-raspberrypi`, `si-linuxcontainers` (LXC), `si-openwrt` und das Linien-Icon `i-ethernet` (Lucide `ethernet-port`). Für Jujutsu gibt es in den festgelegten Versionen kein Logo: `i-branch`.
- **Anschreiben:** Der Brieftext steht in 10 pt (`--fs-letter`, vorher 9,6 pt), der Richtwert ist ca. 230 Wörter (`limits:letter.words.normal`, vorher 250). Der dichte Modus bleibt bei 9 pt und ca. 350 Wörtern. Der Bau schreibt dazu, wenn eine Wortzahl über dem Richtwert der gewählten Dichte liegt.
- **Begriff → Symbol:** Die Tabelle in `assets/icons/README.md` nennt jetzt auch PC-Montage, Ethernet-Verkabelung, Hardware-Reparatur, GitLab, Jenkins, Jujutsu, LXC (Proxmox), NixOS-Container, OpenWRT und Raspberry Pi OS.

## 2026-11-15: Ein Editor für die Vorlage, ein Zuhause pro Regel

Das Aussehen der Mappe ist unverändert (Seitenvergleich: 0 geänderte Seiten für Master-Vorlage, Profilvorlage und eine Bewerbung).

- **Warteschlange für Änderungen an der Vorlage:** `tools/pin_queue.py` (`enqueue`, `next`, `done`, `status`). Ein Pin-Thread ändert nichts mehr selbst, er reiht ein. Es schreibt nur der Editor, der die Sperre `.tmp/locks/template.lock` hält; er arbeitet die Anfragen unter `.tmp/pins/` der Reihe nach ab. Ohne T3 Code wird der Agent selbst Editor, wenn die Sperre frei ist. `references/tencil.md` ist darum herum neu geschrieben. Vorher bearbeitete jeder Pin-Thread die Vorlage direkt und sollte sich mit den anderen abstimmen.
- **Neue Prüfung `pins`** in `tools/check_repo.py` (Teil von `all` und beider Hooks): Eine geänderte Datei unter `assets/mappe/` ohne Anfrage ist ein Befund. `pin_queue.py done` schließt eine Anfrage nur ab, wenn `check_repo.py all` ohne Befund ist.
- **Zahlen in einer Datei:** `assets/mappe/limits.json` hält Wortgrenzen, das Höchstalter des Briefdatums, die Fenstergrößen der QA, die Umbruchlänge für E-Mail-Adressen, die Schwellen der Namensgröße, den Richtwert für den Füllgrad und die Auflösung des Seitenvergleichs. `tools/build_mappe.py` liest sie dort; die Werte sind dieselben wie zuvor. Die Doku nennt den Schlüssel als `limits:<pfad>`.
- **Ein Zuhause pro Regel:** Regeln tragen an ihrem Zuhause eine Id (`<!-- rule: <id> -->`); andere Dateien verweisen mit „Regel `<id>` in `<datei>`“ und wiederholen sie nicht. `python3 tools/check_repo.py rules` listet sie. Die harten Regeln stehen nur noch in `CLAUDE.md`; `SKILL.md` verweist darauf. Die Agentendateien unter `.claude/agents/` enthalten Rolle, Leseliste, Befehl, Grenzen und Bericht; die Leseliste nennt jetzt auch `job_information/portal_page.md`.
- **Neue Prüfung `docs`** in `tools/check_repo.py` (Teil von `all` und beider Hooks): Regel-Ids eindeutig, Verweise treffen ihr Zuhause; Pfade, Dateinamen, Befehle, Schalter, Schemafelder und Symbol-Ids existieren; Zahlen passen zu `limits.json` oder zum gezählten Wert; keine Formulierung aus `tools/stale-terms.txt`.
- **Verlauf nur noch hier:** Hinweise auf frühere Designrunden sind aus Referenzen und Schema entfernt. Was sie festhielten: Seit Runde 4 gibt es keine Fußzeile, die Seitenzahl steht im Registerreiter. Seit Runde 6 fragt das Interview pro Projekt nach einem eigenen Foto, und ein Projektfoto erscheint nur am Beleg mit dem Projektnamen als Titel, sonst ohne Platzhalter.
- `tools/check_repo.py` nimmt mehrere Prüfungen in einem Aufruf an; `tools/fresh_clone_test.py` führt im Klon alle außer `pins` aus.
- Die Doku zur Namensgröße auf dem Deckblatt nennt keine Obergrenze mehr für `is-xlong`; das Skript hatte nie eine.

## 2026-11-14: Vorlage aus Quellen, eine Stelle für Markup

Das Aussehen der Mappe ist unverändert (Seitenvergleich: 0 geänderte Seiten für Master-Vorlage, Profilvorlage und eine Bewerbung). Geändert hat sich der Aufbau dahinter.

- **Quellen der Vorlage** unter `assets/mappe/`: `tokens.css`, `mappe.css`, `screen.css`, `fonts.css`, `icons.svg`, `partials/*.html`, `master.json`. Das Markup steht nur noch in den Partials; `tools/build_mappe.py` baut ein View-Model und enthält kein HTML mehr (`tools/mustache_lite.py` rendert, mit strengen Schlüsseln).
- **Master-Vorlage ist ein Bauergebnis:** `assets/bewerbungsmappe.html` entsteht mit `build_mappe.py master` aus denselben Partials und `master.json`. Sie wird nicht mehr von Hand bearbeitet; `tools/check_repo.py` (Prüfung `template`) und der Hook melden jede Abweichung. Jede Mappe enthält nur noch die Symbole, die sie verwendet.
- **Bewerbungen entstehen aus den Quellen**, nicht mehr durch Austausch von Abschnitten in der gebauten Profilvorlage. Die Profilvorlage bleibt Vorschau und Freigabeobjekt; ist sie nicht aktuell, warnt `application`.
- **Freigabe mit Prüfsumme:** `status … html_approved` speichert `approved_sha256` (HTML und Bilder). `application --pdf` verweigert den Export, wenn die neu gebaute Mappe abweicht.
- **Briefdatum ist Pflicht:** `datum` im Kopf von `anschreiben.md`; das Skript setzt kein Tagesdatum mehr ein. `--pdf` verweigert ein Datum, das älter als 7 Tage ist.
- **Pins finden ihre Quelle:** Jede gebaute Datei trägt `data-part` (Partial, Aussehen) und `data-origin` (Inhalt). `tools/serve_template.py` löst beide zu Datei und Zeile auf.
- **Neue Befehle:** `master [--check]`, `snapshot --save|--compare` (Seitenvergleich), `rebuild --check` (Byte-Vergleich mit den Quellen), `contract` (Vertrag zwischen View-Model, Partials und CSS; ersetzt die Klassenliste in `references/template.md`), `--qa=fast` und `qa --fast`.
- **QA:** Die Sonde steht in `assets/mappe/qa.js`. Die Prüfung legt keine Hilfsdateien mehr neben die Mappe und startet Chromium einmal für alle Bildschirmbreiten und einmal für das PDF. Das PDF bekommt Lesezeichen, wo Chromium das kann.
- **Schemaprüfung ohne Installation:** `validate` nutzt `tools/schema_lite.py`; das Paket `jsonschema` ist nicht mehr nötig.
- **Frischer-Klon-Test, Stufe 1:** `tools/fresh_clone_test.py`.
- Behoben: Auf Folgeseiten passte die Id der Überschrift nicht zu `aria-labelledby` der Seite (ohne sichtbare Wirkung).
- Entfallen: `data-slot` an den Seiten Anschreiben und Motivationsschreiben, der QA-Schnipsel im Kommentar der Vorlage, Exit-Code 3 von `validate`.
