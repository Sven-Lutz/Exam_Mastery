/* Exam Mastery learning environment runtime (em-learn-app-v1). No dependencies, no network, no eval.
   Course data: <script type="application/json" id="em-course"> (built by exam_mastery/learn_app.py).
   Only engine-rendered content HTML (textbook blocks, solutions) is inserted as HTML; everything else uses textContent.
   Learning events: localStorage key em-learn-v2 (versioned, export/import); lab attempts stay in em-progress-v1 and are
   read, never rewritten. No score of mastery is ever computed. */
(() => {
'use strict';
const C = JSON.parse(document.getElementById('em-course').textContent);
const app = document.getElementById('app');
const el = (tag, attrs, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (v === null || v === undefined || v === false) continue; if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); } for (const c of kids.flat()) if (c !== null && c !== undefined && c !== false) e.append(c instanceof Node ? c : document.createTextNode(String(c))); return e; };
const trusted = (tag, attrs, h) => { const e = el(tag, attrs); e.innerHTML = h; return e; };   /* engine-rendered, escaped at build time */
const byId = (xs) => Object.fromEntries(xs.map(x => [x.id, x]));
const S = byId(C.sections), I = byId(C.items), L = byId(C.labs), K = byId(C.cards);
const kcName = (k) => C.kcs[k] || 'Kompetenz ohne Bezeichnung';
const uniqNames = (ks) => { const seen = new Set(); return ks.filter(k => { const n = kcName(k); if (seen.has(n)) return false; seen.add(n); return true; }); };
const today = () => new Date().toISOString().slice(0, 10);

/* ------------------------------------------------------------ storage (versioned, offline, exportable) */
const Store = {
  KEY: 'em-learn-v2', LAB: 'em-progress-v1',
  load() { try { const d = JSON.parse(localStorage.getItem(this.KEY) || 'null'); if (d && d.schema === 2 && Array.isArray(d.events)) return d; } catch (e) { /* unreadable: start empty, nothing overwritten until a write */ } return { schema: 2, created: new Date().toISOString(), events: [], prefs: {} }; },
  save(d) { try { localStorage.setItem(this.KEY, JSON.stringify(d)); return true; } catch (e) { toast('Lernstand konnte nicht gespeichert werden (Speicher voll oder gesperrt). Exportieren Sie ihn unter „Lernstand“.'); return false; } },
  add(ev) { const d = this.load(); d.events.push(Object.assign({ t: new Date().toISOString(), chapter: C.chapter.id }, ev)); this.save(d); },
  pref(k, v) { const d = this.load(); if (v === undefined) return d.prefs[k]; d.prefs[k] = v; this.save(d); },
  labRaw() { try { return JSON.parse(localStorage.getItem(this.LAB) || '{}'); } catch (e) { return {}; } },
  labEvents() { const out = []; for (const r of Object.values(this.labRaw())) if (!r.ctx) for (const [t, ev] of r.at || []) out.push({ t: t.length === 16 ? t + ':00.000Z' : t, type: 'lab', lab: r.lab, task: r.task, kc_ids: r.kc_ids || [], ev }); return out; },
  all() { return this.load().events.concat(this.labEvents()).sort((a, b) => a.t < b.t ? -1 : 1); },
  exportObj() { return { schema: 'em-learn-export-v1', exported: new Date().toISOString(), course: C.course, chapter: C.chapter, learn: this.load(), labs: this.labRaw() }; },
  importObj(o) {
    if (!o || o.schema !== 'em-learn-export-v1' || !o.learn || o.learn.schema !== 2 || !Array.isArray(o.learn.events)) throw new Error('Keine Exam-Mastery-Lernhistorie (Schema em-learn-export-v1).');
    const d = this.load(); const key = e => [e.t, e.type, e.item || '', e.section || '', e.card || '', e.result || ''].join('|');
    const have = new Set(d.events.map(key)); let n = 0;
    for (const e of o.learn.events) { if (typeof e !== 'object' || typeof e.t !== 'string' || typeof e.type !== 'string') continue; if (!have.has(key(e))) { d.events.push(e); have.add(key(e)); n++; } }
    this.save(d);
    const labs = this.labRaw(); let m = 0;
    for (const [k, r] of Object.entries(o.labs || {})) if (!labs[k] && r && Array.isArray(r.at)) { labs[k] = r; m++; }
    try { localStorage.setItem(this.LAB, JSON.stringify(labs)); } catch (e) { }
    return [n, m];
  },
  clear() { try { localStorage.removeItem(this.KEY); localStorage.removeItem(this.LAB); } catch (e) { } },
};

/* ------------------------------------------------------------ observed status per competency (never a score) */
function observations() {
  const ev = Store.all(); const kc = {};
  const get = k => kc[k] || (kc[k] = { opened: false, attempts: 0, unaided: false, aided: false, solution: false, later: false, wrong: 0, hints: 0, lastDay: null, labs: 0 });
  const itemState = {};
  for (const e of ev) {
    if (e.type === 'section_open' && S[e.section]) S[e.section].kc_ids.forEach(k => get(k).opened = true);
    if (e.type === 'lab') { e.kc_ids.forEach(k => { const o = get(k); o.labs++; if (e.ev === 'correct' || e.ev === 'wrong') o.attempts++; }); continue; }
    if (!e.item || !I[e.item]) continue;
    const st = itemState[e.item] || (itemState[e.item] = { help: false, correctDays: new Set() });
    for (const k of I[e.item].kc_ids) {
      const o = get(k);
      if (e.type === 'hint') { st.help = true; o.hints++; }
      if (e.type === 'solution') { st.help = true; o.solution = true; }
      if (e.type === 'tutor') st.help = true;   // a prepared tutor briefing for this item counts as help (CD-7)
      if (e.type === 'attempt') {
        o.attempts++;
        if (e.result === 'correct') { const day = e.t.slice(0, 10); if (st.correctDays.size && !st.correctDays.has(day)) o.later = true; st.correctDays.add(day); if (st.help) o.aided = true; else o.unaided = true; }
        if (e.result === 'wrong' || e.result === 'partial') o.wrong++;
      }
    }
  }
  return kc;
}
function statusWords(o) {
  if (!o) return ['noch nicht geöffnet'];
  const w = [];
  if (o.opened) w.push('Theorie gelesen');
  if (o.labs) w.push('im Lab gearbeitet');
  if (o.unaided) w.push('ohne Hilfe richtig');
  if (o.aided) w.push('mit Hilfe richtig');
  if (o.solution) w.push('Lösung angesehen');
  if (o.later) w.push('an einem späteren Tag erneut richtig');
  if (o.attempts && !o.unaided && !o.aided) w.push(o.attempts + (o.attempts === 1 ? ' Versuch' : ' Versuche') + ', noch nicht richtig');
  if (!w.length) w.push('noch nicht bearbeitet');
  return w;
}

