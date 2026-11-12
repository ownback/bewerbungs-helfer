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

Die Vorlage `assets/bewerbungsmappe.html` enthält dieselben vier Dateien als data-URIs im Block `<style id="font-inter">` am Ende des Kopfs. So funktioniert die Schrift ohne Installation und ohne Netz: in Tencil (das nur die Vorlage ausliefert), beim direkten Öffnen der HTML-Datei und im Chromium-PDF. `tools/build_mappe.py` übernimmt den Kopf unverändert in jede Mappe.

Nach einer Änderung an den Dateien den Block neu erzeugen, z. B.:

```bash
python3 - <<'EOF'
import base64, pathlib, re
d = pathlib.Path('.agents/skills/bewerbungshelfer/assets')
faces = '\n'.join(
    f'    @font-face {{ font-family: "Inter"; font-style: normal; font-weight: {w}; font-display: block; '
    f'src: url(data:font/woff2;base64,{base64.b64encode((d / "fonts" / f"Inter-{n}.woff2").read_bytes()).decode()}) format("woff2"); }}'
    for w, n in ((400, 'Regular'), (500, 'Medium'), (600, 'SemiBold'), (700, 'Bold')))
t = d / 'bewerbungsmappe.html'
s = t.read_text()
s = re.sub(r'(<style id="font-inter">\n).*?(\n  </style>)', lambda m: m.group(1) + faces + m.group(2), s, flags=re.S)
t.write_text(s)
EOF
```
