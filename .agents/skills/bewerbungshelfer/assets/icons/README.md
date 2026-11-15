# Technologie-Logos der Mappe

Die Logos stehen in Markenfarbe als `<symbol>` in `assets/mappe/icons.svg` (Ids `dv-…` und `si-…`, ein Symbol pro Zeile). Der Bau bettet in jede Mappe nur die Symbole ein, die sie verwendet. Zur Laufzeit gibt es keinen Abruf (kein CDN). Dieser Ordner hält Quellen, Lizenzen und den Weg, ein Logo aufzunehmen. Ein Logo im Vorrat sagt nichts über den Bewerber: Was in einer Mappe erscheint, steht allein im Profil.

## Quellen und Lizenzen

| Präfix | Quelle | Version | Lizenz | Hinweis |
|---|---|---|---|---|
| `dv-` | Devicon, https://devicon.dev, npm-Paket `devicon` | 2.17.0 | MIT, Copyright (c) 2015 konpa (`LICENSES.md`) | Vorrang, weil dort die meisten Logos liegen |
| `si-` | Simple Icons, https://simpleicons.org, npm-Paket `simple-icons` | 15.0.0 | CC0 1.0 (gemeinfrei) | nur, wo Devicon kein brauchbares Logo hat (nginx, Proxmox: bei Devicon nur Schriftzüge; OpenWrt, LXC: bei Devicon nicht vorhanden) |

Die Marken gehören ihren Inhabern. Die Logos stehen nur neben dem Namen der Technik und behaupten keine Zugehörigkeit. Der Lizenzhinweis steht zusätzlich im Kommentar von `assets/mappe/icons.svg` und, kurz, im Kopf jeder gebauten Datei (`assets/mappe/partials/document.html`).

## Quelldatei und Farbe je Symbol

<!-- rule: icons.sources -->
`assets/icons/sources.json` nennt für jedes Logo-Symbol die Quelldatei und die Farbe; `tools/devicon_symbols.py` liest die Datei, und `tools/check_repo.py docs` vergleicht sie mit `assets/mappe/icons.svg`. Mit diesen Quellen und dem Werkzeug entstehen die Symbole in der Vorlage Byte für Byte neu.

- `packages`: npm-Paket, Version und Pfadmuster je Präfix. Devicon: `icons/<name>/<name>-<variant>.svg`, Simple Icons: `icons/<name>.svg`.
- `symbols.<id>.variant` (nur Devicon): `original` oder `plain`.
- `symbols.<id>.fill`:
  - `"file"`: Die Füllfarben der Quelldatei bleiben. Das ist der Regelfall für Devicon: das mehrfarbige `original`, wenn es aus flachen Farben besteht, sonst `plain` mit der Markenfarbe der Datei.
  - `"#rrggbb"`: Das ganze Logo bekommt diese eine Farbe. Für Simple Icons (die Dateien haben keine Farbe; der Wert ist `hex` aus `data/simple-icons.json` desselben Pakets) und für Devicon-Dateien ohne eigene Farbe (Farbe aus der Datei devicon.json desselben Pakets).

Wahl der Variante, in dieser Reihenfolge:

1. Devicon `original`, wenn die Datei nur flache Füllfarben hat und bei 3,1 mm Höhe erkennbar bleibt.
2. Devicon `plain`, wenn das Original Verläufe hat (Flutter, Linux, Node.js, Python), zu kleinteilig ist (Docker, Podman) oder Attribute trägt, die das Werkzeug ablehnt (TypeScript).
3. Simple Icons mit der Markenfarbe, wenn Devicon nichts Brauchbares hat.
4. Ist die Markenfarbe auf dem hellen Chip zu blass, die Farbe von Simple Icons nehmen und in `note` begründen (Python: Blau statt Gelb).

Die Chips bleiben hell und der Name dunkel; im Graustufendruck trägt der Name die Information. Linien-Icons (`i-…`) sind keine Logos und bleiben einfarbig.

Die Id-Liste mit Verwendungszweck: Regel `icons.list` in `references/template.md`.

## Zuordnung Begriff → Symbol

<!-- rule: icons.mapping -->
Welcher Chip welches Symbol bekommt, steht hier, damit ein frischer Durchlauf dieselben Symbole wählt. Gilt für `skills.groups[].items[].chips[]` im Profil (`references/profile-schema.md`, Fähigkeiten).

| Begriff (Chip-Name) | Feld im Chip | Symbol | Hinweis |
|---|---|---|---|
| Cisco Packet Tracer | `logo` | `si-cisco` | Simple Icons |
| Wireshark | `logo` | `si-wireshark` | Simple Icons |
| Cisco IOS CLI | `icon` | `i-router` | Linien-Icon, kein Cisco-Logo in der Zeile |
| SSH | `icon` | `i-terminal` | Linien-Icon, kein freies Logo |
| TCP/IP | `icon` | `i-waypoints` | Linien-Icon |
| WAN/LAN | `icon` | `i-cable` | Linien-Icon |
| VLAN | `icon` | `i-layers` | Linien-Icon |
| Firewall | `icon` | `i-shield` | Linien-Icon |
| Ethernet-Verkabelung | `icon` | `i-ethernet` | Linien-Icon (Netzwerkbuchse) |
| PC-Montage | `icon` | `i-cpu` | Linien-Icon |
| Hardware-Reparatur | `icon` | `i-wrench` | Linien-Icon |
| Git | `logo` | `dv-git` | Devicon |
| GitHub | `logo` | `dv-github` | Devicon |
| GitLab | `logo` | `dv-gitlab` | Devicon |
| Jenkins | `logo` | `dv-jenkins` | Devicon |
| Jujutsu | `icon` | `i-branch` | Linien-Icon; weder Devicon noch Simple Icons haben in den festgelegten Versionen ein Logo |
| LXC (Proxmox) | `logo` | `si-linuxcontainers` | Simple Icons (Linux Containers); das Proxmox-Logo steht für Proxmox VE selbst |
| NixOS-Container | `logo` | `dv-nixos` | Devicon |
| OpenWRT | `logo` | `si-openwrt` | Simple Icons |
| Raspberry Pi OS | `logo` | `dv-raspberrypi` | Devicon |
| NixOS/Nix | `logo` | `dv-nixos` | Devicon |
| Dockform | `logo` | `dv-docker` | kein eigenes Logo verfügbar; Docker-Logo als Zeichen für das Docker-Ökosystem |
| Kubernetes | `logo` | `dv-kubernetes` | Devicon |
| Ansible | `logo` | `dv-ansible` | Devicon |