/* ------------------------------------------------------------ helpers */
let toastTimer = null;
function toast(msg) { const t = document.getElementById('toast'); if (!t) return; t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 4500); }
function typeset(node) { try { if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([node]).catch(() => { }); } catch (e) { } }
function download(name, text, type) { const a = el('a', { href: URL.createObjectURL(new Blob([text], { type: type || 'application/json' })), download: name }); document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
function theme() { return document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }
function applyTheme(v) { if (v === 'light' || v === 'dark') document.documentElement.dataset.theme = v; else delete document.documentElement.dataset.theme; document.querySelectorAll('iframe.lab-frame').forEach(f => { try { f.contentWindow.postMessage({ em: 'theme', theme: theme() }, '*'); } catch (e) { } }); }
const sectionOfKc = k => C.sections.find(s => s.kc_ids.includes(k));
function numberMatch(input, list) {
  const v = Number(String(input).trim().replace(/\s/g, '').replace(/\.(?=\d{3}(\D|$))/g, '').replace(',', '.'));
  if (!Number.isFinite(v)) return null;
  return list.some(x => { const n = Number(String(x).replace(',', '.')); return Math.abs(Math.abs(n) - Math.abs(v)) <= Math.max(0.5, Math.abs(n) * 0.005); });
}

/* ------------------------------------------------------------ shell */
const MODES = [['start', 'Überblick'], ['lernen', 'Lernen'], ['ueben', 'Üben'], ['klausur', 'Klausur'], ['stand', 'Lernstand'], ['tutor', 'Tutor'], ['material', 'Material']];
let main, nav, ctx, sideOpen = false, routed = false;
function shell() {
  const themeSel = el('select', { id: 'theme', 'aria-label': 'Darstellung', onchange: e => { Store.pref('theme', e.target.value); applyTheme(e.target.value); } },
    el('option', { value: 'auto' }, 'Auto'), el('option', { value: 'light' }, 'Hell'), el('option', { value: 'dark' }, 'Dunkel'));
  themeSel.value = Store.pref('theme') || 'auto';
  const menu = el('button', { class: 'icon-btn menu-btn', 'aria-controls': 'sidebar', 'aria-expanded': 'false', onclick: () => toggleSide() }, el('span', { 'aria-hidden': 'true' }, '☰'), el('span', { class: 'sr' }, 'Navigation'));
  const top = el('header', { class: 'topbar' }, menu, el('div', { class: 'brand' }, el('span', { class: 'brand-course' }, C.course), el('span', { class: 'brand-sep', 'aria-hidden': 'true' }, '·'), el('span', { class: 'brand-chapter' }, 'Kapitel ' + C.chapter.no + ' ' + C.chapter.title)), el('label', { class: 'theme-l' }, el('span', { class: 'sr' }, 'Darstellung'), themeSel));
  nav = el('nav', { id: 'sidebar', class: 'sidebar', 'aria-label': 'Kursnavigation' });
  main = el('main', { id: 'main', class: 'main', tabindex: '-1' });
  ctx = el('aside', { class: 'context', 'aria-label': 'Zum aktuellen Abschnitt' });
  const scrim = el('div', { class: 'scrim', onclick: () => toggleSide(false) });
  app.replaceChildren(top, el('div', { class: 'body' }, nav, scrim, main, ctx), el('div', { id: 'toast', class: 'toast', role: 'status', 'aria-live': 'polite', hidden: true }));
  applyTheme(themeSel.value);
}
function toggleSide(v) { sideOpen = v === undefined ? !sideOpen : v; document.body.classList.toggle('side-open', sideOpen); document.querySelector('.menu-btn').setAttribute('aria-expanded', String(sideOpen)); }
function renderNav(route) {
  const obs = observations(); const opened = new Set(Store.load().events.filter(e => e.type === 'section_open').map(e => e.section));
  const list = el('ul', { class: 'nav-modes' }, MODES.map(([m, t]) => el('li', {}, el('a', { href: '#/' + m, class: 'nav-mode', 'aria-current': route.mode === m ? 'page' : null }, t))));
  const secs = el('ol', { class: 'nav-sections' }, C.sections.map(s => el('li', {}, el('a', { href: '#/lernen/' + s.id, class: 'nav-sec' + (opened.has(s.id) ? ' seen' : ''), 'aria-current': route.mode === 'lernen' && route.id === s.id ? 'location' : null },
    el('span', { class: 'sec-no' }, s.no), el('span', { class: 'sec-t' }, s.title), s.labs.length ? el('span', { class: 'chip-lab', title: 'enthält ein interaktives Lab' }, 'Lab') : null, el('span', { class: 'sr' }, opened.has(s.id) ? ' (gelesen)' : '')))));
  nav.replaceChildren(el('div', { class: 'nav-head' }, el('div', { class: 'eyebrow' }, C.course), el('div', { class: 'nav-title' }, C.chapter.title)), list, el('div', { class: 'nav-label' }, 'Kapitel'), secs);
}
function setContext(s) {
  if (!s) { ctx.replaceChildren(); ctx.hidden = true; return; }
  ctx.hidden = false;
  const obs = observations();
  const blocks = [el('h2', { class: 'ctx-h' }, 'In diesem Abschnitt')];
  if (s.kc_ids.length) blocks.push(el('div', { class: 'ctx-group' }, el('h3', {}, 'Lernziele'), el('ul', { class: 'ctx-kcs' }, uniqNames(s.kc_ids).map(k => { const w = statusWords(obs[k]).filter(x => x !== 'Theorie gelesen'); return el('li', {}, kcName(k), w.length && obs[k] ? el('span', { class: 'ctx-st' }, w.join(' · ')) : null); }))));
  if (s.labs.length) blocks.push(el('div', { class: 'ctx-group' }, el('h3', {}, 'Interaktiv'), el('ul', {}, s.labs.map(l => el('li', {}, el('a', { href: '#lab-' + l, onclick: e => { e.preventDefault(); const t = document.getElementById('lab-' + l); if (t) t.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); } }, L[l].title))))));
  if (s.items.length) blocks.push(el('div', { class: 'ctx-group' }, el('h3', {}, 'Passende Übungen'), el('ul', {}, s.items.map(i => el('li', {}, el('a', { href: '#/ueben/' + i }, shortPrompt(I[i])), el('span', { class: 'ctx-st' }, I[i].stage_title))))));
  if (s.sources.length) blocks.push(el('div', { class: 'ctx-group' }, el('h3', {}, 'Quellen'), el('ul', { class: 'ctx-src' }, s.sources.slice(0, 6).map(x => el('li', {}, x)))));
  blocks.push(el('a', { class: 'btn btn-ghost', href: '#/tutor/' + s.id }, 'Tutor-Briefing zu diesem Abschnitt'));
  ctx.replaceChildren(...blocks);
  typeset(ctx);
}
/* B22: never cut inside \( ... \) - a cut formula stays raw TeX in the sidebar; cut before it (or after it if it starts the text) */
function shortPrompt(it) { if (it.title) return it.title; const t = (new DOMParser().parseFromString(it.prompt, 'text/html').body.textContent || '').trim(); if (t.length <= 70) return t;
  let cut = 68; const open = t.lastIndexOf('\\(', cut), close = t.lastIndexOf('\\)', cut);
  if (open > close) { const end = t.indexOf('\\)', open); cut = open > 20 || end < 0 ? open : end + 2; }
  return t.slice(0, cut).trimEnd() + ' …'; }

