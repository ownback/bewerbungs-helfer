# Bewerbungshelfer

Ein lokales, agent-agnostisches Repository für deutsche Ausbildungsbewerbungen.

Der Workflow startet in einem frischen Clone ohne Profil- oder Bewerbungsdaten, gleicht zuerst vorhandene Unterlagen ab und fragt nur echte Lücken ab. Danach sucht er im Browser genau eine Ausbildungsstelle bei der Bundesagentur für Arbeit und baut daraus eine vollständige Bewerbungsmappe als HTML. Nach der Freigabe wird die HTML-Datei über den Browser als A4-PDF exportiert.

Die Mappe ist für den Versand per E-Mail gedacht. Es wird nichts ausgedruckt und nichts handschriftlich unterschrieben.

## Die sechs Seiten

1. Deckblatt
2. Anschreiben
3. Lebenslauf
4. Motivationsschreiben
5. Zertifikate
6. Zeugnisse

**Pro Stelle neu:** Anschreiben und Motivationsschreiben.  
**Stabil:** Deckblatt, Lebenslauf, Zertifikate und Zeugnisse.

Das **Anschreiben** beantwortet, warum der Bewerber fachlich und persönlich zur Ausbildung passt. Das **Motivationsschreiben** erklärt, warum er diesen Weg gehen will und warum ihn das Thema beschäftigt.

Das **Deckblatt** ist eine gestaltete Titelseite mit Inhaltsangabe, optionalem großem Bewerbungsfoto, Name, Ausbildungsziel, Kontakt und Kurzprofil.

## Start

```bash
git clone https://github.com/ownback/bewerbungs-helfer
cd bewerbungs-helfer
```

Dann im Repo Claude, Codex oder einen anderen Harness starten und den Skill aufrufen. Der Skill-Name ist `bewerbungshelfer`.

- Codex / T3 Code: `$bewerbungshelfer`
- Claude Code: `CLAUDE.md` lädt `AGENTS.md` automatisch; der Skill ist über `.claude/skills/bewerbungshelfer` als `/bewerbungshelfer` verfügbar

Der Agent gleicht zuerst vorhandene Unterlagen ab, ergänzt das Profil und sucht danach eine Ausbildungsstelle. Anschließend baut er die Mappe.

Vorhandene Unterlagen können unter `profile/import/` abgelegt werden. Der Agent liest sie und fragt nur nach fehlenden Angaben.

## Dokumentation

- [Produktbrief](docs/product-brief.md)
- [Workflow](docs/workflow.md)
- [Profil und Fragebogen](docs/questionnaire.md)
- [Bundesagentur](docs/bundesagentur.md)
- [HTML-Mappe](docs/bewerbungsmappe.md)
- [Nachweise und Bilder](docs/asset-handling.md)
- [Designsystem](docs/design-system.md)
- [Datenverträge](docs/schemas.md)
- [Datenschutz](docs/privacy.md)
- [Warum Skill statt Skripte](docs/skill-vs-scripts.md)
- [Stencil](docs/stencil.md)
- [Prüfung](docs/testing.md)
- [Änderungsliste](docs/change-list.md)

## Repo-Aufbau

```text
.agents/skills/bewerbungshelfer/   Workflow, Referenzen, Vorlagen, Schemas, HTML-Basis
docs/                              Planung und Entscheidungen
profile/                           Lokales Profil, nicht versioniert
applications/                      Lokale Bewerbungen, nicht versioniert
```

## Grenzen

- Deutsch
- nur Ausbildung
- nur Bundesagentur für Arbeit
- eine Stelle pro Durchlauf
- keine Scraping- oder PDF-Skripte
- kein automatisches Absenden
- keine automatischen Portalausfüllungen
- keine erfundenen Qualifikationen oder Nachweise
- keine Demo-Daten im Repository

## Stencil

Die Basisvorlage kann in Stencil geöffnet, markiert und kommentiert werden. HTML und Stencil sind gemeinsam die Quelle der Wahrheit: HTML für Struktur und PDF-Export, Stencil für visuelle Markierungen und freigegebene Designänderungen. Details stehen in [docs/stencil.md](docs/stencil.md).

## Erster echter Durchlauf

Es sind keine Profil-, Job- oder Bewerbungsdaten im Repository. Der Agent startet nach dem Klonen mit einem leeren Profil, führt das Interview, sucht eine Stelle und baut daraus die erste Bewerbungsmappe.
