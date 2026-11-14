# Visuelle Prüfung der Mappe (Tencil)

Die Master-Vorlage `.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html` enthält ausschließlich
`[PLATZHALTER]` und keine personenbezogenen Daten; nur sie ist über die Fernadresse erreichbar. Sie ist wie
jede Mappe ein Bauergebnis aus den Quellen unter `assets/mappe/` (`references/template.md`).
Der lokale Dienst (`127.0.0.1`) zeigt zusätzlich die gebauten Dateien des Nutzers: seine Profilvorlage
(`profile/<name>/assets/profile/<name>_template.html`) und seine Bewerbungen
(`profile/<name>/applications/**/application/bewerbungsmappe - <name>.html`). Diese Seiten enthalten
persönliche Daten und werden nie über die Fernadresse, nie über einen Tunnel und nie an Dritte ausgeliefert.

## Dienste

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

Server: `tools/serve_template.py`. Das Passwort für den Fernzugriff steht in
`.tmp/tencil-auth/credentials` (Format `nutzer:passwort`, Modus 0600). Es gehört nicht in
versionierte Dateien und wird nicht in Threads ausgegeben.

## Ablauf für den Nutzer

1. Seite öffnen: lokal `http://127.0.0.1:8791/` (Übersicht, dort das Dokument wählen), von anderen Geräten `https://tencil.dnanu.de` (nur Master-Vorlage).
2. <kbd>C</kbd> drücken, Element anklicken, Änderung beschreiben, <kbd>Enter</kbd>.
3. Jeder Pin startet einen T3-Code-Thread in diesem Repository. Der Fortschritt erscheint
   am Pin, und die Seite lädt neu, sobald die angezeigte Datei neu gebaut ist.
4. Wenn das Ergebnis passt, löst der Nutzer den Pin auf.

## Regeln für den Agenten im Pin-Thread

- **Alle drei Dokumente sind Bauergebnisse.** Master-Vorlage, Profilvorlage und Bewerbung werden nie direkt bearbeitet, auch `assets/bewerbungsmappe.html` nicht. Die Änderung gehört in die Quelle, damit jeder neue Bau sie enthält.
- **Der Pin nennt die Quelle.** Der Server löst die Attribute `data-part` und `data-origin` der gebauten Datei (`references/template.md`, Attribute für Pins) zu Datei und Zeile auf. Der Kontext sieht so aus:
  `p.contact-item [Aussehen .agents/skills/bewerbungshelfer/assets/mappe/partials/cover.html:27 · Inhalt profile:person.phone] (profile/<name>/assets/profile/<name>_profile.json:16:1)`
  - In Klammern am Ende steht die Quelle des **Inhalts** (`data-origin`), aufgelöst zu Datei und Zeile. Hat das Element keinen Inhalt aus Daten, steht dort das Partial.
  - „Aussehen“ nennt das Partial und die Zeile, die das Element zeichnet (`data-part`).
- **Eine Entscheidung trifft der Agent: Aussehen oder Inhalt?**
  - **Aussehen** (Abstand, Größe, Farbe, Schrift, Anordnung, Symbol) → `data-part`: das genannte Partial und sein Block in `assets/mappe/mappe.css`; Werte, die mehrfach gelten, in `tokens.css`; Bildschirmverhalten in `screen.css`. Eine Änderung am Aussehen gilt für alle Mappen. Braucht das Partial einen neuen Schlüssel, zusätzlich die `…_view`-Funktion in `tools/build_mappe.py` und `assets/mappe/master.json`.
  - **Inhalt** (Wortlaut, Daten, Reihenfolge, Sichtbarkeit) → `data-origin`:
    - `profile:…` → `<name>_profile.json` und `<name>_profile.md`; ist es eine neue wiederkehrende Entscheidung, ein Profilfeld (Schema, `references/profile-schema.md`) und eine Interviewfrage (`references/interview.md`)
    - `job:…` → `job_information/job.json` der Stelle, nur mit Beleg aus der Anzeige
    - `text:…` → `text_generation/*.md` der Stelle (E-Mail: `application/email.md`)
    - `master:…` → Platzhaltertext in `assets/mappe/master.json`
    - `build:…` → berechnete Angabe; die Regel steht in `tools/build_mappe.py`
  - Fehlt für die Änderung ein Mechanismus, eine Regel oder ein Feld im Skill, zuerst dort ergänzen (Skill, Referenz, Schema, Build-Skript), nicht nur in dieser einen Mappe.
- **Neu bauen und prüfen, in dieser Reihenfolge:**
  1. nach jeder Änderung unter `assets/mappe/`: `python3 tools/build_mappe.py master` (der Hook von `tools/check_repo.py` meldet eine Master-Vorlage, die nicht zu ihren Quellen passt)
  2. `python3 tools/build_mappe.py profile-template profile/<name> --qa=fast`
  3. `python3 tools/build_mappe.py application <stelle> --qa=fast` für jede betroffene Stelle (kein `--pdf`, kein Statuswechsel). Eine freigegebene Mappe fällt dabei auf `draft` zurück; das melden.
  4. Darf sich nur eine Stelle ändern: vorher `snapshot --save`, nachher `snapshot --compare` (`references/qa-and-export.md`); die Ausgabe nennt jede Seite, die sich bewegt hat.
  5. Zum Schluss einmal die volle Prüfung mit `--qa`.
  Die Seite lädt nach dem Neubau von selbst neu. Am Ende nennen: welche Quelldateien geändert wurden und welche Regel jetzt gilt.
