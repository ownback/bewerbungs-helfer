# Lokales Profil

Hier entstehen beim ersten Durchlauf:

- `master-profile.json` – das bestätigte Master-Profil, primäre Quelle, validiert gegen `.agents/skills/bewerbungshelfer/assets/schemas/profile.schema.json`
- `master-profile.md` – lesbare Zusammenfassung für die gemeinsame Prüfung
- `import/` – optional vom Nutzer bereitgestellte Lebensläufe, Zeugnisse und Zertifikate
- `assets/` – lokale Bild- und Dokumentdateien

Der gesamte Inhalt ist gitignoriert; nur diese Datei und leere `.gitkeep`-Platzhalter für `import/` und `assets/` sind versioniert. Das Repository startet ohne Profil-, Job- oder Bewerbungsdaten.
