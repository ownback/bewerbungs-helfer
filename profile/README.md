# Lokale Profile

Alles in diesem Ordner außer dieser Datei und den `.gitkeep`-Platzhaltern ist gitignoriert.

```text
profile/
  import/                          neue Unterlagen hier ablegen (alter Lebenslauf, Zeugnisse, Foto, Unterschrift)
  assets/                          frei für gemeinsame, nicht personenbezogene Dateien (derzeit leer)
  privacy-needles.txt              optional: weitere Suchtexte für tools/check_repo.py privacy, einer pro Zeile
  <vorname.nachname>/
    assets/
      documents/                   Zeugnisse und Zertifikate (<name>_….png)
        old/                       alter Lebenslauf (PDF/DOCX) und extracted_information.md
      photos/cv/                   Bewerbungsfoto
      photos/project/              Projektfotos
      signature/                   Unterschrift
      profile/
        <name>_profile.json        Profil (Schema: assets/schemas/profile.schema.json im Skill)
        <name>_profile.md          lesbare Fassung
        <name>_motivation.md       Mastertext des Motivationsschreibens (einmal geschrieben, von dir freigegeben)
        <name>_template.html       Profilvorlage (gebaut, nicht von Hand bearbeiten)
        <name>_template.pdf        A4-Vorschau der Profilvorlage
    applications/
      ledger.json                  alle erfassten Stellen mit Status (abgeleitet: build_mappe.py ledger sync)
      apprenticeships|jobs|internships/<beruf>/<suchort>/<NN>-<ort>-<firma>/
        job_information/           ba_scrape.md, job.json, firma.md (Fakten zur Firma mit Beleg)
        text_generation/           anschreiben.md, motivationsschreiben.md, kontaktdaten.md
        application/               bewerbungsmappe - <name>.html/.pdf, email.md, application-manifest.json, assets/
      sent/apprenticeships|jobs|internships/…   gesendete Bewerbungen
      dropped/apprenticeships|jobs|internships/…   aussortierte Stellen, je mit DROPPED.txt (Grund, Datum)
```

Details: `.agents/skills/bewerbungshelfer/references/applications.md` und `references/profile-schema.md`.
