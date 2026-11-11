# Projektanweisungen

Dieses Repository ist der lokale Bewerbungshelfer für Ausbildungsbewerbungen. Es ist agent-agnostisch und enthält keine Profil- oder Bewerbungsdaten.

## Sprache

- Kommunikation mit dem Nutzer: Deutsch.
- Generierte Bewerbungsunterlagen: Deutsch.
- Code, Dateinamen und technische Kommentare dürfen Englisch sein.

## Workflow

- Für jede Bewerbungsaufgabe zuerst `.agents/skills/bewerbungshelfer/SKILL.md` lesen.
- Immer nur eine Stelle und eine Bewerbungsmappe pro Durchlauf bearbeiten.
- Bundesagentur für Arbeit ist die einzige Jobquelle.
- Der Workflow beginnt mit der gemeinsamen HTML-Basisvorlage und dem Profilinterview.
- Browserwerkzeuge des Harness für die Jobsuche und die HTML-Prüfung verwenden. Keine Scraping-Skripte schreiben.
- Anschreiben und Motivationsschreiben werden pro Stelle neu geschrieben. Deckblatt, Lebenslauf, Zertifikate und Zeugnisse bleiben stabil.
- Keine Tatsachen, Kontaktdaten, Qualifikationen oder Nachweise erfinden.
- Keine Bewerbung automatisch absenden und keine Portale automatisch ausfüllen.
- PDF erst nach ausdrücklicher Freigabe der HTML-Fassung erzeugen.
- Stencil ist optionales visuelles Bearbeitungswerkzeug. HTML und Stencil gemeinsam sind die Quelle der Wahrheit; HTML bleibt für Struktur und PDF-Export maßgeblich.

## Daten

- `profile/` und `applications/` enthalten persönliche Daten und sind gitignoriert.
- Vor dem Commit prüfen, dass keine echten Kontaktdaten oder Dokumente erfasst wurden.
- Das Repository enthält keine Demo-Profile, Demo-Jobs oder Demo-Bewerbungen.
