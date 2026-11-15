# Mehrere Stellen parallel bearbeiten

Ein Durchlauf hat genau ein Profil und eine oder mehrere Stellen. Was den Nutzer oder den Browser braucht, macht der Hauptagent nacheinander. Was nur Dateien braucht, läuft pro Stelle parallel.

## Aufteilung

<!-- rule: agents.lanes -->
| Schritt | wer | wie |
|---|---|---|
| Profil, Interview, Profilvorlage | Hauptagent | mit dem Nutzer |
| BA-Suche, Auswahl | Hauptagent | Browser, mit dem Nutzer |
| Anzeigen erfassen (`ba_scrape.md`, `job.json`), Captcha | Hauptagent | Browser, nacheinander (Regel `capture.one-tab` in `references/job-search.md`) |
| Duplikatprüfung, Ordner, Ränge | Hauptagent | `check-duplicate`, `references/applications.md` |
| Texte, Mappe, technische QA | ein Schreib-Subagent **pro Stelle**, parallel | nur Dateien und Shell |
| inhaltliche QA | ein Prüf-Subagent pro Stelle, parallel | nur lesen, Bericht in `.tmp/qa/` |
| Freigabe, PDF, Versandablage | Hauptagent | mit dem Nutzer, einzeln pro Mappe |
| Änderungen an der Vorlage | der Editor der Warteschlange | Regel `pins.one-writer` in `references/tencil.md` |

Browserarbeit nie an Subagenten geben: Sie haben je nach Harness keinen Browser, und das Captcha braucht den Nutzer.

## Voraussetzungen vor dem Start der Subagenten

- Profilvorlage gebaut und vom Nutzer freigegeben.
- Pro Stelle: Ordner angelegt, `ba_scrape.md` und `job.json` vollständig und schemagültig, Kontakt erfasst, kein ungeklärtes Duplikat, keine blockierende Frage offen und jede Antwort eingearbeitet (Regel `jobs.open-questions` in `references/job-search.md`). `status profile/<name>` zeigt das je Stelle.

## Auftrag an den Schreib-Subagenten

Rolle, Leseliste und Grenzen stehen in `.claude/agents/bewerbung-writer.md`; die Datei gilt für jedes Harness. Jeder Auftrag nennt genau einen Stellenordner und das Profil:

```text
Profil: profile/<name>
Stelle: profile/<name>/applications/<typ>/<beruf>/<suchort>/<NN-ort-firma>
Rolle, Leseliste und Grenzen: .claude/agents/bewerbung-writer.md
Melde: Pfade, Wortzahlen, QA-Ergebnis, offene Punkte, unbelegte Anforderungen.
```

Gleichzeitige Builds sind sicher: Jeder Subagent schreibt nur in seinen Ordner (Regel `agents.writer-scope` in `.claude/agents/bewerbung-writer.md`); das Ledger wird pro Aufruf unter einer Sperre aus den Ordnern abgeleitet und atomar geschrieben. Höchstens drei Subagenten gleichzeitig (Ratenlimits); mehr Stellen in Wellen zu je drei, im Abstand von 30–60 Sekunden starten. Meldet ein Agent ein Ratenlimit, warten und die Welle halbieren.

## Auftrag an den Prüf-Subagenten

Rolle, Leseliste und Grenzen stehen in `.claude/agents/bewerbung-qa.md`. Der Auftrag nennt Profil und Stellenordner wie oben. Der Subagent prüft die gebaute Mappe nach der Prüfliste in `references/qa-and-export.md` und schreibt einen Bericht nach `.tmp/qa/<NN-ort-firma>.md`; er ändert nichts (Regel `agents.qa-scope` in `.claude/agents/bewerbung-qa.md`).

Der Hauptagent übernimmt die Vorschläge (oder gibt sie an einen neuen Schreib-Auftrag), baut neu und zeigt dann dem Nutzer die Mappe zur Freigabe.

## Harness

- **Claude Code:** Subagenten `bewerbung-writer` und `bewerbung-qa` in `.claude/agents/`. Pro Stelle einen `bewerbung-writer` starten, höchstens drei in derselben Antwort (siehe oben); danach pro Stelle einen `bewerbung-qa`.
- **Codex:** pro Stelle einen Subagenten mit dem Auftragstext oben starten (`spawn_agent` o. ä.), danach auf alle warten; ebenso für die Prüfung.
- **Andere Harnesses:** falls Subagenten möglich sind, wie oben; sonst die Schritte pro Stelle nacheinander selbst ausführen.
