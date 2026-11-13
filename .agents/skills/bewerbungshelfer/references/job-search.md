# Jobsuche bei der Bundesagentur für Arbeit

Die BA-Jobsuche ist die einzige Jobquelle. Der **Hauptagent** arbeitet im Browser des Harness auf der öffentlichen Website: klicken, lesen, Text übernehmen. Keine Scraping-Skripte, keine internen Endpunkte, keine Umgehung von Anmeldung oder Captcha, keine Massenabfragen.

An die Suche gehen nur Beruf, Ort und Umkreis. Name, Kontaktdaten, Geburtsdaten, Lebenslauf und Nachweise werden nie eingegeben.

Werkzeuge, die Seiten nur zusammenfassen (z. B. WebFetch), liefern keinen wörtlichen Text. `ba_scrape.md`, `requirements[].evidence` und `company_facts[].evidence` müssen wörtlich sein, also aus dem Seiteninhalt im Browser kopiert.

Die Selektoren unten stammen von der Website im November 2026. Wenn sich die Seite ändert, passt der Agent seinen Weg an und meldet die Abweichung.

## 1. Zur Jobsuche

1. `https://www.arbeitsagentur.de/privatpersonen` öffnen.
2. Im Kopfbereich (`bahf-header`) „Suche“ wählen → Portalsuche `https://web.arbeitsagentur.de/portal/portalsuche/`.
3. Kachel „Jobsuche“ öffnen (Link auf `https://www.arbeitsagentur.de/jobsuche`). Direkt aufrufen ist ebenso erlaubt.

## 2. Suchbereich

- `#suchbereich-tabbar-item-0` „Jobs“ für Jobs
- `#suchbereich-tabbar-item-1` „Ausbildung“ für Ausbildungsplätze **und** Praktika

## 3. Suchfelder

- `#was-input`: Beruf, Ausbildung oder Praktikum, z. B. „Fachinformatiker Systemintegration“
- `#wo-input`: Zielort (Ort oder PLZ, keine Straße)
- `#umkreis-dropdown-button`: Umkreis; erst aktiv, wenn ein Ort eingetragen ist

Umkreis:

- Vorgabe des Nutzers (`goal.radius_km` oder Ansage im Gespräch) verwenden.
- Ohne Vorgabe: „ganzer Ort“ (`#umkreis-dropdown-item-0`).
- Keine Treffer: den Nutzer fragen, ob der Umkreis leicht vergrößert werden darf. Erst nach seinem Ja erweitern, schrittweise.

## 4. Trefferliste

Beispiel-URL: `/jobsuche/suche?suchbereich=ausbildung&was=…&wo=…&umkreis=25`

1. Sortieren: `#sortierung-dropdown-button` → `#sortierung-dropdown-item-1` „Neueste Veröffentlichung“.
2. Nur bei Ausbildung: Filter `#ausbildungsart-betriebliche-ausbildung-label` „Betriebliche Ausbildung“.
3. Treffer sind `#ergebnisliste-item-N` mit Link auf `/jobsuche/jobdetail/<referenznummer>`.

Dem Nutzer eine kurze Liste zeigen: Titel, Firma, Ort, Entfernung (falls angezeigt), Beginn, Veröffentlichung, Link. Höchstens etwa zehn Treffer auf einmal. Der Nutzer wählt eine oder mehrere Stellen.

Vor dem Erfassen jede gewählte Stelle gegen das Ledger prüfen (`references/applications.md`, Duplikate). Bei einem Treffer den Nutzer warnen und fragen, ob trotzdem weiter.

Bei vielen Treffern (mehrere Suchorte, Auswahl „alle“) vor dem Erfassen filtern und die Ausschlüsse dem Nutzer mit Grund zeigen:

