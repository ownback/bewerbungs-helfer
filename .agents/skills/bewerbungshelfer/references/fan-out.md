# Mehrere Stellen parallel bearbeiten

Ein Durchlauf hat genau ein Profil und eine oder mehrere Stellen. Was den Nutzer oder den Browser braucht, macht der Hauptagent nacheinander. Was nur Dateien braucht, läuft pro Stelle parallel.

## Aufteilung

| Schritt | wer | wie |
|---|---|---|
| Profil, Interview, Profilvorlage | Hauptagent | mit dem Nutzer |
| BA-Suche, Auswahl | Hauptagent | Browser, mit dem Nutzer |
| Anzeigen erfassen (`ba_scrape.md`, `job.json`), Captcha | Hauptagent | Browser, **nacheinander**; der Nutzer löst jedes Captcha |
| Duplikatprüfung, Ordner, Ränge | Hauptagent | `check-duplicate`, `references/applications.md` |
| Texte, Mappe, technische QA | ein Schreib-Subagent **pro Stelle**, parallel | nur Dateien und Shell |
| inhaltliche QA | ein Prüf-Subagent pro Stelle, parallel | nur lesen, Bericht in `.tmp/qa/` |
| Freigabe, PDF, Versandablage | Hauptagent | mit dem Nutzer, einzeln pro Mappe |

Browserarbeit nie an Subagenten geben: Sie haben je nach Harness keinen Browser, und das Captcha braucht den Nutzer.

## Voraussetzungen vor dem Start der Subagenten

- Profilvorlage gebaut und vom Nutzer freigegeben.
- Pro Stelle: Ordner angelegt, `ba_scrape.md` und `job.json` vollständig und schemagültig, Kontakt erfasst, kein ungeklärtes Duplikat.

## Auftrag an den Schreib-Subagenten

Jeder Auftrag nennt genau einen Stellenordner und das Profil:

```text
Profil: profile/<name>
Stelle: profile/<name>/applications/<typ>/<beruf>/<suchort>/<NN-ort-firma>
Lies .agents/skills/bewerbungshelfer/references/writing.md und qa-and-export.md.
Schreibe text_generation/anschreiben.md, motivationsschreiben.md, kontaktdaten.md und application/email.md,
wende den Skill humanizer auf Anschreiben, Motivationsschreiben und E-Mail an,
baue mit: python3 tools/build_mappe.py application "<stelle>" --qa
und behebe Befunde nur über die .md-Dateien. Ändere nichts außerhalb des Stellenordners.
Kein PDF, kein Statuswechsel, nichts senden. Melde: Pfade, Wortzahlen, QA-Ergebnis, offene Punkte, unbelegte Anforderungen.
```

Regeln für den Subagenten:

- Arbeitet nur im eigenen Stellenordner. Profil, Profilvorlage, Skill-Vorlage, Ledger-Einträge anderer Stellen und `job.json` bleiben unverändert (fehlt etwas in `job.json`, meldet er es).
- Erfindet nichts; fehlt ein Fakt, meldet er eine Frage statt eines Satzes.
- Setzt keinen Status und erzeugt kein PDF.

Gleichzeitige Builds sind sicher: Jeder schreibt nur in seinen Ordner; das Ledger wird pro Aufruf atomar geschrieben. Bei sehr vielen Stellen (mehr als etwa fünf) in Wellen starten.

## Auftrag an den Prüf-Subagenten

Liest Profil, `job.json`, `ba_scrape.md`, die drei Texte, `email.md` und das Manifest, rendert die Seiten mit `preview` nach `.tmp/previews/<NN-ort-firma>/` und sieht jede Seite an. Prüft die Liste in `references/qa-and-export.md` und schreibt einen kurzen Bericht nach `.tmp/qa/<NN-ort-firma>.md`: Befund, Fundstelle, Vorschlag. Ändert keine Dateien im Profilordner.

Der Hauptagent übernimmt die Vorschläge (oder gibt sie an einen neuen Schreib-Auftrag), baut neu und zeigt dann dem Nutzer die Mappe zur Freigabe.

## Harness

- **Claude Code:** Subagenten `bewerbung-writer` und `bewerbung-qa` in `.claude/agents/`. Pro Stelle einen `bewerbung-writer` starten, alle in derselben Antwort, damit sie parallel laufen; danach pro Stelle einen `bewerbung-qa`.
- **Codex:** pro Stelle einen Subagenten mit dem Auftragstext oben starten (`spawn_agent` o. ä.), danach auf alle warten; ebenso für die Prüfung. Die Rollenbeschreibungen in `.claude/agents/*.md` gelten sinngemäß.
- **Andere Harnesses:** falls Subagenten möglich sind, wie oben; sonst die Schritte pro Stelle nacheinander selbst ausführen.