/* ------------------------------------------------------------ views */
function viewStart() {
  const ev = Store.load().events; const last = [...ev].reverse().find(e => e.type === 'section_open');
  const opened = new Set(ev.filter(e => e.type === 'section_open').map(e => e.section));
  const nextSec = C.sections.find(s => !opened.has(s.id)) || C.sections[0];
  const obs = observations();
  const openKc = Object.keys(C.kcs).filter(k => !(obs[k] && (obs[k].unaided || obs[k].aided)));
  const items = C.items.filter(i => !i.exam);
  const hero = el('section', { class: 'hero' }, el('div', { class: 'eyebrow' }, C.course + ' · Kapitel ' + C.chapter.no), el('h1', {}, C.chapter.title),
    el('p', { class: 'lede' }, `${C.sections.length} Abschnitte · ${C.labs.length} interaktive ${C.labs.length === 1 ? 'Simulation' : 'Simulationen'} · ${items.length} Übungsaufgaben · ${C.exam.items.length} Klausuraufgaben`),
    el('div', { class: 'hero-actions' },
      last && S[last.section] ? el('a', { class: 'btn btn-primary', href: '#/lernen/' + last.section }, 'Weiterlesen: ' + S[last.section].title) : el('a', { class: 'btn btn-primary', href: '#/lernen/' + C.sections[0].id }, 'Kapitel beginnen'),
      last && nextSec && nextSec.id !== last.section ? el('a', { class: 'btn', href: '#/lernen/' + nextSec.id }, 'Noch nicht gelesen: ' + nextSec.title) : null));
  const cards = el('div', { class: 'tiles' },
    tile('Lernen', 'Lehrbuch mit eingebetteten Simulationen und Kurzabfragen an Ort und Stelle.', '#/lernen/' + (last ? last.section : C.sections[0].id), `${opened.size} von ${C.sections.length} Abschnitten geöffnet`),
    tile('Üben', 'Aufgaben nach Lernziel und Schwierigkeit, mit gestuften Hinweisen und Musterlösung auf Anfrage.', '#/ueben', `${items.length} Aufgaben`),
    tile('Klausur', 'Probeklausur als eigener Modus; Lösungen und Bewertungsschema erst nach der Abgabe.', '#/klausur', C.exam.total_points ? `${C.exam.items.length} Aufgaben · ${C.exam.total_points} Punkte` : 'keine Probeklausur'),
    tile('Lernstand', 'Was Sie tatsächlich bearbeitet haben – je Lernziel, ohne Punktwert der Beherrschung.', '#/stand', `${Object.keys(C.kcs).length - openKc.length} von ${Object.keys(C.kcs).length} Lernzielen mit richtiger Lösung`));
  const toc = el('section', { class: 'toc', 'aria-labelledby': 'toc-h' }, el('h2', { id: 'toc-h', class: 'eyebrow' }, 'Inhalt des Kapitels'),
    el('ol', { class: 'toc-list' }, C.sections.map(s => el('li', {}, el('a', { href: '#/lernen/' + s.id, class: opened.has(s.id) ? 'seen' : '' }, el('span', { class: 'toc-no' }, s.no), el('span', { class: 'toc-t' }, s.title),
      s.labs.length ? el('span', { class: 'chip-lab' }, 'Simulation') : null, el('span', { class: 'toc-st' }, opened.has(s.id) ? 'gelesen' : ''))))));
  const sims = C.labs.length ? el('section', { class: 'sims', 'aria-labelledby': 'sim-h' }, el('h2', { id: 'sim-h', class: 'eyebrow' }, 'Interaktive Simulationen in diesem Kapitel'),
    el('div', { class: 'sim-grid' }, C.labs.map(l => el('a', { class: 'sim', href: '#/lernen/' + l.section }, l.static_svg ? trusted('div', { class: 'sim-fig' }, l.static_svg) : null,
      el('span', { class: 'sim-t' }, l.title), el('span', { class: 'sim-s' }, 'Abschnitt ' + (S[l.section] ? S[l.section].no + ' · ' + S[l.section].title : '')))))) : null;
  const rec = openKc.slice(0, 3).map(k => { const s = sectionOfKc(k); return el('li', {}, el('a', { href: s ? '#/lernen/' + s.id : '#/ueben' }, kcName(k)), s ? el('span', { class: 'muted' }, ' – ' + s.title) : null); });
  return [hero, cards, toc, sims, rec.length ? el('section', { class: 'panel' }, el('h2', {}, 'Als Nächstes sinnvoll'), el('p', { class: 'muted' }, 'Lernziele, zu denen noch keine richtige Lösung beobachtet wurde:'), el('ul', { class: 'plain' }, rec)) : null,
    el('p', { class: 'fine' }, (C.chapter.status || '').replace(/\*\*/g, ''))];
}
function tile(t, d, href, meta) { return el('a', { class: 'tile', href }, el('h2', {}, t), el('p', {}, d), el('span', { class: 'tile-meta' }, meta)); }