- anderer Beruf oder andere Fachrichtung im Titel; Titel ohne Fachrichtung nur nach Rückfrage
- Beginn nicht im Zieljahr (`goal.start`), auch „ab sofort“
- geforderter Schulabschluss über dem Profil (z. B. Abitur/Fachhochschulreife bei Mittlerer Reife): nach Rückfrage ausschließen; Anzeigen, die im Text auch den eigenen Abschluss akzeptieren, bleiben
- Duplikat = gleiche Firma und gleicher Titel (auch mit anderer Referenznummer oder als Partner-Listing): die Fassung mit vollständigem BA-Text bzw. die beim Arbeitgeber noch offene behalten; unterschiedliche Schwerpunkte im Text sind keine Duplikate
- abgelaufene Bewerbungsfrist

Ausgeschlossene Stellen werden nicht gelöscht, sondern mit Grund festgehalten (z. B. `DROPPED.txt` im verschobenen Ordner unter `.tmp/`). Anzeigen ohne BA-Kontaktblock (nur Link zu Partnerseiten wie Studyflix, ausbildung.de, finest-jobs oder zur Karriereseite) bleiben in der Auswahl: Bewerbung dann über das Portal.

## 5. Rang und Ordner

Die gewählten Stellen nach Entfernung vom Suchort sortieren (01 = am nächsten). Entfernung aus der Trefferliste; fehlt sie, nach Arbeitsort schätzen und das in `job.json` (`search.distance_km: null`) offen lassen. Gleichstand: Reihenfolge der Trefferliste. Danach die Ordner anlegen (`references/applications.md`) und `search` in `job.json` füllen (Bereich, Suchbegriff, Ort, Umkreis, Sortierung, Filter, Ergebnis-URL, Rang, Entfernung).

## 6. Anzeige erfassen

Jede gewählte Stelle in einem **neuen Tab** öffnen und nacheinander erfassen, nicht parallel: das Captcha braucht den Nutzer.

### Kopfbereich

| Feld | Selektor | Ziel in `job.json` |
|---|---|---|
| Titel | `#detail-kopfbereich-titel` | `title` |
| Firma | `#detail-kopfbereich-firma` | `company` |
| Beginn | `#detail-kopfbereich-eintrittsdatum-mit-datum` | `start_text`, `start` (JJJJ-MM-TT, wenn eindeutig) |
| Veröffentlicht | `#detail-kopfbereich-veroeffentlichungsdatum` | `published.text` (sichtbar) und `published.date` (exaktes Datum aus dem `title`-Attribut) |
| Angebotsart | Kopfbereich | `offer_type` |
| Ort | `#detail-kopfbereich-arbeitsort` | `place` |
| Anstellungsart | Kopfbereich | `employment_type` |
| Ausbildungsberuf | Kopfbereich | `apprenticeship` |
| Benötigter Schulabschluss | `#detail-kopfbereich-bildungsabschluss` | `school_degree` |
| Logo | Kopfbereich | `employer.logo_url` (nur URL notieren, nicht herunterladen) |

### Inhalt

- **Stellenausschreibung:** den kompletten Textkasten wörtlich übernehmen, mit Absätzen und Aufzählungen → `ba_scrape.md` und `description`.
- **Anforderungen:** jede Anforderung mit wörtlichem Beleg in `requirements[]`; Bewertung gegen das Profil (`met`, `partial`, `not_met`, `unknown`) und Profilbeleg. Ohne Profilbeleg ist sie `unknown`, nicht `met`.
- **Arbeitsorte:** `#detail-arbeitsorte-arbeitsort-*` → `locations[]`.
- **Arbeitgeber:** Hauptsitz, Unternehmensbeschreibung, Liste „Vorteile für Mitarbeitende“, Links zu Homepage und Karriereseite → `employer`, `benefits`.
- **Fußbereich:** Referenznummer `#detail-footer-referenznummer` → `reference_number`; Hinweis „Stelle betreut durch die BA“ → `managed_by_ba`.

### Informationen zur Bewerbung

Firma, Ansprechpartner (Anrede, Name), Abteilung, Straße, Hausnummer, PLZ, Ort, Telefon, E-Mail, Bewerbungsweg (E-Mail, Post oder Arbeitgeber-Website `#detail-bewerbung-url`) und „Sonstige Angaben zur Bewerbung“ (`#detail-bewerbung-anlagen`, geforderte Unterlagen) → `contact`, `application`.

