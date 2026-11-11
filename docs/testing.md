# Prüfung

## Repository

- keine Profil-, Job- oder Bewerbungsdaten im Git
- `profile/` und `applications/` sind gitignoriert
- alle JSON-Dateien im Skill sind gültiges JSON: `python3 -m json.tool <datei>`
- die drei Schemas sind gültige JSON-Schemas (Draft 2020-12), z. B. mit einem lokal installierten `jsonschema`-Paket: `python3 -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('<schema>')))"`
- `git ls-files` enthält nichts unter `profile/` außer `README.md` und `.gitkeep`, nichts unter `applications/` oder `workspace/`
- optional, je nach Harness: Skill ist unter `~/.agents/skills/bewerbungshelfer` verlinkt
- alle Dokumentationslinks funktionieren

## HTML-Vorlage

Die leere Vorlage unter `.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html` enthält Platzhalter. Sie wird erst im lokalen Bewerbungsordner ausgefüllt.

Eine ausgefüllte Mappe wird geprüft:

- sechs Abschnitte; sechs A4-Seiten im Regelfall, Folgeseiten nur für weitere Nachweise oder Lebenslauf-Fortsetzung
- keine Seite mit Überlauf (Prüfung siehe `references/qa-and-export.md`)
- `profile/master-profile.json`, `job.json` und `application-manifest.json` gegen ihre Schemas validiert
- Reihenfolge: Deckblatt, Anschreiben, Lebenslauf, Motivationsschreiben, Zertifikate, Zeugnisse
- kein Platzhalter mehr vorhanden
- echte Nachweise sichtbar oder ausdrücklich fehlend
- keine externen Ressourcen
- HTML und Stencil zeigen denselben Stand, wenn Stencil verwendet wurde
- Desktop bei 1440 × 900 oder 1280 × 800 geprüft
- Mobil bei 390 × 844 und 375 × 812 geprüft
- A4/PDF separat bei 210 × 297 mm geprüft

## Echter Durchlauf

1. frischen Clone öffnen
2. Skill starten
3. Profilinterview ausfüllen
4. genau eine Ausbildungsstelle auswählen
5. HTML im Browser prüfen
6. ausdrücklich freigeben
7. PDF über den Browser exportieren
8. Kontaktübersicht und E-Mail-Entwurf prüfen
9. bestätigen, dass nichts gesendet wurde
