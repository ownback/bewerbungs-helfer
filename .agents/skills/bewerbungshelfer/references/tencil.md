# Vorlage visuell prüfen und ändern (Tencil und Warteschlange)

Der Nutzer sieht eine Mappe im Browser, setzt mit Tencil einen Pin auf ein Element und beschreibt die Änderung. Diese Datei regelt, wie aus dem Pin eine Änderung an den Quellen wird, ohne dass sich mehrere Agenten in die Quere kommen. Sie gilt genauso für Änderungen an der Vorlage, die der Nutzer im Gespräch wünscht.

## Eine Warteschlange, ein Editor

<!-- rule: pins.one-writer -->
Jede Änderung an den Quellen der Vorlage (`assets/mappe/`) ist eine Anfrage in `.tmp/pins/`. Es schreibt nur der **Editor**: der Agent, der die Sperre `.tmp/locks/template.lock` hält. Alle anderen reihen ihre Anfrage ein und bearbeiten nichts. Der Editor arbeitet die Anfragen einzeln in der Reihenfolge ihres Eingangs ab.

Das Werkzeug dafür ist `tools/pin_queue.py`:

| Befehl | Zweck | Exit-Code |
|---|---|---|
| `enqueue --text "…" [--context "…"] [--from …]` | Anfrage anlegen: `.tmp/pins/<zeit>-<id>.md` mit dem Wunsch des Nutzers, der Kontextzeile des Pins und daraus `data-part` und `data-origin`. Die Ausgabe nennt die Kennung der Anfrage und den Stand der Sperre. `--file <datei>` statt `--text` für langen Text. | 0 |
| `next --holder <name>` | Editor werden oder bleiben und die älteste offene Anfrage holen. Solange sie nicht abgeschlossen ist, liefert der Befehl dieselbe Anfrage erneut und hält die Sperre frisch. | 0 Anfrage · 2 Warteschlange leer, Sperre frei · 3 ein anderer ist Editor |
| `done <kennung> --holder <name> --result "…"` | Anfrage abschließen. Der Befehl ruft `tools/check_repo.py all` auf und lehnt bei einem Befund ab. Er hält die Prüfsummen der geänderten Quellen fest, verschiebt die Anfrage nach `.tmp/pins/done/` und gibt die Sperre frei, wenn nichts mehr offen ist. | 0, bei Befund 1 |
| `status` | Sperre, offene Anfragen, geänderte Quellen ohne Anfrage | 0 |

`python3 tools/check_repo.py pins` (Teil von `all`, des Git-Hooks und des Claude-Code-Hooks) schlägt fehl, wenn eine Datei unter `assets/mappe/` vom letzten Commit abweicht und keine Anfrage sie deckt. Gedeckt ist sie, solange eine Anfrage offen ist, oder wenn eine abgeschlossene Anfrage genau diesen Stand der Datei festgehalten hat. Wer ohne Anfrage ändert, bekommt die Meldung beim nächsten Schreiben oder beim Commit.

Eine Sperre ohne Lebenszeichen des Editors gilt nach einiger Zeit als verwaist; `status` zeigt das, und der nächste `next` übernimmt sie samt der angefangenen Anfrage.

### Wer einen Pin bekommt (Weiterleiter)

Ein Auftrag mit einem Block `<tencil-context>` ist ein Pin. Der Agent in diesem Thread ändert nichts, auch nicht bei einer Kleinigkeit und auch nicht, wenn der Pin nur einen Text oder ein Profilfeld betrifft.

1. Einreihen, pro Pin eine Anfrage, bei einem Batch in der Reihenfolge der Pins:

   ```bash
   python3 tools/pin_queue.py enqueue --from "<eigener Thread>" --context "<Kontextzeile des Pins>" --text "<Wunsch des Nutzers, wörtlich>"
   ```

2. Die Ausgabe nennt die Sperre.
   - **„Sperre: belegt von …“:** Es gibt einen Editor. In T3 Code ihm die Datei der Anfrage mit `t3_thread_send` nennen, wenn sein Name eine Thread-Id ist (`t3:<thread-id>`). Dann am Pin „eingereiht“ mit der Kennung der Anfrage melden und aufhören.
   - **„Sperre: frei“ in T3 Code:** den Editor-Thread wecken oder starten. Gibt es im Projekt einen Thread mit dem Titel „Pin-Editor“ (`t3_thread_list`), bekommt er die Nachricht „Neue Pin-Anfragen, bitte die Warteschlange abarbeiten“ (`t3_thread_send`). Sonst `t3_thread_launch` mit dem Titel „Pin-Editor“ und dem Auftrag „Du bist der Editor der Pin-Warteschlange. Lies `.agents/skills/bewerbungshelfer/references/tencil.md`, Abschnitt Editor, und arbeite die Warteschlange ab.“ Dann „eingereiht“ melden und aufhören.
   - **„Sperre: frei“ ohne T3 Code** (Claude Code, Codex, anderes Harness): selbst Editor werden, weiter im Abschnitt Editor.
