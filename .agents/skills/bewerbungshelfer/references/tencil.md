# Visuelle Prüfung der Mappe (Tencil)

Die Basisvorlage `.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html` enthält ausschließlich
`[PLATZHALTER]` und keine personenbezogenen Daten; nur sie ist über die Fernadresse erreichbar.
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
   am Pin, und die Seite lädt nach jeder Änderung an der Vorlage neu.
4. Wenn das Ergebnis passt, löst der Nutzer den Pin auf.

## Regeln für den Agenten im Pin-Thread

- Der Kontext nennt die Quelle, z. B.
  `div.cover-main (.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html:884:7)`.
  Zeile und Spalte beziehen sich auf die Datei, die der Nutzer gerade ansieht.
- **Master-Vorlage:** dort ändern, und nur in dieser Datei. Danach Profilvorlage und Mappen neu bauen.
- **Profilvorlage oder Bewerbung (gebaute Dateien):** die Datei selbst nie bearbeiten. Die Änderung gehört in die Quelle, damit sie
  reproduzierbar ist und jeder neue Bau sie enthält:
  - Aussehen, Abstände, Schrift, Farben, Symbole → Master-Vorlage; ändert sich das Markup (Klassen, Verschachtelung), zusätzlich `tools/build_mappe.py` und den Datenvertrag in `references/template.md`
  - Inhalt aus dem Profil (Texte, Einträge, Reihenfolge, Chips, Sichtbarkeit) → `<name>_profile.json` und `<name>_profile.md`; ist es eine neue wiederkehrende Entscheidung, ein Profilfeld (Schema, `references/profile-schema.md`) und eine Interviewfrage (`references/interview.md`)
  - Brieftexte und E-Mail → `text_generation/*.md` bzw. `application/email.md` der Stelle
  - Fehlt für die Änderung ein Mechanismus, Regel oder Feld im Skill, zuerst dort ergänzen (Skill, Referenz, Schema, Build-Skript), nicht nur in dieser einen Mappe
  - Danach in dieser Reihenfolge neu bauen und prüfen: `python3 tools/build_mappe.py profile-template profile/<name> --qa`, dann `application <stelle> --qa` für jede betroffene Stelle (kein `--pdf`, kein Statuswechsel). Eine freigegebene Mappe fällt dabei auf `draft` zurück; das melden.
  - Die Seite lädt nach dem Neubau von selbst neu. Am Ende nennen: welche Quelldateien geändert wurden und welche Regel jetzt gilt.
- `data-tencil-src`, `data-tencil-component`, das `<script>` für `tencil.js` und das
  Live-Reload-Skript fügt der Server beim Ausliefern ein. Sie dürfen nie in die Vorlage
  geschrieben werden, weil die Vorlage als PDF exportiert wird.
- Platzhalter in eckigen Klammern bleiben Platzhalter. In der Master-Vorlage und in allen Dateien außerhalb von
  `profile/` keine echten Namen, Kontaktdaten, Firmen oder Fotos einsetzen; keine externen Ressourcen einbinden.
- Gestaltungsregeln aus `SKILL.md` und dem Kopfkommentar der Vorlage einhalten. Die
  Druckfassung (A4, `@media print`) darf nicht kaputtgehen.
- Keine weiteren Server starten, keine PDFs erzeugen, nichts committen. Zum Schluss kurz
  melden, was in welcher Zeile geändert wurde.

## Ersatzweg ohne Tencil

Wenn Tencil nicht verfügbar ist, `http://127.0.0.1:8791/` in der Vorschau von T3 Code öffnen, das Dokument wählen
und das Element dort markieren. Die Annotation übergibt Selektor, HTML und Screenshot an den
Agenten. Der Agent sucht die Stelle per Selektor oder Text in der Vorlage und hält sich an
dieselben Regeln. Läuft der Daemon nicht, wird die Seite trotzdem angezeigt, nur ohne Overlay.
