# Master-Profil

Das Profil hat zwei lokale Darstellungen:

- `profile/master-profile.json` ist die primäre, strukturierte Quelle.
- `profile/master-profile.md` ist die menschenlesbare Zusammenfassung für die gemeinsame Prüfung.

Beide Dateien bleiben gitignoriert. Die Vorlage liegt unter `assets/templates/master-profile.json`.

## Grundsätze

- Keine Angabe ohne Quelle oder ausdrückliche Bestätigung.
- Jede Angabe trägt einen Status: `confirmed`, `inferred`, `open` oder `conflict`.
- `inferred` ist eine vom Nutzer freigegebene Näherung, keine überprüfte Tatsache.
- Offene Punkte bleiben sichtbar und werden nicht durch plausible Texte ersetzt.
- Praktikum, Anstellung, Schulbildung und Projekt werden nie vermischt.
- Eine Jahresangabe bleibt eine Jahresangabe, wenn kein Monat bekannt ist.
- Defekte Dateien werden nicht eingebunden. Das gilt besonders für Fotos und Nachweise.

## Zeiträume

Jede Station verwendet:

```json
{
  "start": "YYYY-MM",
  "end": "YYYY-MM",
  "precision": "month|year|day|unknown",
  "is_current": false,
  "approx": false
}
```

- `approx: true` nur nach ausdrücklicher Freigabe einer plausiblen Näherung.
- `end: null` nur bei einer laufenden Station mit `is_current: true`.
- Bei `precision: "year"` steht im jeweiligen Feld nur `YYYY`.
- Die Darstellung im Lebenslauf folgt der gespeicherten Präzision.

## Person

Enthält Name, Anschrift, Telefon, E-Mail, Geburtsdatum, Geburtsort und Foto.

Das Foto ist nur gültig, wenn:

- die Datei technisch lesbar ist,
- sie zum Nutzer gehört,
- `consent: true` gesetzt ist,
- ein sinnvoller Zuschnitt gewählt wurde.

Eine leere oder defekte Datei bleibt mit `valid: false` und einem offenen Punkt im Profil.

## Ausbildung

Jeder Eintrag enthält:

- Einrichtung und Ort
- offiziellen Bildungsgang
- Abschluss oder Abschlussziel
- Zeitraum
- `expected: true`, wenn der Abschluss noch aussteht
- Details nur, wenn sie zur Einordnung nötig sind

Klassenbezeichnungen aus der Schulzeit sind keine Bildungsgänge. Sie dürfen als Detail vorkommen, aber nicht den offiziellen Bildungsgang ersetzen.

## Erfahrung

Jeder Eintrag enthält:

- Organisation und Ort
- `kind`: `internship`, `employment`, `volunteer` oder `other`
- Rolle
- Zeitraum
- konkrete Aufgaben
- optional ein Ergebnis
- Quellen und Status

Freigegebene typische Aufgaben werden als `confirmed` gespeichert. Sie müssen nicht in der finalen Mappe als Schätzung markiert werden.

## Projekte

Jeder Eintrag enthält:

- Name und Zeitraum
- Ziel
- eigene Rolle
- Werkzeuge
- Ergebnis
- optional einen Link
- nur echte, freigegebene Bilder mit `consent: true` und `valid: true`

Ein Projektbild darf niemals als angebliches Projektbild generiert werden.

## Fähigkeiten

Fähigkeiten werden in Gruppen und Sprachen gespeichert. Jede Fähigkeit hat:

- `name`
- `level`: `learning`, `basic`, `solid`, `advanced`, `future` oder `native`
- `scale`: ganze Zahl von 1 bis 5 für die visuelle Darstellung
- `evidence`: kurzer Beleg oder ausdrückliche Selbsteinschätzung
- `source_status`

Die Skala ist keine Prozentangabe. Sie dient nur der visuellen Gruppierung. Die Legende lautet:

| Skala | Bedeutung |
|---|---|
| 1 | Lernwunsch oder erste Berührung |
| 2 | Grundkenntnisse |
| 3 | sicher in bekannten Aufgaben |
| 4 | eigenständig und routiniert |
| 5 | sehr sicher |

`native` wird bei Sprachen unabhängig von der Balkenlänge zusätzlich als „Muttersprache“ ausgewiesen.

## Nachweise

Jeder Nachweis enthält:

- eindeutige ID
- Titel
- Aussteller
- Datum
- Datei
- Art
- Sichtbarkeit in der Mappe
- Originalstatus
- technische Gültigkeit
- Quelle und Status

Nicht vorhandene Nachweise bleiben offen. Es werden keine Ersatzdokumente erzeugt.

## Darstellung

`presentation` speichert freigegebene, wiederkehrende Darstellungsentscheidungen:

- Fußzeile: nur der Name
- Unternehmensname auf dem Deckblatt: nein
- Fähigkeiten: Diagramme
- Timeline-Verbindungslinien: nein
- Seitenzahlen: einfache Zahl ohne Gesamtseitenzahl
- Icon-IDs für wiederkehrende Kategorien

## Offene Punkte

Jeder offene Punkt hat eine ID, eine Frage, einen Status und eine Auswirkung:

- `blocking`: Workflow stoppt.
- `non_blocking`: Ausgabe kann weitergehen.
- `research_needed`: Agent recherchiert zuerst öffentlich.

Der Nutzer sieht vor der Mappe eine kompakte Liste aller offenen Punkte.