function viewSection(id) {
  const s = S[id] || C.sections[0]; Store.add({ type: 'section_open', section: s.id, kc_ids: s.kc_ids });
  const idx = C.sections.indexOf(s);
  const art = el('article', { class: 'reader' });
  art.append(el('div', { class: 'eyebrow' }, 'Abschnitt ' + s.no), el('h1', {}, s.title));
  if (s.kc_ids.length) art.append(el('div', { class: 'objectives' }, el('span', { class: 'obj-l' }, 'Sie lernen hier:'), el('ul', {}, uniqNames(s.kc_ids).map(k => el('li', {}, kcName(k))))));
  const labsAfter = {}; s.labs.forEach(l => (labsAfter[L[l].after] = labsAfter[L[l].after] || []).push(L[l]));
  s.parts.forEach((p, i) => { art.append(trusted('div', { class: 'part part-' + p.type }, p.html)); (labsAfter[i] || []).forEach(l => art.append(labEmbed(l))); });
  (C.tracks || []).filter(t => t.kc_ids.some(k => s.kc_ids.includes(k))).forEach(t => art.append(trackEmbed(t)));
  if (s.cards.length) art.append(quickChecks(s));
  if (s.items.length) art.append(el('section', { class: 'panel practice-link' }, el('h2', {}, 'Selbst anwenden'), el('ul', { class: 'plain' }, s.items.map(i => el('li', {}, el('a', { href: '#/ueben/' + i }, shortPrompt(I[i])), el('span', { class: 'muted' }, ' · ' + I[i].stage_title))))));
  art.append(el('nav', { class: 'pager', 'aria-label': 'Abschnitte' }, idx > 0 ? el('a', { class: 'btn', href: '#/lernen/' + C.sections[idx - 1].id, rel: 'prev' }, '← ' + C.sections[idx - 1].title) : el('span'),
    idx < C.sections.length - 1 ? el('a', { class: 'btn btn-primary', href: '#/lernen/' + C.sections[idx + 1].id, rel: 'next' }, C.sections[idx + 1].title + ' →') : el('a', { class: 'btn btn-primary', href: '#/ueben' }, 'Zu den Übungen →')));
  setContext(s);
  return [art];
}
function trackEmbed(t) {   /* v0.19: the adaptive learning track of this section, inside the chapter */
  const box = el('section', { class: 'lab-embed track-embed', id: 'track-' + t.id.replace(/\W+/g, '-'), 'aria-label': 'Diagnostisch üben: ' + t.title });
  const frame = el('iframe', { class: 'lab-frame', title: t.title, src: t.href + '?embed=1&theme=' + theme(), 'data-track': t.id });
  box.append(el('div', { class: 'lab-head' }, el('div', {}, el('span', { class: 'eyebrow' }, 'Diagnostisch üben'), el('h2', {}, t.title)), el('a', { class: 'btn btn-ghost', href: t.href, target: '_blank', rel: 'noopener' }, 'Eigenes Fenster')),
    el('p', { class: 'muted' }, 'Jede Antwort wird geprüft; erkennt die Engine einen typischen Fehler, zeigt sie die Ursache im Bild und wählt die nächste Aufgabe danach. Kein Prozentwert, nur beobachtete Schritte.'), frame);
  return box;
}
function labEmbed(l) {
  const box = el('section', { class: 'lab-embed', id: 'lab-' + l.id, 'aria-label': 'Interaktive Simulation: ' + l.title });
  const frame = el('iframe', { class: 'lab-frame', title: l.title, src: l.href + '?embed=1&theme=' + theme(), 'data-lab': l.id });
  const head = el('div', { class: 'lab-head' }, el('div', {}, el('span', { class: 'eyebrow' }, 'Interaktive Simulation'), el('h2', {}, l.title)), el('a', { class: 'btn btn-ghost', href: l.href, target: '_blank', rel: 'noopener' }, 'Eigenes Fenster'));
  const stat = l.static_svg ? el('details', { class: 'lab-static' }, el('summary', {}, 'Statische Abbildung (wie im PDF)'), trusted('div', { class: 'fig' }, l.static_svg)) : null;
  box.append(head, el('p', { class: 'muted' }, 'Erst vorhersagen, dann beobachten: Die Simulation öffnet sich nach Ihrer Vorhersage. Wiederholer können die Vorhersage überspringen.'), frame, stat);
  return box;
}
window.addEventListener('message', e => {   /* height of embedded labs; data only, never code */
  const d = e.data; if (!d || d.em !== 'height' || typeof d.h !== 'number') return;
  document.querySelectorAll('iframe.lab-frame').forEach(f => { if (f.contentWindow === e.source) f.style.height = Math.min(Math.max(d.h + 4, 300), 20000) + 'px'; });
});
function quickChecks(s) {
  const box = el('section', { class: 'panel quick' }, el('h2', {}, 'Kurz prüfen'), el('p', { class: 'muted' }, 'Erst selbst beantworten, dann aufdecken – Abrufen festigt mehr als erneutes Lesen.'));
  s.cards.forEach(cid => { const c = K[cid]; const back = trusted('div', { class: 'qc-back', hidden: true }, c.back);
    const rate = el('div', { class: 'qc-rate', hidden: true }, el('span', { class: 'muted' }, 'Gewusst?'), ['ja', 'teilweise', 'nein'].map(v => el('button', { class: 'btn btn-small', onclick: () => { Store.add({ type: 'card', card: cid, section: s.id, result: v === 'ja' ? 'correct' : v === 'teilweise' ? 'partial' : 'wrong' }); rate.replaceChildren(el('span', { class: 'muted' }, 'Notiert: ' + v + '.')); } }, v)));
    const btn = el('button', { class: 'btn btn-small', 'aria-expanded': 'false', onclick: () => { back.hidden = false; rate.hidden = false; btn.remove(); typeset(back); } }, 'Antwort aufdecken');
    box.append(el('div', { class: 'qc' }, trusted('div', { class: 'qc-front' }, c.front), btn, back, rate)); });
  return box;
}

