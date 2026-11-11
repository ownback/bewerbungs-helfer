# Bundesagentur für Arbeit

## Rolle

Die Bundesagentur-Jobsuche ist die einzige Jobquelle der ersten Version. Der Agent arbeitet mit dem Browser des Harness auf der öffentlichen Website.

## Suche

- Suchbereich: **Ausbildung**
- Suchbegriff aus dem Master-Profil
- Ort oder PLZ aus dem Master-Profil (keine Straße)
- Umkreis aus dem Master-Profil
- Startzeitpunkt nur als Filter, wenn die Anzeige ihn zuverlässig angibt

Der Agent zeigt eine kurze Auswahl mit Titel, Unternehmen, Ort, Entfernung, Beginn und Link. Der Nutzer wählt genau eine Stelle.

## Stellenerfassung

Aus der Detailansicht werden übernommen:

- Titel
- Unternehmen
- Ausbildungsberuf
- vollständige Beschreibung
- Ort
- Beginn
- Dauer
- Frist
- Bewerbungsweg
- Ansprechpartner
- Rolle oder Abteilung
- E-Mail
- Telefon
- Quell-URL
- Abrufdatum

Die Daten werden in `job.json` nach `.agents/skills/bewerbungshelfer/assets/schemas/job.schema.json` festgehalten.

## Anforderungen

Jede Anforderung bekommt:

- den wörtlichen Beleg aus der Anzeige
- eine Bewertung gegen das Profil
- optional einen Profilbeleg

Bewertungen:

- `met`
- `partial`
- `not_met`
- `unknown`

Eine Anforderung ohne Profilbeleg ist `unknown`, nicht `met`.

## Kontakt

Die Anzeige hat Vorrang. Fehlt ein Ansprechpartner, sucht der Agent auf der öffentlichen Karriereseite oder einer anderen öffentlichen Unternehmensseite nach einem passenden Kontakt.

Ein persönlicher Ansprechpartner wird nur übernommen, wenn Name und Rolle belegt sind. Eine allgemeine Bewerbungsadresse ist kein persönlicher Kontakt.

Wenn kein verlässlicher persönlicher Kontakt gefunden wird:

- neutrale Anrede „Sehr geehrte Damen und Herren“
- `contact.confidence: "unknown"`
- offener Punkt in `job.json`
- Hinweis in `contact-summary.md`

## Grenzen

- Keine Massenabfragen
- Keine Umgehung von Anmeldung oder Bot-Schutz
- Keine Abhängigkeit von internen Endpunkten
- Außer Suchbegriff, Ort/PLZ und Umkreis keine Profildaten an die Jobsuche übertragen (kein Name, keine Kontaktdaten, keine Geburtsdaten, keine Dokumente)
- Keine zweite Jobquelle in der ersten Version

## Änderungen der Website

Wenn sich die Jobsuche ändert, passt der Agent seinen Browser-Workflow an. Es gibt keine versteckte Scraping-Abhängigkeit im Repository.