Die Kontaktdaten liegen hinter einem Captcha (`#kontaktdaten-captcha-*`):

1. Zum Captcha scrollen.
2. Den Nutzer bitten: „Bitte löse im Browser das Captcha bei <Firma>. Sag Bescheid, wenn die Kontaktdaten sichtbar sind.“
3. Erst danach weiterlesen und übernehmen. Das Captcha nie selbst lösen oder umgehen.

Erfahrung (November 2026): Eine Lösung gilt nur im Tab, in dem sie eingegeben wurde, und hält dort für ca. 23–27 Anzeigen; danach erscheint das Captcha erneut. Andere Tabs und Subagenten sehen weiter das Captcha. Bei vielen Stellen deshalb zuerst alle Anzeigen ohne Kontakt erfassen (parallel möglich), danach die Kontaktblöcke im gelösten Tab nacheinander lesen und bei jedem neuen Captcha den Nutzer erneut bitten.

Anzeigen ohne Kontaktblock oder mit Bewerbungsweg „Über Internetseite des Arbeitgebers“: die verlinkte Portal-/Partnerseite öffnen (höchstens zwei Klicks bis zur konkreten Anzeige, keine Formulare ausfüllen, kein Login) und wörtlich nach `job_information/portal_page.md` übernehmen (URL, Abrufdatum, Anzeigentext, Kontakt, Bewerbungsweg, Unterlagen). Fehler wie tote Links, Links auf andere Stellen oder geschlossene Stellen in `application.notes` vermerken.

Regeln für den Kontakt:

- Name, Anrede und Rolle nur übernehmen, wenn sie auf der Seite stehen. `contact.source: "ba_captcha"` bzw. `"ba_page"`.
- Allgemeine Bewerbungsadresse gehört nach `application.email`, nicht in den persönlichen Kontakt.
- Straße ausgeschrieben mit Hausnummer in `contact.street` („Musterstraße 3“), auch wenn die Anzeige „Str.“ schreibt; in `ba_scrape.md` bleibt die Originalschreibweise.
- `confidence: "verified"` nur mit Name und Quell-URL, `partial` nur mit Quell-URL, sonst `unknown`.
- Anrede in `contact.salutation`: „Sehr geehrte Frau …“ / „Sehr geehrter Herr …“ nur mit belegtem Namen und belegter Anrede; sonst „Sehr geehrte Damen und Herren“.
- Fehlt ein Ansprechpartner, zuerst die Karriereseite der Firma prüfen (`company_website`). Eine allgemeine Websuche nach Kontaktdaten nur als letzter Ausweg (`web_search`), mit Quelle, und dem Nutzer sagen.
- Keine Kontaktdaten von ähnlichen Firmen übernehmen.

### Kurzrecherche zur Firma

Erlaubt ist eine kurze Websuche zur Firma (Branche, Größe, Produkte, Ausbildung). Jede Aussage, die in einen Brief soll, kommt nach `company_facts[]` mit wörtlichem Beleg, Quell-URL, Abrufdatum und `source_kind`. Briefe verwenden nur Aussagen aus `company_facts`. Die BA bleibt die einzige Quelle für Stellen.

### Entfernung zum Wohnort

`commute`: Wohnort aus dem Profil, Entfernung zum Arbeitsort (Quelle angeben, z. B. Trefferliste, wenn Such- und Wohnort gleich sind), `over_50_km`. Der Umzugssatz der E-Mail hängt am Suchort, nicht an der Entfernung (`references/writing.md`).

## 7. Speichern

- `job_information/ba_scrape.md` nach `assets/templates/ba_scrape.md`: alles von der Seite, menschenlesbar, wörtlich.
- `job_information/job.json` nach `assets/templates/job.json`, gültig gegen `assets/schemas/job.schema.json`.
- Was nicht auf der Seite steht, bleibt leer und wird nicht abgeleitet. Fristen nur übernehmen, wenn ein Datum ausdrücklich genannt ist.
- Offene Punkte mit Auswirkung (`blocking`, `non_blocking`, `research_needed`) in `open_questions`.