function viewPractice(focus) {
  const groups = {}; C.items.filter(i => !i.exam).forEach(i => (groups[i.stage_title] = groups[i.stage_title] || []).push(i));
  const kcFilter = Store.pref('kcFilter') || '';
  const sel = el('select', { 'aria-label': 'Nach Lernziel filtern', onchange: e => { Store.pref('kcFilter', e.target.value); route(); } }, el('option', { value: '' }, 'Alle Lernziele'), Object.keys(C.kcs).filter(k => C.items.some(i => i.kc_ids.includes(k))).map(k => el('option', { value: k }, kcName(k))));
  sel.value = kcFilter;
  const out = [el('div', { class: 'eyebrow' }, 'Üben'), el('h1', {}, 'Aufgaben'), el('p', { class: 'lede' }, 'Erst selbst lösen. Hinweise kommen gestuft; die Musterlösung öffnet sich erst nach einem eigenen Versuch.'), el('div', { class: 'filters' }, sel)];
  for (const t of C.tracks || []) { const sec = C.sections.find(x => t.kc_ids.some(k => x.kc_ids.includes(k)));
    out.splice(3, 0, el('section', { class: 'panel track-link' }, el('h2', {}, 'Adaptiv üben: ' + t.title), el('p', {}, t.case), el('a', { class: 'btn btn-primary', href: sec ? '#/lernen/' + sec.id : t.href }, 'Lernstrecke öffnen'))); }
  for (const [stage, list] of Object.entries(groups)) {
    const vis = list.filter(i => !kcFilter || i.kc_ids.includes(kcFilter)); if (!vis.length) continue;
    out.push(el('h2', { class: 'stage-h' }, stage), ...vis.map(i => itemCard(i, focus === i.id, list.indexOf(i) + 1)));
  }
  setContext(focus && I[focus] && I[focus].section ? S[I[focus].section] : null);
  if (focus) setTimeout(() => { const t = document.getElementById('item-' + focus); if (t) { t.scrollIntoView(); t.querySelector('textarea, input, button')?.focus({ preventScroll: true }); } }, 30);
  return out;
}
function itemCard(it, open, n) {
  const box = el('article', { class: 'item' + (open ? ' focus' : ''), id: 'item-' + it.id, 'aria-labelledby': 'ih-' + it.id });
  const meta = [it.points ? it.points + ' P.' : null, it.kc_ids.map(kcName).join(' · ')].filter(Boolean).join(' · ');
  box.append(el('h3', { id: 'ih-' + it.id }, (n ? 'Aufgabe ' + n : it.stage_title) + (it.title ? ' · ' + it.title : '') + (it.minutes ? ' · ≈ ' + it.minutes + ' Min.' : '') + (it.points ? ' · ' + it.points + ' Punkte' : '')), el('p', { class: 'item-kc muted' }, uniqNames(it.kc_ids).map(kcName).join(' · ')), trusted('div', { class: 'prompt' }, it.prompt));
  const draftKey = 'draft:' + it.id; const ta = el('textarea', { rows: 4, 'aria-label': 'Ihre Lösung', placeholder: 'Ihre Lösung (bleibt nur in diesem Browser)' }); ta.value = Store.pref(draftKey) || '';
  ta.addEventListener('change', () => Store.pref(draftKey, ta.value));
  const fb = el('div', { class: 'feedback', role: 'status', 'aria-live': 'polite' });
  const hints = el('ol', { class: 'hints' }); let shown = 0; let attempted = false;
  const solBtn = el('button', { class: 'btn', disabled: true, onclick: () => { sol.hidden = false; solBtn.disabled = true; Store.add({ type: 'solution', item: it.id }); typeset(sol); selfRate.hidden = false; } }, 'Musterlösung öffnen');
  const unlock = () => { attempted = true; solBtn.disabled = !it.solution; };
  const hintBtn = it.hints.length ? el('button', { class: 'btn', onclick: () => { if (shown < it.hints.length) { hints.append(trusted('li', {}, it.hints[shown++])); Store.add({ type: 'hint', item: it.id, n: shown }); typeset(hints); } if (shown >= it.hints.length) hintBtn.disabled = true; } }, `Hinweis (${it.hints.length} Stufen)`) : null;
  const tools = el('div', { class: 'row' });
  if (it.numbers.length) {
    const num = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Ihr Endergebnis (Zahl)', placeholder: 'Endergebnis' });
    const chk = el('button', { class: 'btn btn-primary', onclick: () => { const r = numberMatch(num.value, it.numbers); if (r === null) { fb.textContent = 'Bitte eine Zahl eingeben.'; return; } unlock();
      Store.add({ type: 'attempt', item: it.id, result: r ? 'correct' : 'wrong', mode: 'number' });
      fb.replaceChildren(el('strong', { class: r ? 'ok' : 'bad' }, r ? 'Stimmt mit einem Ergebnis der Musterlösung überein. ' : 'Diese Zahl kommt in der Musterlösung nicht vor. '),
        r ? 'Vergleichen Sie auch Ihren Rechenweg mit der Musterlösung.' : 'Prüfen Sie Ihren Rechenweg oder nutzen Sie einen Hinweis.', !r && it.section ? el('a', { href: '#/lernen/' + it.section, class: 'fb-link' }, ' Nachlesen: ' + S[it.section].title) : null); } }, 'Ergebnis prüfen');
    num.addEventListener('keydown', e => { if (e.key === 'Enter') chk.click(); });
    tools.append(num, chk);
  } else {
    tools.append(el('button', { class: 'btn btn-primary', onclick: () => { if (ta.value.trim().length < 10) { fb.textContent = 'Notieren Sie zuerst Ihre eigene Antwort (mindestens ein Satz).'; return; } Store.pref(draftKey, ta.value); unlock(); Store.add({ type: 'draft', item: it.id }); fb.textContent = 'Antwort notiert. Vergleichen Sie jetzt mit der Musterlösung und bewerten Sie sich selbst.'; } }, 'Antwort festhalten'));
  }
  if (hintBtn) tools.append(hintBtn);
  tools.append(solBtn);
  const sol = trusted('div', { class: 'solution', hidden: true }, it.solution || '<p>Keine Musterlösung vorhanden.</p>');
  const selfRate = el('div', { class: 'self-rate', hidden: true }, el('span', { class: 'muted' }, 'Ihre Selbsteinschätzung:'),
    [['correct', 'richtig'], ['partial', 'teilweise'], ['wrong', 'falsch']].map(([v, t]) => el('button', { class: 'btn btn-small', onclick: () => { Store.add({ type: 'attempt', item: it.id, result: v, mode: 'self' }); selfRate.replaceChildren(el('span', { class: 'muted' }, 'Notiert: ' + t + ' (Selbsteinschätzung).'), v !== 'correct' && it.section ? el('a', { href: '#/lernen/' + it.section, class: 'fb-link' }, ' Passender Abschnitt: ' + S[it.section].title) : null); } }, t)));
  box.append(ta, tools, fb, hints, sol, selfRate);
  return box;
}

