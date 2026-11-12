# Lokale Profile

Alles in diesem Ordner außer dieser Datei und den `.gitkeep`-Platzhaltern ist gitignoriert.

```text
profile/
  import/                          neue Unterlagen hier ablegen (alter Lebenslauf, Zeugnisse, Foto, Unterschrift)
  assets/                          frei für gemeinsame, nicht personenbezogene Dateien (derzeit leer)
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
        <name>_template.html       Profilvorlage (gebaut, nicht von Hand bearbeiten)
        <name>_template.pdf        A4-Vorschau der Profilvorlage
    applications/
      ledger.json                  alle Bewerbungen mit Status
      apprenticeships|jobs|internships/<beruf>/<suchort>/<NN>-<ort>-<firma>/
        job_information/           ba_scrape.md, job.json
        text_generation/           anschreiben.md, motivationsschreiben.md, kontaktdaten.md
        application/               bewerbungsmappe - <name>.html/.pdf, email.md, application-manifest.json, assets/
      sent/apprenticeships|jobs|internships/…   gesendete Bewerbungen
```

Details: `.agents/skills/bewerbungshelfer/references/applications.md` und `references/profile-schema.md`.
