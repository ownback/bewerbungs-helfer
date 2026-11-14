# Schrift der Bewerbungsmappe: Inter

- Inter 4.1, Copyright (c) 2016 The Inter Project Authors, https://github.com/rsms/inter
- Lizenz: SIL Open Font License 1.1, siehe `OFL.txt` (ohne Reserved Font Name; die Untermenge darf „Inter“ heißen)
- Quelle: `Inter-4.1.zip` der offiziellen Release-Seite, Ordner `web/` (statische Schnitte)

## Dateien

`Inter-Regular.woff2` (400), `Inter-Medium.woff2` (500), `Inter-SemiBold.woff2` (600), `Inter-Bold.woff2` (700).

Statische Schnitte statt der variablen Schrift: Chromium bettet sie im PDF als TrueType (CID) ein. Mit einer variablen Schrift entstehen Type-3-Fonts, deren Text sich schlecht auswählen und auswerten lässt.

Untermenge (pyftsubset aus fontTools), Latin + Latin Extended:

```bash
pyftsubset Inter-Regular.woff2 --flavor=woff2 --no-hinting --desubroutinize \
  --unicodes="U+0000-00FF,U+0100-024F,U+0259,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0300-0304,U+0306-0308,U+030A-030C,U+0326-0328,U+1E00-1EFF,U+2000-206F,U+2070-209F,U+20A0-20CF,U+2100-214F,U+2190-2199,U+2212,U+2215,U+2713,U+2714,U+25CF,U+FEFF,U+FFFD" \
  --layout-features='kern,liga,calt,clig,tnum,pnum,lnum,case,ccmp,locl,mark,mkmk,frac,sups,subs,ordn,dnom,numr,zero,ss01,ss02,cv05,cv08,cv11'
```

## Einbettung

`tools/build_mappe.py` setzt die vier Dateien bei jedem Bau als data-URIs in den Block `<style id="font-inter">` am Ende des Kopfs. Die `@font-face`-Regeln stehen in `assets/mappe/fonts.css`; jeder Platzhalter dort nennt eine Datei dieses Ordners ohne Endung (`Inter-Regular` für `Inter-Regular.woff2`). So funktioniert die Schrift ohne Installation und ohne Netz: in Tencil, beim direkten Öffnen der HTML-Datei und im Chromium-PDF.

Nach einer Änderung an den Dateien: `python3 tools/build_mappe.py master`, dann Profilvorlage und Mappen neu bauen. Ein weiterer Schnitt braucht die Datei hier und eine Zeile in `fonts.css`.
