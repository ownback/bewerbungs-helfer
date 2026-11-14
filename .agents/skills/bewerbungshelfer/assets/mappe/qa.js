/* QA-Sonde der Bewerbungsmappe. Einzige Quelle für die Überlauf- und Füllgradmessung.

   Automatisch: tools/build_mappe.py lädt qa.html (lädt diese Datei) in Headless-Chromium und übergibt die
   Mappe und die Ansichten als URL-Parameter. Jede Ansicht ist ein iframe exakter Größe; das Ergebnis steht
   als JSON in <body data-qa="…">. Es entsteht keine Hilfsdatei.

   Von Hand: Mappe bei Desktopbreite (≥ 861 px, dort haben die Seiten feste A4-Größe) öffnen, diese Datei in
   die Konsole kopieren und mappeProbe(window) aufrufen, wenn alle Bilder geladen sind. hits muss [] sein.

   mappeOverflow prüft je Seite: (1) Inhalt länger oder breiter als die Seite, (2) Elemente, die in den
   unteren Rand ragen, (3) Elemente oder lange Wörter, die seitlich aus dem Satzspiegel oder aus ihrem
   Block laufen. Treffer werden mit data-overflow rot markiert und als „Seite: Grund“ gemeldet. */

function mappeOverflow(win) {
  const doc = win.document;
  return [...doc.querySelectorAll('.page')].flatMap((p, i) => {
    const r = p.getBoundingClientRect(), cs = win.getComputedStyle(p), hits = new Set();
    const bottom = r.bottom - parseFloat(cs.paddingBottom) + 2;
    const left = r.left + parseFloat(cs.paddingLeft) - 2, right = r.right - parseFloat(cs.paddingRight) + 2;
    if (p.scrollHeight > p.clientHeight + 1 || p.scrollWidth > p.clientWidth + 1) hits.add('Seite läuft über');
    for (const e of p.querySelectorAll('*')) {
      if (e.closest('.folio, svg')) continue;
      const st = win.getComputedStyle(e), b = e.getBoundingClientRect();
      if (st.position === 'absolute' || b.width === 0) continue;
      if (b.bottom > bottom) hits.add('ragt in den unteren Rand');
      if (!e.closest('.cover-page') && (b.left < left || b.right > right)) hits.add('seitlich aus dem Satzspiegel');
      if (st.display !== 'inline' && st.overflowX === 'visible' && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0) hits.add('Wort zu lang für Block');
    }
    if (hits.size) p.setAttribute('data-overflow', '');
    return [...hits].map(h => (i + 1) + ': ' + h);
  });
}

/* Füllgrad je Seite: [Seite, Anteil des Satzspiegels in %, Rest bis zum unteren Rand in mm]; negativ = Überlauf. */
function mappeFill(win) {
  const mm = 96 / 25.4;
  return [...win.document.querySelectorAll('.page')].map((p, i) => {
    const r = p.getBoundingClientRect(), cs = win.getComputedStyle(p);
    const top = r.top + parseFloat(cs.paddingTop), bottom = r.bottom - parseFloat(cs.paddingBottom);
    let low = top;
    for (const e of p.querySelectorAll('*')) {
      if (e.closest('.folio, svg, .section-head')) continue;
      const b = e.getBoundingClientRect();
      if (b.width > 0 && b.height > 0) low = Math.max(low, b.bottom);
    }
    return [i + 1, Math.round(100 * (low - top) / (bottom - top)), Math.round((bottom - low) / mm * 10) / 10];
  });
}

/* full = false: nur Breite und horizontaler Überlauf (Mobilansichten haben keine festen Seiten). */
function mappeProbe(win, full = true) {
  const doc = win.document, pages = [...doc.querySelectorAll('.page')];
  const out = { width: win.innerWidth, hscroll: doc.documentElement.scrollWidth - win.innerWidth, pages: pages.length };
  if (full) {
    out.hits = mappeOverflow(win);
    out.fill = mappeFill(win);
    out.cv = pages.flatMap((p, i) => p.dataset.section === '3' ? [i + 1] : []);
  }
  return out;
}

/* Prüfstand in qa.html: ?doc=<URL der Mappe>&views=<name>:<breite>x<höhe>,… Die erste Ansicht wird voll geprüft. */
(function () {
  const params = new URLSearchParams(location.search);
  if (!params.get('doc') || !params.get('views') || !document.body || document.querySelector('.page')) return;
  const views = params.get('views').split(',').map(v => {
    const [name, size] = v.split(':'), [w, h] = size.split('x').map(Number);
    return { name, w, h };
  });
  const loaded = views.map((v, i) => new Promise(resolve => {
    const f = document.createElement('iframe');
    f.style.cssText = `display:block;border:0;width:${v.w}px;height:${v.h}px`;
    f.addEventListener('load', async () => {
      try { await f.contentDocument.fonts.ready; } catch (e) {}
      setTimeout(() => {
        let data = null;
        try { data = mappeProbe(f.contentWindow, i === 0); } catch (e) { data = { error: String(e) }; }
        resolve([v.name, data]);
      }, 300);
    });
    f.src = params.get('doc');
    document.body.appendChild(f);
  }));
  Promise.all(loaded).then(results => document.body.setAttribute('data-qa', JSON.stringify(Object.fromEntries(results))));
})();