Ein Begriff, der hier fehlt: Logo aus der Liste in `references/template.md` wählen, sonst Linien-Icon oder Text-Chip; danach diese Tabelle ergänzen.

## Neues Logo aufnehmen

Das ist eine Designänderung an der Vorlage (`references/tencil.md`).

1. Variante und Farbe nach Regel `icons.sources` wählen und das Symbol in `assets/icons/sources.json` eintragen. Gibt es kein Logo, bleibt es bei einem Linien-Icon oder Text-Chip.
2. Quelldateien in einen leeren Ordner laden. Das Werkzeug gibt die Befehle aus den Einträgen aus (es lädt selbst nichts):

   ```bash
   mkdir -p .tmp/icons/dv .tmp/icons/si
   python3 tools/devicon_symbols.py .tmp/icons/dv --prefix dv --urls
   python3 tools/devicon_symbols.py .tmp/icons/si --prefix si --urls
   ```

   Die Ausgabe sind `curl`-Zeilen auf jsDelivr mit den festen Versionen; mit `--only <name>` nur für ein Symbol. An die Adresse gehen nur Paketname, Version und Dateiname.
3. Umwandeln: `python3 tools/devicon_symbols.py .tmp/icons/dv --prefix dv` bzw. `… .tmp/icons/si --prefix si`. Das Werkzeug prüft jede Datei einzeln und meldet Fehler mit Dateinamen auf stderr (Exit-Code 1); gültige Dateien erscheinen trotzdem auf stdout, defekte nie:
   - gültiges XML ohne DOCTYPE/ENTITY, Wurzel `<svg>` im SVG-Namensraum, `viewBox` mit vier Zahlen und Breite/Höhe > 0
   - Dateiname (ohne `.svg`) nur `a-z`, `0-9` und einzelne Bindestriche, weil er die Symbol-Id bildet (`dv-<name>`, `si-<name>`); sonst Datei umbenennen
   - ein Eintrag für die Id in `sources.json`; ohne ihn wird die Datei abgelehnt
   - nur `svg`, `g`, `path`, `circle`, `ellipse`, `rect`, `polygon`, `polyline`, `line` (dazu `title`, `desc`, `defs`, die entfallen); nie `script`, `style`, `foreignObject`, `use`, `image`, `a`, Filter, Animationen, Text
   - nur bekannte Attribute; keine Ereignis-Attribute, keine `href`/`xlink:href`, kein `url(…)` (damit auch keine Verläufe), kein `data:`/`http(s):`
   - Farben: Bei `fill: "file"` bleiben die Füllfarben, und jede Form braucht eine (an sich oder an einer Gruppe darüber). Bei einer Farbe `#rrggbb` entfallen die Füllfarben der Datei, das Logo steht in einer Gruppe mit dieser Farbe. Weiß wird in beiden Fällen zur Aussparung in der Farbe des Chips (`--dv-cutout`); das gilt auch für `fill` im `style`-Attribut. Im `style`-Attribut sind nur `fill`, `fill-rule`, `clip-rule`, `opacity`, `fill-opacity` erlaubt; `stroke` nur `none`/`currentColor` (Strichfarben gehen sonst verloren: anderes Logo wählen)
   - das fertige Symbol wird erneut als XML gelesen und gegen dieselben Regeln geprüft
   Probe auf Reproduzierbarkeit: Die 39 Quelldateien aus `sources.json` laden (Devicon 2.17.0, Simple Icons 15.0.0) und umwandeln; die Ausgabe muss mit den `dv-…`- und `si-…`-Zeilen in `assets/mappe/icons.svg` Byte für Byte übereinstimmen.
4. Die Zeilen alphabetisch in `assets/mappe/icons.svg` einfügen (eine Zeile pro Symbol), die Tabellen in `references/template.md` und diese Datei ergänzen, im Profil `chips[].logo` setzen, `build_mappe.py master` ausführen, neu bauen und die Chips ansehen, farbig und in Graustufen (Chip-Höhe 3,1 mm: feine Logos müssen lesbar bleiben).
5. Das Schema (`profile.schema.json`, `$defs/chip`) erlaubt `dv-…` und `si-…`; ein neues Präfix braucht eine Schemaänderung und einen Eintrag unter `packages`.

## Neues Linien-Icon aufnehmen

Linien-Icons (`i-…`) kommen aus Lucide (npm-Paket `lucide-static`, Version 0.469.0, ISC; Lizenz in `LICENSES.md`): die Formen aus `icons/<name>.svg` unverändert als `<symbol id="i-<kurzname>" viewBox="0 0 24 24">…</symbol>` in den oberen Block von `assets/mappe/icons.svg` setzen, ohne `fill`, `stroke` und `class` (Strich und Farbe setzt `.icon` im CSS), dann die Liste in `references/template.md` und die Hinweise in `LICENSES.md`, `icons.svg` und `partials/document.html` nachtragen. `i-ethernet` ist `ethernet-port`.
