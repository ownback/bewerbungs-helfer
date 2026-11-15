# Änderungen

Hier steht, was sich wann geändert hat. Die Referenzen unter `.agents/skills/bewerbungshelfer/references/` beschreiben nur den heutigen Stand.

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