function viewExam() {
  const items = C.exam.items.map(id => I[id]).filter(Boolean);
  if (!items.length) return [el('h1', {}, 'Klausur'), el('p', {}, 'Für dieses Kapitel gibt es keine Probeklausur.')];
  const started = Store.pref('examStart');
  const head = [el('div', { class: 'eyebrow' }, 'Klausurtraining'), el('h1', {}, 'Probeklausur'), el('p', { class: 'lede' }, `${items.length} Aufgaben · ${C.exam.total_points} Punkte${C.exam.minutes ? ' · ' + C.exam.minutes + ' Minuten' : ''}${C.exam.aids ? ' · Hilfsmittel: ' + C.exam.aids : ''}. ${C.exam.subtitle || ''}`),
    el('p', { class: 'muted' }, 'Bearbeiten Sie alle Aufgaben ohne Unterlagen. Lösungen und Bewertungsschema erscheinen erst nach der Abgabe. Die Punkte sind eine Selbstbewertung, keine offizielle Bewertung.')];
  if (!started) return [...head, el('button', { class: 'btn btn-primary', onclick: () => { Store.pref('examStart', new Date().toISOString()); Store.add({ type: 'exam_start' }); route(); } }, 'Klausur beginnen')];
  const sheets = items.map((it, n) => { const ta = el('textarea', { rows: 6, 'aria-label': 'Antwort zu Aufgabe ' + (n + 1) }); ta.value = Store.pref('exam:' + it.id) || ''; ta.addEventListener('change', () => Store.pref('exam:' + it.id, ta.value));
    return el('article', { class: 'item exam-item', id: 'item-' + it.id }, el('h3', {}, `Aufgabe ${n + 1}${it.title ? ' · ' + it.title : ''}`, el('span', { class: 'meta' }, ` ${it.minutes ? '≈ ' + it.minutes + ' Min. · ' : ''}${it.points} Punkte`)), trusted('div', { class: 'prompt' }, it.prompt), ta); });
  const timer = el('span', { class: 'timer' }); const tick = () => { const m = Math.floor((Date.now() - Date.parse(started)) / 60000); timer.textContent = 'Bearbeitungszeit: ' + m + (C.exam.minutes ? ' von ' + C.exam.minutes : '') + ' min'; timer.classList.toggle('over', !!C.exam.minutes && m > C.exam.minutes); }; tick(); const iv = setInterval(() => { if (!document.body.contains(timer)) clearInterval(iv); else tick(); }, 20000);
  const submit = el('button', { class: 'btn btn-primary', onclick: () => { if (!confirm('Klausur abgeben? Danach werden die Lösungen angezeigt.')) return; Store.add({ type: 'exam_submit' }); sheets.forEach((sh, n) => { const it = items[n]; sh.querySelector('textarea').disabled = true;
      const sol = trusted('div', { class: 'solution' }, it.solution); const rub = el('fieldset', { class: 'rubric' }, el('legend', {}, 'Selbstbewertung nach Schema'), it.rubric.map(([c, p], j) => el('label', { class: 'rub-row' }, el('input', { type: 'checkbox', 'data-p': p }), trusted('span', {}, c), el('span', { class: 'pts' }, p + ' P.'))));
      sh.append(sol, rub); typeset(sol); });
    const total = el('p', { class: 'score', role: 'status' }); const upd = () => { let s = 0; document.querySelectorAll('.rubric input:checked').forEach(x => s += Number(x.dataset.p)); total.textContent = `Selbstbewertung: ${s} von ${C.exam.total_points} Punkten (keine offizielle Bewertung).`; };
    document.querySelectorAll('.rubric input').forEach(x => x.addEventListener('change', upd)); upd();
    const save = el('button', { class: 'btn', onclick: () => { let s = 0; document.querySelectorAll('.rubric input:checked').forEach(x => s += Number(x.dataset.p)); Store.add({ type: 'exam_self_score', points: s, of: C.exam.total_points }); Store.pref('examStart', null); toast('Selbstbewertung gespeichert. Eine neue Bearbeitung beginnt mit „Klausur beginnen“.'); } }, 'Selbstbewertung speichern');
    const bp = (C.exam.blueprint || []).length ? el('section', { class: 'panel blueprint' }, el('h2', {}, 'Blueprint dieser Klausur'),
      el('table', {}, el('thead', {}, el('tr', {}, ...['Aufgabe', 'Kompetenz', 'Operator', 'Anforderung', 'Punkte', 'Zeit'].map(t => el('th', {}, t)))),
        el('tbody', {}, ...C.exam.blueprint.map(r => el('tr', {}, el('td', {}, String(r.no || r.item)), el('td', {}, r.competency), el('td', {}, r.operator), el('td', {}, r.level || ''), el('td', {}, String(r.points)), el('td', {}, (r.minutes || '') + ' Min.')))))) : null;
    submit.replaceWith(el('div', { class: 'row' }, total, save)); if (bp) document.querySelector('.row').after(bp); } }, 'Abgeben und Lösungen anzeigen');
  setContext(null);
  return [...head, el('p', {}, timer), ...sheets, submit];
}

