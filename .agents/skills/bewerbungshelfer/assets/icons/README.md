# Technologie-Logos der Mappe

Die Logos stehen als einfarbige `<symbol>` in der SVG-Bibliothek von `assets/bewerbungsmappe.html` (Ids `dv-…` und `si-…`). Zur Laufzeit gibt es keinen Abruf (kein CDN). Dieser Ordner hält Quellen, Lizenzen und den Weg, ein Logo aufzunehmen. Ein Logo im Vorrat sagt nichts über den Bewerber: Was in einer Mappe erscheint, steht allein im Profil.

## Quellen und Lizenzen

| Präfix | Quelle | Version | Lizenz | Hinweis |
|---|---|---|---|---|
| `dv-` | Devicon, https://devicon.dev, npm-Paket `devicon` | 2.17.0 | MIT, Copyright (c) 2015 konpa (`LICENSES.md`) | Vorrang, weil dort die meisten Logos liegen |
| `si-` | Simple Icons, https://simpleicons.org, npm-Paket `simple-icons` | 15.0.0 | CC0 1.0 (gemeinfrei) | nur, wo Devicon kein brauchbares einfarbiges Logo hat (nginx, Proxmox: bei Devicon nur Schriftzüge) |

Die Marken gehören ihren Inhabern. Die Logos stehen nur neben dem Namen der Technik und behaupten keine Zugehörigkeit. Der Lizenzhinweis steht zusätzlich im Kommentar der SVG-Bibliothek der Vorlage.

## Zuordnung Symbol → Quelldatei

Devicon-Pfad: `icons/<name>/<name>-<variante>.svg`, Simple-Icons-Pfad: `icons/<name>.svg`. Mit diesen Quellen und `tools/devicon_symbols.py` entstehen die Symbole in der Vorlage Byte für Byte neu.

| Variante `plain` | Variante `original` | Simple Icons |
|---|---|---|
| android, ansible, archlinux, bash, cloudflare, css3, debian, docker, flutter, git, html5, javascript, kubernetes, linux, nixos, nodejs, podman, python, swift, typescript | apple, github, react, rust, windows11 | bluetooth, cisco, homeassistant, nextcloud, nginx, proxmox, tailscale, wireguard, wireshark |

Die Id-Liste mit Verwendungszweck steht in `references/template.md` (Abschnitt Icons und Logos).

## Zuordnung Begriff → Symbol

Welcher Chip welches Symbol bekommt, steht hier, damit ein frischer Durchlauf dieselben Symbole wählt. Gilt für `skills.groups[].items[].chips[]` im Profil (`references/profile-schema.md`, Fähigkeiten). Die Liste der Logo-Ids steht in `references/template.md`.

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
| Git | `logo` | `dv-git` | Devicon |
| GitHub | `logo` | `dv-github` | Devicon |
| NixOS/Nix | `logo` | `dv-nixos` | Devicon (plain) |
| Dockform | `logo` | `dv-docker` | kein eigenes Logo verfügbar; Docker-Logo als Zeichen für das Docker-Ökosystem |
| Kubernetes | `logo` | `dv-kubernetes` | Devicon |
| Ansible | `logo` | `dv-ansible` | Devicon |

Ein Begriff, der hier fehlt: Logo aus der Liste in `references/template.md` wählen, sonst Linien-Icon oder Text-Chip; danach diese Tabelle ergänzen.

## Neues Logo aufnehmen

Das ist eine Designänderung an der Vorlage (`references/tencil.md`).

1. Devicon zuerst prüfen: `plain`, sonst `original`. Wirkt das Logo einfarbig als Schriftzug oder zerfällt es, Simple Icons nehmen. Gibt es keines, bleibt es bei einem Linien-Icon oder Text-Chip.
2. SVG in einen leeren Ordner laden, z. B.:

   ```bash
   mkdir -p .tmp/icons/dv .tmp/icons/si
   curl -fLo .tmp/icons/dv/rust.svg https://cdn.jsdelivr.net/npm/devicon@2.17.0/icons/rust/rust-original.svg
   curl -fLo .tmp/icons/si/nginx.svg https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/nginx.svg
   ```

3. Umwandeln: `python3 tools/devicon_symbols.py .tmp/icons/dv --prefix dv` bzw. `… .tmp/icons/si --prefix si`. Das Werkzeug prüft jede Datei einzeln und meldet Fehler mit Dateinamen auf stderr (Exit-Code 1); gültige Dateien erscheinen trotzdem auf stdout, defekte nie:
   - gültiges XML ohne DOCTYPE/ENTITY, Wurzel `<svg>` im SVG-Namensraum, `viewBox` mit vier Zahlen und Breite/Höhe > 0
   - Dateiname (ohne `.svg`) nur `a-z`, `0-9` und einzelne Bindestriche, weil er die Symbol-Id bildet (`dv-<name>`, `si-<name>`); sonst Datei umbenennen
   - nur `svg`, `g`, `path`, `circle`, `ellipse`, `rect`, `polygon`, `polyline`, `line` (dazu `title`, `desc`, `defs`, die entfallen); nie `script`, `style`, `foreignObject`, `use`, `image`, `a`, Filter, Animationen, Text
   - nur bekannte Attribute; keine Ereignis-Attribute, keine `href`/`xlink:href`, kein `url(…)`, kein `data:`/`http(s):`
   - Füllfarben werden entfernt (erben `currentColor`), Weiß wird Aussparung; das gilt auch für `fill` im `style`-Attribut. Im `style`-Attribut sind nur `fill`, `fill-rule`, `clip-rule`, `opacity`, `fill-opacity` erlaubt; `stroke` nur `none`/`currentColor` (Strichfarben gehen sonst verloren: anderes Logo wählen)
   - das fertige Symbol wird erneut als XML gelesen und gegen dieselben Regeln geprüft
   Probe auf Reproduzierbarkeit: Die 34 Quelldateien aus der Tabelle oben laden (Devicon 2.17.0, Simple Icons 15.0.0) und umwandeln; die Ausgabe muss mit den `<symbol>`-Zeilen der SVG-Bibliothek in `assets/bewerbungsmappe.html` Byte für Byte übereinstimmen.
4. Die Zeilen alphabetisch in die SVG-Bibliothek der Vorlage einfügen, die Tabellen in `references/template.md` und diese Datei ergänzen, im Profil `chips[].logo` setzen, neu bauen und die Chips ansehen (Chip-Höhe 3,1 mm: feine Logos müssen lesbar bleiben).
5. Das Schema (`profile.schema.json`, `$defs/chip`) erlaubt `dv-…` und `si-…`; ein neues Präfix braucht eine Schemaänderung.
