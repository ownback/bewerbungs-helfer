# Workflow

## Überblick

```text
Vorhandene Unterlagen auswerten
      ↓
Profilinterview nur für Lücken
      ↓
Profil strukturieren und bestätigen
      ↓
eine Ausbildungsstelle suchen
      ↓
Stelle und Unternehmensbezug belegen
      ↓
Passung prüfen
      ↓
Anschreiben und Motivation getrennt entwerfen
      ↓
Bewerbungsmappe als HTML bauen
      ↓
HTML auf Desktop, Mobil und A4 prüfen
      ↓
HTML freigeben
      ↓
PDF, Kontaktübersicht, E-Mail-Entwurf
```

Der Workflow stoppt vor jeder Außenwirkung. Der Nutzer sendet selbst.

## 0. Basisvorlage

Die gemeinsame HTML-Vorlage liegt unter `.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html`.

Der Nutzer kann sie in Stencil öffnen und Änderungen markieren. Der Agent setzt die Markierungen im HTML um. Beide Fassungen müssen denselben Stand zeigen. Ohne Stencil prüfen Agent und Nutzer die Vorlage direkt im Browser.

Die Basisvorlage wird aus der freigegebenen Designsprache aufgebaut und **einmalig** gestaltet. Sie enthält keine persönlichen Daten. Ist sie freigegeben, beginnt jeder Durchlauf mit Schritt 1. Unternehmensspezifische Änderungen bleiben in der jeweiligen Bewerbung.

## 1. Unterlagen und Profil

Prüfe zuerst `profile/master-profile.json`, `profile/master-profile.md` und alle bereitgestellten Dateien.

Wenn das Profil noch nicht bestätigt ist:

- lies PDFs, DOCX und Bilder vollständig und visuell,
- prüfe DOCX auf eingebettete Bilder,
- erfasse alle Stationen, Zeiträume, Aufgaben und Nachweise,
- markiere die Angaben als `confirmed`, `inferred`, `open` oder `conflict` (`field_status` bzw. `source_status`),
- frage nur nach fehlenden, defekten oder widersprüchlichen Punkten,
- speichere bestätigte Angaben in `profile/master-profile.json`,
- halte die menschenlesbare Fassung in `profile/master-profile.md` aktuell,
- validiere das JSON gegen das Profil-Schema.

Defekte Bilder, insbesondere ein leeres Bewerbungsfoto, werden nicht eingebunden. Sie bleiben als offener Punkt sichtbar.

## 2. Eine Stelle suchen

Der Agent nutzt den Browser des Harness und die öffentliche Bundesagentur-Jobsuche im Bereich **Ausbildung**. Eingegeben werden nur Suchbegriff, Ort oder PLZ und Umkreis.

Er zeigt eine kurze Auswahl. Der Nutzer wählt genau eine Stelle. Die Auswahl wird mit URL und Abrufdatum festgehalten.

## 3. Stelle belegen

Der Agent liest die vollständige Anzeige und erstellt `job.json`.

Er erfasst:

- Titel, Unternehmen, Ausbildungsberuf
- Ort, Start, Dauer, Frist
- vollständige Beschreibung
- Anforderungen mit wörtlichem Beleg
- Bewerbungsweg
- Ansprechpartner, Rolle, Abteilung
- vollständige Kontaktdaten
- offene Fragen mit Auswirkung

Fehlt ein Ansprechpartner, sucht der Agent auf der öffentlichen Unternehmensseite. Bleibt der Kontakt unklar, nutzt er „Sehr geehrte Damen und Herren“ und dokumentiert das.

Unternehmensbezogene Aussagen für die Briefe werden mit Quell-URL, wörtlichem Beleg und Abrufdatum gespeichert.

## 4. Passung prüfen

Jede Anforderung wird gegen das Profil bewertet:

- `met`
- `partial`
- `not_met`
- `unknown`

Das Anschreiben zeigt Eignung und die Wahrscheinlichkeit eines erfolgreichen Ausbildungsabschlusses. Das Motivationsschreiben erklärt den persönlichen Antrieb. Keine Lücke wird durch Werbesprache ersetzt.

Vor der Freigabe wird geprüft, dass beide Texte keine Hauptargumente, Anekdoten oder Projektgeschichten doppelt erzählen.

## 5. Unternehmensmappe bauen

Kopiere die Basisvorlage nach:

```text
applications/<unternehmen>-<beruf>/bewerbungsmappe.html
```

Daneben entsteht `application-manifest.json` mit Status `draft`.

Die sechs Abschnitte bleiben in dieser Reihenfolge:

1. Deckblatt
2. Anschreiben
3. Lebenslauf
4. Motivationsschreiben
5. Zertifikate
6. Zeugnisse

Deckblatt, Lebenslauf, Zertifikate und Zeugnisse werden aus dem Master-Profil und den bereitgestellten Dateien übernommen. Anschreiben und Motivationsschreiben werden neu geschrieben.

Das Deckblatt enthält Inhaltsangabe, ein optionales großes Bewerbungsfoto, Name, Ausbildungsziel, Kontakt und Kurzprofil. Es bleibt unternehmensunabhängig und enthält keinen Unternehmensnamen.

Nachweise werden als lokale Dateien in `applications/<...>/assets/` eingebunden. PDFs werden als eingebettete Objekte oder als verlinkte Dokumentkarten dargestellt; Bilder als echte Bildkarten. Fehlt ein Nachweis, steht das ausdrücklich in der Mappe.

## 6. HTML prüfen

Der Agent öffnet die Mappe im Browser und prüft Inhalt und Reihenfolge. Das responsive Bildschirmlayout wird mindestens bei 1440 × 900, 390 × 844 und 375 × 812 geprüft. Der A4-Umbruch wird anschließend separat in der Druckvorschau oder einer Headless-A4-Vorschau kontrolliert, inklusive Überlaufprüfung jeder Seite. Jede generierte Aussage muss durch Profil oder Stellenanzeige belegt sein. Der Nutzer prüft dieselbe Fassung.

Wenn Stencil verwendet wird, prüft der Nutzer die Markierungen und bestätigt, dass HTML und Stencil denselben Stand zeigen.

Erst nach eindeutiger Freigabe weiter. Dann Manifest auf `html_approved` setzen.

## 7. PDF und Versandvorbereitung

Der Agent nutzt die **PDF-Exportfunktion** des Browsers. Die Mappe wird nicht ausgedruckt und nicht handschriftlich unterschrieben:

- A4
- Hintergrundgrafiken an
- Kopf- und Fußzeile aus
- Maßstab 100 %

Danach erstellt er:

- `contact-summary.md`
- `email-draft.md`

Das Manifest wird auf `pdf_exported` und danach `ready_to_send` gesetzt. Er sendet nichts und füllt kein Portal aus.

## Abbruchkriterien

Stoppen und fragen bei:

- unklarem Profil
- blockierenden offenen Punkten
- fehlender Stellenauswahl
- widersprüchlichen Angaben
- fehlender Freigabe für Bilder
- unbelegten Aussagen
- fehlender HTML-Freigabe

## Ordner

```text
profile/
  import/
  assets/
  master-profile.json
  master-profile.md
applications/<unternehmen>-<beruf>/
  job.json
  application-manifest.json
  bewerbungsmappe.html
  bewerbungsmappe.pdf
  contact-summary.md
  email-draft.md
  assets/
```