3. Meldet der Editor später das Ergebnis in diesen Thread, gibt der Agent es unverändert als Antwort am Pin weiter.

Der Editor-Thread läuft mit Claude Sonnet 5.5 (`claudeAgent/claude-sonnet-5-5`, Entscheidung des Nutzers vom 2026-11-15): beim `t3_thread_launch` das Modell ausdrücklich setzen. Pin-Threads, die nur einreihen, bleiben beim Modell aus der Projekteinstellung (Abschnitt Modell für Pins). Ohne T3 Code übernimmt der Agent die Rolle mit dem Modell, mit dem er läuft.

### Editor

1. Sperre nehmen und die erste Anfrage holen. Der Name ist in T3 Code `t3:<eigene Thread-Id>`, sonst die Kennung der eigenen Anfrage:

   ```bash
   python3 tools/pin_queue.py next --holder "<name>"
   ```

   Exit-Code 3: Ein anderer ist Editor. Nichts bearbeiten, „eingereiht“ melden, aufhören.
2. Die Anfrage bearbeiten, in dieser Reihenfolge: Quelle wählen, ändern, Doku anpassen, neu bauen und prüfen (die drei folgenden Abschnitte). Dauert das lange, zwischendurch `next` aufrufen; das hält die Sperre.
3. Abschließen. `--result` nennt die geänderten Quelldateien und die Regel, die jetzt gilt:

   ```bash
   python3 tools/pin_queue.py done "<kennung>" --holder "<name>" --result "…"
   ```

   Lehnt der Befehl ab, die gemeldeten Befunde beheben und ihn wiederholen.
4. Den Pin beantworten: Ergebnis und geänderte Dateien mit Zeile. Kam die Anfrage aus einem anderen Thread (Feld `from`), geht die Antwort in T3 Code mit `t3_thread_send` dorthin.
5. Wieder `next`, bis Exit-Code 2 kommt. Dann ist die Warteschlange leer und die Sperre frei.

Berührt eine Anfrage dieselbe Stelle wie eine frühere, gilt die spätere; die Doku beschreibt nur den neuen Stand. Widerspricht eine Anfrage einer Regel aus `CLAUDE.md` oder braucht sie eine Entscheidung des Nutzers, schließt der Editor sie ohne Änderung ab und nennt in `--result` die Frage.

## Quelle wählen

<!-- rule: pins.source -->
Master-Vorlage, Profilvorlage und Bewerbung sind Bauergebnisse (Regel `hard.generated` in `CLAUDE.md`). Die Änderung gehört in die Quelle, und der Pin nennt sie. Der Server löst die Attribute `data-part` und `data-origin` der gebauten Datei (`references/template.md`, Attribute für Pins) zu Datei und Zeile auf. Die Kontextzeile sieht so aus:

`p.contact-item [Aussehen .agents/skills/bewerbungshelfer/assets/mappe/partials/cover.html:27 · Inhalt profile:person.phone] (profile/<name>/assets/profile/<name>_profile.json:16:1)`

- In Klammern am Ende steht die Quelle des **Inhalts** (`data-origin`), aufgelöst zu Datei und Zeile. Hat das Element keinen Inhalt aus Daten, steht dort das Partial.
- „Aussehen“ nennt das Partial und die Zeile, die das Element zeichnet (`data-part`).

Der Editor entscheidet eines: Aussehen oder Inhalt?

- **Aussehen** (Abstand, Größe, Farbe, Schrift, Anordnung, Symbol) → `data-part`: das genannte Partial und sein Block in `assets/mappe/mappe.css`; Werte, die mehrfach gelten, in `tokens.css`; Bildschirmverhalten in `screen.css`; Zahlen, die das Skript liest, in `assets/mappe/limits.json`. Eine Änderung am Aussehen gilt für alle Mappen. Braucht das Partial einen neuen Schlüssel, zusätzlich die `…_view`-Funktion in `tools/build_mappe.py` und `assets/mappe/master.json`.
- **Inhalt** (Wortlaut, Daten, Reihenfolge, Sichtbarkeit) → `data-origin`:
  - `profile:…` → `<name>_profile.json` und `<name>_profile.md`; ist es eine neue wiederkehrende Entscheidung, ein Profilfeld (Schema, `references/profile-schema.md`) und eine Interviewfrage (`references/interview.md`)
  - `job:…` → `job_information/job.json` der Stelle, nur mit Beleg aus der Anzeige
  - `text:…` → `text_generation/*.md` der Stelle (E-Mail: `application/email.md`)
  - `master:…` → Platzhaltertext in `assets/mappe/master.json`
  - `build:…` → berechnete Angabe; die Regel steht in `tools/build_mappe.py`
