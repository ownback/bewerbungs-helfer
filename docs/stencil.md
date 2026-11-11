# Stencil

## Rolle

Stencil ist das visuelle Bearbeitungswerkzeug für die HTML-Vorlage. Der Nutzer öffnet die HTML-Datei in Stencil, markiert Stellen und beschreibt Änderungen. Der Agent setzt diese Änderungen im HTML um.

Der Stencil-MCP-Server ist in dieser Sitzung nicht als Tool verfügbar. Die Dokumentation beschreibt deshalb die vorgesehene Rolle. Sobald der Server im Harness eingerichtet ist, kann der Nutzer die HTML-Datei öffnen und markieren.

## Source of Truth

- **HTML** ist die technische Quelle für Inhalt, Struktur und PDF-Export.
- **Stencil** ist die visuelle Quelle für Markierungen, Kommentare und freigegebene Designänderungen.
- Beide müssen nach einer Änderungsrunde denselben Stand zeigen.

Der Agent darf Stencil nicht als Voraussetzung behandeln. Wenn Stencil nicht verbunden ist, arbeitet er direkt am HTML und bittet den Nutzer um Freigabe im Browser. Sobald der Stencil-MCP-Server im Harness verfügbar ist, kann der Nutzer die aktuelle HTML-Datei öffnen und markieren.

## Ablauf

1. Agent erstellt die Basisvorlage `assets/bewerbungsmappe.html`.
2. Nutzer öffnet die Vorlage in Stencil und markiert gewünschte Änderungen.
3. Agent liest die Markierungen und ändert das HTML.
4. Nutzer prüft die geänderte Vorlage erneut in Stencil.
5. Erst wenn die Vorlage freigegeben ist, entstehen daraus die Bewerbungsmappen für einzelne Unternehmen.
6. Jede Unternehmensmappe kann wieder in Stencil geöffnet und kommentiert werden.
7. Agent übernimmt freigegebene Änderungen zurück in die Vorlage, wenn sie unternehmensunabhängig sind.

## Änderungen

### Vorlagenänderungen

Änderungen an Layout, Typografie, Farben, Seitenaufbau und gemeinsamen Komponenten gehören in die Basisvorlage. Sie werden auf alle künftigen Bewerbungen angewendet.

### Unternehmensspezifische Änderungen

Änderungen an Anschreiben, Motivationsschreiben, Projektkarten und Unternehmensdaten bleiben in der jeweiligen Bewerbung.

### Rückfluss

Wenn eine unternehmensspezifische Änderung auch für andere Bewerbungen sinnvoll ist, fragt der Agent, ob sie in die Basisvorlage übernommen werden soll. Ohne Freigabe bleibt sie lokal.

## Prüfung

Nach jeder Stencil-Runde:

- HTML öffnen und mit den Stencil-Markierungen vergleichen
- keine Platzhalter oder verwaisten Kommentare stehen lassen
- A4-Seitenumbrüche prüfen
- PDF-Export prüfen
- Nutzer bestätigt, dass HTML und Stencil denselben Stand zeigen

## Wenn Stencil nicht verfügbar ist

Der Workflow funktioniert weiter:

- Agent und Nutzer prüfen direkt im Browser.
- Änderungswünsche werden als Text oder Screenshot übergeben.
- Das HTML bleibt die einzige technische Quelle.
- Sobald Stencil verfügbar ist, kann die aktuelle HTML-Datei geöffnet werden.
