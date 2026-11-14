# Änderungen

Hier steht, was sich wann geändert hat. Die Referenzen unter `.agents/skills/bewerbungshelfer/references/` beschreiben nur den heutigen Stand.

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