function trackRows() {
  let d = null; try { d = JSON.parse(localStorage.getItem('em-tutor-v1') || 'null'); } catch (e) { d = null; }
  const rows = []; for (const t of C.tracks || []) { const sm = d && d.tracks && d.tracks[t.id] && d.tracks[t.id].summary; if (!sm) continue;
    rows.push(el('section', { class: 'kc-group' }, el('div', { class: 'kc-group-h' }, el('h2', {}, 'Lernstrecke: ' + t.title), el('span', { class: 'muted' }, (d.tracks[t.id].events || []).filter(e => e.type === 'attempt').length + ' geprüfte Antworten')),
      el('ul', { class: 'kc-list' }, sm.kcs.map(([n, w]) => el('li', { class: 'kc-row' }, el('div', { class: 'kc-name' }, n), el('ul', { class: 'chips' }, el('li', { class: 'chip' + (/ohne Hilfe/.test(w) ? ' chip-ok' : /noch nicht/.test(w) ? ' chip-open' : '') }, w)), el('span')))))); }
  return rows;
}
function viewProgress() {
  const obs = observations(); const ev = Store.all();
  /* one row per competency NAME (several plan entries can share it); observations of all of them are merged */
  const merge = ks => ks.map(k => obs[k]).filter(Boolean).reduce((m, o) => ({ opened: m.opened || o.opened, attempts: m.attempts + o.attempts, unaided: m.unaided || o.unaided, aided: m.aided || o.aided,
    solution: m.solution || o.solution, later: m.later || o.later, wrong: m.wrong + o.wrong, hints: m.hints + o.hints, labs: m.labs + o.labs }), { opened: false, attempts: 0, unaided: false, aided: false, solution: false, later: false, wrong: 0, hints: 0, labs: 0 });
  const byName = {}; Object.keys(C.kcs).forEach(k => (byName[kcName(k)] = byName[kcName(k)] || []).push(k));
  const row = (name, ks) => { const o = merge(ks); const touched = o.opened || o.attempts || o.labs || o.solution; const w = statusWords(touched ? o : null); const s = sectionOfKc(ks[0]);
    const item = C.items.find(i => i.kc_ids.some(k => ks.includes(k)));
    const next = !o.opened ? ['Lesen', s ? '#/lernen/' + s.id : null] : !(o.unaided || o.aided) ? (item ? ['Üben', '#/ueben/' + item.id] : null) : o.unaided && !o.later ? ['Später wiederholen', '#/material'] : null;
    return [el('li', { class: 'kc-row' }, el('div', { class: 'kc-name' }, name), el('ul', { class: 'chips' }, w.map(x => el('li', { class: 'chip' + (/ohne Hilfe|später/.test(x) ? ' chip-ok' : /noch nicht/.test(x) ? ' chip-open' : '') }, x))), next && next[1] ? el('a', { class: 'btn btn-small', href: next[1] }, next[0]) : el('span')), o]; };
  const groups = C.sections.map(sec => { const names = [...new Set(sec.kc_ids.map(kcName))]; const rs = names.map(n => row(n, byName[n]));
    const done = rs.filter(([, o]) => o.unaided || o.aided).length;
    return el('section', { class: 'kc-group' }, el('div', { class: 'kc-group-h' }, el('h2', {}, el('a', { href: '#/lernen/' + sec.id }, sec.no + ' ' + sec.title)), el('span', { class: 'muted' }, `${done} von ${rs.length} Lernzielen mit richtiger Lösung`)), el('ul', { class: 'kc-list' }, rs.map(([li]) => li))); });
  const rows = groups;
  const exp = el('button', { class: 'btn', onclick: () => download(`lernhistorie-${C.chapter.id || 'kapitel'}-${today()}.json`, JSON.stringify(Store.exportObj(), null, 1)) }, 'Lernhistorie exportieren');
  const file = el('input', { type: 'file', accept: 'application/json,.json', class: 'sr', id: 'imp', onchange: e => { const f = e.target.files[0]; if (!f) return; if (f.size > 5e6) { toast('Datei zu groß.'); return; } f.text().then(t => { try { const [n, m] = Store.importObj(JSON.parse(t)); toast(`${n} Ereignisse und ${m} Lab-Einträge übernommen; vorhandene bleiben erhalten.`); route(); } catch (err) { toast('Import abgelehnt: ' + err.message); } }); } });
  const imp = el('label', { class: 'btn', for: 'imp' }, 'Lernhistorie importieren');
  const del = el('button', { class: 'btn btn-danger', onclick: () => { if (prompt('Zum Löschen des gesamten Lernstands in diesem Browser bitte LÖSCHEN eintippen.') === 'LÖSCHEN') { Store.clear(); toast('Lernstand gelöscht.'); route(); } } }, 'Lernstand löschen');
  const log = el('details', { class: 'log' }, el('summary', {}, `Protokoll aller Ereignisse (${ev.length} Einträge)`), el('ol', {}, ev.slice(-200).reverse().map(e => el('li', {}, `${e.t.slice(0, 16).replace('T', ' ')} · ${({ section_open: 'Abschnitt geöffnet', attempt: 'Antwort geprüft', hint: 'Hinweis angesehen', solution: 'Musterlösung angesehen', card: 'Kurzabfrage', lab: 'Simulation', exam_start: 'Klausur begonnen', exam_submit: 'Klausur abgegeben', exam_self_score: 'Selbstbewertung', note: 'Antwort festgehalten' })[e.type] || 'Ereignis'}${e.item ? ' · Aufgabe ' + e.item : ''}${e.section && S[e.section] ? ' · ' + S[e.section].title : ''}${e.lab ? ' · ' + (e.task === 'predict' ? 'Vorhersage' : String(e.task).startsWith('mission:') ? 'Erkundungsauftrag' : e.task === 'explain' || e.task === 'summary' ? 'eigene Erklärung' : 'Aufgabe') : ''}${e.result ? ' · ' + e.result : ''}${e.ev ? ' · ' + e.ev : ''}`))));
  setContext(null);
  return [el('div', { class: 'eyebrow' }, 'Lernstand'), el('h1', {}, 'Was Sie bisher bearbeitet haben'),
    el('p', { class: 'lede' }, 'Nur beobachtete Ereignisse in diesem Browser. Eine richtige Antwort zeigt, dass Sie die Aufgabe heute lösen konnten – nicht, dass Sie es dauerhaft behalten. Dafür sind die Anki-Karten da.'),
    ...rows, ...trackRows(), el('section', { class: 'panel' }, el('h2', {}, 'Sichern und übertragen'), el('p', { class: 'muted' }, 'Der Lernstand liegt nur in diesem Browser (localStorage). Exportieren Sie ihn, um ihn zu sichern oder auf ein anderes Gerät zu übertragen.'), el('div', { class: 'row' }, exp, imp, file, del)), log];
}

