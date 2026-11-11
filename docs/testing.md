# Prüfung

## Repository

- keine Profil-, Job- oder Bewerbungsdaten im Git
- `profile/` und `applications/` sind gitignoriert
- Skill-Validator läuft erfolgreich
- Skill ist unter `~/.agents/skills/bewerbungshelfer` verlinkt
- alle Dokumentationslinks funktionieren

## HTML-Vorlage

Die leere Vorlage unter `.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html` enthält Platzhalter. Sie wird erst im lokalen Bewerbungsordner ausgefüllt.

Eine ausgefüllte Mappe wird geprüft:

- sechs A4-Seiten
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
