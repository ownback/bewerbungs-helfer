# Jobsuche und Stellenerfassung

## Suche

Öffne die Bundesagentur-Jobsuche im Browser. Wähle **Ausbildung**. Nutze aus dem Master-Profil ausschließlich:

- Suchbegriff (`goal.apprenticeship` oder eine Alternative)
- Ort oder PLZ (`goal.locations`, keine Straße)
- Umkreis (`goal.radius_km`)

Name, Kontaktdaten, Geburtsdaten, Lebenslauf und Nachweise werden nie in die Suche eingegeben.

Zeige höchstens zehn Treffer. Der Nutzer wählt genau eine Stelle. Öffne die Detailansicht und lies die vollständige Beschreibung. Die Anzeige im Browser des Harness lesen und den Originaltext übernehmen. Werkzeuge, die Seiten nur zusammenfassen (z. B. WebFetch), liefern keinen wörtlichen Beleg; `evidence` und `company_facts.evidence` müssen wörtlich sein.

## `job.json`

Das Schema steht unter `assets/schemas/job.schema.json`.

### Quelle und Stelle

- Bundesagentur-URL
- Abrufdatum
- Titel
- Unternehmen
- Ausbildungsberuf
- alle Standorte
- Beginn
- Dauer
- Frist
- vollständige Beschreibung
- Benefits

### Anforderungen

Jede Anforderung enthält:

- wörtlichen Beleg aus der Anzeige
- Bewertung gegen das Profil
- Profilbeleg

Bewertungen:

- `met`
- `partial`
- `not_met`
- `unknown`

### Unternehmen

Unternehmensbezogene Aussagen für die Briefe werden zusätzlich gespeichert:

- Aussage
- wörtlicher Beleg
- Quell-URL
- Abrufdatum

Keine Kultur- oder Kundenversprechen ohne Quelle. `company_facts` braucht mindestens einen Eintrag; Anschreiben und Motivationsschreiben verwenden nur Unternehmensaussagen, die dort stehen. `used_in` hält fest, in welchem Brief eine Aussage verwendet wird.

### Kontakt

Getrennt erfassen:

- Unternehmen
- Ansprechpartner
- Rolle oder Funktion
- Abteilung
- Straße
- PLZ
- Ort
- Telefon
- E-Mail
- Quell-URL
- Vertrauensgrad

Regeln:

- Name und Rolle nur übernehmen, wenn sie belegt sind.
- Allgemeine Bewerbungsadresse unter `application.email`, nicht als persönlicher Kontakt.
- Telefonnummer nur übernehmen, wenn öffentlich und eindeutig zugeordnet.
- `confidence: "verified"` nur mit Name und Quell-URL; `partial` nur mit Quell-URL.
- Bei Unsicherheit `confidence: "unknown"` und offenen Punkt ergänzen.
- Die verwendete Anrede steht in `contact.salutation`.
- Wenn kein persönlicher Kontakt belegt ist, nutze „Sehr geehrte Damen und Herren“ und dokumentiere das in `contact-summary.md`.
- Keine Kontaktdaten von einem ähnlichen Unternehmen übernehmen.

### Offene Punkte

Jeder offene Punkt enthält eine Auswirkung:

- `blocking`: Der Workflow stoppt.
- `non_blocking`: Die Ausgabe kann weitergehen.
- `research_needed`: Der Agent recherchiert zuerst öffentlich.

## Fristen

Nur ein ausdrücklich genanntes Datum übernehmen. Keine Frist aus dem Beginn ableiten.