- **Doku im selben Durchgang, auch bei kleinen Änderungen:** Jede sichtbare Änderung an den Quellen der Vorlage oder am Build-Skript steht danach in `references/template.md`. Betrifft sie eine Prüfung, auch in `references/qa-and-export.md`; ist es eine Regel für Texte, in `references/writing.md` und den Agentendateien unter `.claude/agents/`. Veraltete Aussagen ersetzen, nicht ergänzen: nach dem alten Wert suchen (z. B. alte Maße, „gleich breit“, alte Position) und jede Fundstelle angleichen. Eine Änderung, die nur in CSS oder Profil steht, gilt als nicht reproduzierbar.
- **Parallele Pin-Threads:** Jeder Pin oder Batch startet einen eigenen Thread im selben Arbeitsverzeichnis. Vor dem ersten Schreiben `git status` und `git diff` der betroffenen Dateien lesen; fremde, noch nicht committete Änderungen gehören anderen Threads und werden nie zurückgesetzt. Datei direkt vor jeder Änderung neu lesen. Berührt ein Pin dieselbe Stelle wie ein früherer, gilt der neuere Pin, und die Doku beschreibt nur den neuen Stand. In T3 Code die anderen Pin-Threads des Projekts mit `t3_thread_list` finden, mit `t3_thread_read` lesen und mit `t3_thread_send` abstimmen (wer welche Datei ändert, wer zum Schluss neu baut). Neu bauen und `--qa` laufen lassen erst, wenn kein anderer Pin-Thread mehr an Vorlage oder Build-Skript schreibt.
- `data-tencil-src`, `data-tencil-component`, das `<script>` für `tencil.js` und das
  Live-Reload-Skript fügt der Server beim Ausliefern ein. Sie dürfen nie in ein Partial oder eine
  gebaute Datei geschrieben werden, weil die Mappe als PDF exportiert wird.
- Platzhalter in eckigen Klammern bleiben Platzhalter. In `assets/mappe/` und in allen Dateien außerhalb von
  `profile/` keine echten Namen, Kontaktdaten, Firmen oder Fotos einsetzen; keine externen Ressourcen einbinden.
- Gestaltungsregeln aus `references/template.md` (Designsystem) einhalten. Die
  Druckfassung (A4, `@media print`) darf nicht kaputtgehen.
- Keine weiteren Server starten, keine PDFs erzeugen, nichts committen. Zum Schluss kurz
  melden, was in welcher Zeile geändert wurde.

## Ersatzweg ohne Tencil

Wenn Tencil nicht verfügbar ist, `http://127.0.0.1:8791/` in der Vorschau von T3 Code öffnen, das Dokument wählen
und das Element dort markieren. Die Annotation übergibt Selektor, HTML und Screenshot an den
Agenten. Das HTML enthält `data-part` und `data-origin` des Elements oder eines Vorfahren; der Agent
liest daraus Partial und Inhaltsquelle und hält sich an dieselben Regeln. Läuft der Daemon nicht, wird die Seite trotzdem angezeigt, nur ohne Overlay.

## Modell für Pins

Pins starten Threads mit dem Modell aus der Projekteinstellung des Daemons, nicht aus dem globalen `--model`. Datei: `~/.config/tencil/projects/bewerbungs-helfer-<hash>.settings.json` (Hash = erste 10 Zeichen von SHA-256 des absoluten Repo-Pfads), Eintrag `"models": {"t3code": "claudeAgent/claude-haiku-5-5"}` (Aufwand: Standard des Modells, medium). Danach `systemctl --user restart tencil`. Andere Projekte desselben Daemons bleiben unberührt.

## Störungen

- **Daemon startet nach dem Booten nicht** (`EADDRNOTAVAIL` auf der Tailscale-Adresse): Der Dienst startet vor Tailscale und gibt nach fünf Fehlversuchen auf. Abhilfe ist ein Drop-in `~/.config/systemd/user/tencil.service.d/retry.conf` mit `[Unit] StartLimitIntervalSec=0` und `[Service] RestartSec=5`, danach `systemctl --user daemon-reload`.
- **Tencil unverändert verwenden.** Das installierte Paket unter `~/.config/tencil/runtime/node_modules/tencil/dist/` nicht patchen. Meldet ein Pin „Ein Batch darf nicht Vorlage und Unternehmensmappen mischen“, stammt das von einem alten lokalen Patch für die frühere Ordnerstruktur. Dann das Paket neu installieren (`npm install` im Runtime-Ordner) oder die Originaldatei zurückspielen und `systemctl --user restart tencil`.