- Fehlt für die Änderung ein Mechanismus, eine Regel oder ein Feld im Skill, zuerst dort ergänzen (Referenz, Schema, Build-Skript), nicht nur in dieser einen Mappe.

## Doku im selben Durchgang

<!-- rule: pins.docs-same-pass -->
Eine Änderung, die nur in CSS oder Profil steht, gilt als nicht reproduzierbar. Vor `done` stimmt die Doku:

- Jede Regel hat genau ein Zuhause, markiert mit `<!-- rule: <id> -->`. Dort wird sie geändert; andere Dateien verweisen mit „Regel `<id>` in `<datei>`“ und wiederholen sie nicht. Die Liste gibt `python3 tools/check_repo.py rules` aus.
- Eine Zahl, die das Build-Skript liest, steht in `assets/mappe/limits.json`. Die Doku nennt den Schlüssel als `limits:<pfad>`; steht eine Zahl direkt davor, vergleicht die Prüfung sie mit der Datei.
- Sichtbare Änderungen am Aussehen stehen in `references/template.md`, Prüfungen in `references/qa-and-export.md`, Regeln für Texte in `references/writing.md`.
- Die Doku beschreibt nur den heutigen Stand. Was sich geändert hat, bekommt eine Zeile in `CHANGELOG.md`.
- `python3 tools/check_repo.py docs` prüft Regel-Ids, Pfade, Befehle, Schemafelder, Symbol-Ids, Zahlen und veraltete Formulierungen (`references/qa-and-export.md`, Repository-Prüfung). Ersetzt eine Änderung eine Formulierung, die nicht wiederkehren darf, kommt sie in `tools/stale-terms.txt`.

## Neu bauen und prüfen

<!-- rule: pins.rebuild -->
In dieser Reihenfolge:

1. nach jeder Änderung unter `assets/mappe/`: `python3 tools/build_mappe.py master`
2. `python3 tools/build_mappe.py profile-template profile/<name> --qa=fast`
3. `python3 tools/build_mappe.py application <stelle> --qa=fast` für jede betroffene Stelle (kein `--pdf`, kein Statuswechsel). Eine freigegebene Mappe fällt dabei auf `draft` zurück; das melden.
4. Darf sich nur eine Stelle ändern: vorher `snapshot --save`, nachher `snapshot --compare` (`references/qa-and-export.md`, Seitenvergleich); die Ausgabe nennt jede Seite, die sich bewegt hat.
5. Zum Schluss einmal die volle Prüfung mit `--qa`.

Die Seite im Browser lädt nach dem Neubau von selbst neu.

## Grenzen

<!-- rule: pins.limits -->
- `data-tencil-src`, `data-tencil-component`, das `<script>` für `tencil.js` und das Live-Reload-Skript fügt der Server beim Ausliefern ein. Sie dürfen nie in ein Partial oder eine gebaute Datei geschrieben werden, weil die Mappe als PDF exportiert wird.
- Platzhalter in eckigen Klammern bleiben Platzhalter. In `assets/mappe/` und in allen Dateien außerhalb von `profile/` keine echten Namen, Kontaktdaten, Firmen oder Fotos einsetzen; keine externen Ressourcen einbinden.
- Gestaltungsregeln aus `references/template.md` (Designsystem) einhalten. Die Druckfassung (A4, `@media print`) darf nicht kaputtgehen.
- Keine weiteren Server starten, keine PDFs erzeugen, nichts committen.

## Ablauf für den Nutzer

1. Seite öffnen: lokal `http://127.0.0.1:8791/` (Übersicht, dort das Dokument wählen), von anderen Geräten `https://tencil.dnanu.de` (nur Master-Vorlage).
2. <kbd>C</kbd> drücken, Element anklicken, Änderung beschreiben, <kbd>Enter</kbd>.
3. Jeder Pin startet einen T3-Code-Thread in diesem Repository. Er reiht die Änderung ein; der Editor arbeitet die Pins nacheinander ab. Der Fortschritt erscheint am Pin, und die Seite lädt neu, sobald die angezeigte Datei neu gebaut ist.
4. Wenn das Ergebnis passt, löst der Nutzer den Pin auf.

Den Stand der Warteschlange zeigt `python3 tools/pin_queue.py status`.