function briefing(sec, itemId) {
  const ev = Store.all(); const it = itemId ? I[itemId] : null; const s = sec || (it && it.section ? S[it.section] : null);
  const rel = ev.filter(e => (it && e.item === it.id) || (s && e.section === s.id) || (it && e.type === 'lab' && e.kc_ids.some(k => it.kc_ids.includes(k))));
  const hints = rel.filter(e => e.type === 'hint').length, wrong = rel.filter(e => e.type === 'attempt' && e.result !== 'correct').length, solv = rel.some(e => e.type === 'solution');
  const strip = h => (new DOMParser().parseFromString(h, 'text/html').body.textContent || '').replace(/\s+/g, ' ').trim();
  const L_ = [`# Tutor-Briefing (Exam Mastery)`, '', `Kurs: ${C.course}`, `Kapitel ${C.chapter.no}: ${C.chapter.title}`];
  if (s) L_.push(`Abschnitt ${s.no}: ${s.title}`, '', 'Lernziele:', ...uniqNames(s.kc_ids).map(k => `- ${kcName(k)}`), '', 'Quellen der Vorlesung:', ...(s.sources.length ? s.sources.map(x => `- ${x}`) : ['- (keine Angabe)']));
  if (it) L_.push('', `Offene Aufgabe (${it.stage}${it.points ? ', ' + it.points + ' P.' : ''}):`, strip(it.prompt));
  L_.push('', 'Beobachtet (nur dieser Browser):', `- Hinweise genutzt: ${hints}`, `- nicht richtige Versuche: ${wrong}`, `- Musterlösung angesehen: ${solv ? 'ja' : 'nein'}`,
    '', 'Bitte an den Tutor:', '- Erkläre nur so viel, wie ich zum nächsten eigenen Schritt brauche; frage zuerst, wie ich vorgehen würde.', '- Stütze dich auf die genannten Quellen der Vorlesung; kennzeichne alles, was darüber hinausgeht.', '- Keine fertige Lösung, solange ich nicht darum bitte.');
  return L_.join('\n');
}
function viewTutor(id) {
  const sec = S[id] || null; const item = I[id] || null;
  const last = [...Store.load().events].reverse().find(e => e.type === 'section_open');
  const s = sec || (item ? null : (last ? S[last.section] : C.sections[0]));
  const text = briefing(s, item ? item.id : null);
  const ta = el('textarea', { class: 'brief', rows: 16, readonly: true, 'aria-label': 'Tutor-Briefing' }); ta.value = text;
  const logTutor = () => { if (item) Store.add({ type: 'tutor', item: item.id }); };
  const copy = el('button', { class: 'btn btn-primary', onclick: () => { logTutor(); const done = () => toast('Briefing kopiert.'); if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(text).then(done, () => { ta.select(); document.execCommand('copy'); done(); }); else { ta.select(); document.execCommand('copy'); done(); } } }, 'Briefing kopieren');
  const dl = el('button', { class: 'btn', onclick: () => { logTutor(); download('tutor-briefing.md', text, 'text/markdown'); } }, 'Als Datei speichern');
  const pick = el('select', { 'aria-label': 'Abschnitt wählen', onchange: e => { location.hash = '#/tutor/' + e.target.value; } }, C.sections.map(x => el('option', { value: x.id }, x.no + ' ' + x.title))); if (s) pick.value = s.id;
  setContext(s);
  return [el('div', { class: 'eyebrow' }, 'Tutor'), el('h1', {}, 'Tutor-Briefing'),
    el('p', { class: 'lede' }, 'Diese Seite hat keine Live-Verbindung zu einer KI. Sie bereitet den Kontext für ein Gespräch mit Ihrem Tutor vor: Abschnitt, Lernziele, Quellen, offene Aufgabe und was Sie bereits versucht haben.'),
    el('div', { class: 'tutor-modes' },
      el('div', { class: 'tm tm-local' }, el('h2', {}, 'Funktioniert hier, ohne Verbindung'), el('ul', {}, el('li', {}, 'Briefing zum gewählten Abschnitt zusammenstellen'), el('li', {}, 'Ihre beobachteten Versuche einbeziehen'), el('li', {}, 'Kopieren oder als Datei speichern'))),
      el('div', { class: 'tm tm-agent' }, el('h2', {}, 'Braucht einen Agenten (z. B. Claude Code)'), el('ul', {}, el('li', {}, 'Rückfragen beantworten und erklären'), el('li', {}, 'Ihre eigene Lösung kommentieren'), el('li', {}, 'Neue Übungsvarianten erzeugen')))),
    el('div', { class: 'filters' }, pick), ta,
    item ? el('p', { class: 'muted', 'data-tutor-note': '' }, 'Wenn Sie dieses Briefing nutzen, zählt eine spätere richtige Lösung dieser Aufgabe im Lernstand als „mit Hilfe richtig“.') : null,
    el('div', { class: 'row' }, copy, dl),
    el('section', { class: 'panel' }, el('h2', {}, 'So verwenden Sie das Briefing'), el('ol', {}, el('li', {}, 'Briefing kopieren.'), el('li', {}, 'In Claude Code im Kursordner einfügen, zum Beispiel nach „/exam-mastery lernen“.'), el('li', {}, 'Ohne KI: Hinweise und Musterlösungen der Übungen sowie die Quellenangaben im Text helfen ebenso.')),
      el('p', { class: 'muted' }, 'Nichts wird automatisch übertragen. Das Briefing enthält keine Namen, nur Kursinhalte und Ihre beobachteten Versuche zu diesem Abschnitt.'))];
}

function viewMaterial() {
  setContext(null);
  const labs = C.labs.map(l => el('li', {}, el('a', { href: l.href }, l.title), el('span', { class: 'muted' }, ' – ' + uniqNames(l.kc_ids).map(kcName).join(' · '))));
  return [el('div', { class: 'eyebrow' }, 'Material'), el('h1', {}, 'Dokumente und Exporte'),
    el('ul', { class: 'docs' }, C.materials.map(([t, h]) => el('li', {}, el('a', { class: 'doc', href: h }, el('span', { class: 'doc-t' }, t), el('span', { class: 'muted' }, h.split('/').pop()))))),
    C.anki ? el('section', { class: 'panel' }, el('h2', {}, 'Anki'), el('p', {}, 'Für das langfristige Behalten: Karten in Anki importieren (Datei → Importieren). Exam Mastery plant keine Wiederholungen selbst.'), el('a', { class: 'btn', href: C.anki }, 'Anki-Paket herunterladen')) : null,
    labs.length ? el('section', { class: 'panel' }, el('h2', {}, 'Simulationen einzeln öffnen'), el('ul', { class: 'plain' }, labs)) : null,
    el('section', { class: 'panel' }, el('h2', {}, 'Lernhistorie'), el('a', { class: 'btn', href: '#/stand' }, 'Exportieren oder importieren'))];
}

/* ------------------------------------------------------------ router */
function parse() { const [, mode, id] = (location.hash || '#/start').split('/'); return { mode: MODES.some(m => m[0] === mode) ? mode : 'start', id: id ? decodeURIComponent(id) : null }; }
function route() {
  const r = parse(); toggleSide(false); renderNav(r);
  const v = { start: viewStart, lernen: () => viewSection(r.id || (C.sections[0] || {}).id), ueben: () => viewPractice(r.id), klausur: viewExam, stand: viewProgress, tutor: () => viewTutor(r.id), material: viewMaterial }[r.mode];
  if (r.mode === 'start') setContext(null);
  document.body.classList.toggle('exam-focus', r.mode === 'klausur' && !!Store.pref('examStart'));
  document.body.classList.toggle('no-ctx', r.mode !== 'lernen' && !(r.mode === 'ueben' && r.id) && r.mode !== 'tutor');
  main.replaceChildren(...v().filter(Boolean)); main.scrollTop = 0; window.scrollTo(0, 0);
  if (routed) main.focus({ preventScroll: true }); routed = true;   /* focus follows navigation, not the initial load */
  typeset(main);
  document.title = (MODES.find(m => m[0] === r.mode) || [, ''])[1] + ' · ' + C.chapter.title;
  app.dataset.ready = '1';
}
shell(); window.addEventListener('hashchange', route); route();
window.EMApp = { Store, observations, briefing };
})();