## Dienste

Die Master-Vorlage `assets/bewerbungsmappe.html` enthält ausschließlich `[PLATZHALTER]` und keine personenbezogenen Daten; nur sie ist über die Fernadresse erreichbar. Der lokale Dienst (`127.0.0.1`) zeigt zusätzlich die gebauten Dateien des Nutzers: seine Profilvorlage (`profile/<name>/assets/profile/<name>_template.html`) und seine Bewerbungen (`profile/<name>/applications/**/application/bewerbungsmappe - <name>.html`). Diese Seiten enthalten persönliche Daten und werden nie über die Fernadresse, nie über einen Tunnel und nie an Dritte ausgeliefert.

| Unit (systemd, Nutzer) | Adresse | Zweck |
| --- | --- | --- |
| `tencil.service` | `127.0.0.1:4747` | Tencil-Daemon, von `npx tencil setup` verwaltet und mit anderen Projekten geteilt. Nicht von Hand ändern. |
| `mappe-template.service` | `http://127.0.0.1:8791/` | Übersicht mit Master-Vorlage, Profilvorlage und Bewerbungen (Seiten unter `/f/<Repo-Pfad>`, dazu nur Bilder unter `profile/<name>/`), Tencil-Overlay und Live-Reload, ohne Anmeldung |
| `mappe-template-remote.service` | `127.0.0.1:8792` → `https://tencil.dnanu.de` | Nur die Master-Vorlage mit Basic Auth. Liefert `/tencil.js` und `/ws` über dieselbe Origin aus. Einziges Ziel des Tunnels. |

```sh
systemctl --user status tencil mappe-template mappe-template-remote
systemctl --user restart mappe-template mappe-template-remote
journalctl --user -u mappe-template -u mappe-template-remote -u tencil -f
systemctl --user disable --now mappe-template-remote   # Fernzugriff abschalten
```

Server: `tools/serve_template.py`. Das Passwort für den Fernzugriff steht in `.tmp/tencil-auth/credentials` (Format `nutzer:passwort`, Modus 0600). Es gehört nicht in versionierte Dateien und wird nicht in Threads ausgegeben.

## Ersatzweg ohne Tencil

Wenn Tencil nicht verfügbar ist, `http://127.0.0.1:8791/` in der Vorschau von T3 Code öffnen, das Dokument wählen und das Element dort markieren. Die Annotation übergibt Selektor, HTML und Screenshot an den Agenten. Das HTML enthält `data-part` und `data-origin` des Elements oder eines Vorfahren; der Agent nennt beide in `--context` und reiht die Änderung wie einen Pin ein. Läuft der Daemon nicht, wird die Seite trotzdem angezeigt, nur ohne Overlay.

Wünscht der Nutzer eine Änderung an der Vorlage im Gespräch, ist der Ablauf derselbe: `enqueue` mit seinem Wunsch, dann als Editor weiter.

## Modell für Pins

Pins starten Threads mit dem Modell aus der Projekteinstellung des Daemons, nicht aus dem globalen `--model`. Datei: `~/.config/tencil/projects/bewerbungs-helfer-<hash>.settings.json` (Hash = erste 10 Zeichen von SHA-256 des absoluten Repo-Pfads), Eintrag `"models": {"t3code": "claudeAgent/claude-haiku-5-5"}` (Aufwand: Standard des Modells, medium). Danach `systemctl --user restart tencil`. Andere Projekte desselben Daemons bleiben unberührt.

## Störungen

- **Daemon startet nach dem Booten nicht** (`EADDRNOTAVAIL` auf der Tailscale-Adresse): Der Dienst startet vor Tailscale und gibt nach fünf Fehlversuchen auf. Abhilfe ist ein Drop-in `~/.config/systemd/user/tencil.service.d/retry.conf` mit `[Unit] StartLimitIntervalSec=0` und `[Service] RestartSec=5`, danach `systemctl --user daemon-reload`.
- **Tencil unverändert verwenden.** Das installierte Paket unter `~/.config/tencil/runtime/node_modules/tencil/dist/` nicht patchen. Meldet ein Pin „Ein Batch darf nicht Vorlage und Unternehmensmappen mischen“, stammt das von einem alten lokalen Patch für die frühere Ordnerstruktur. Dann das Paket neu installieren (`npm install` im Runtime-Ordner) oder die Originaldatei zurückspielen und `systemctl --user restart tencil`.
- **Eine Anfrage bleibt liegen:** `python3 tools/pin_queue.py status` zeigt offene Anfragen und die Sperre. Ist kein Editor mehr da, übernimmt der nächste Agent mit `next`.
