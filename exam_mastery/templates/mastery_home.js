/* Mastery V1 home: start / continue / study. Reads library.json and the learner state of this origin (localStorage).
   Decisions come from the tested runtime (assets/em_tutor.js: EMT.decide, EMT.kcStatus, EMT.kcEvidenceBasis); this file
   only orders them (rules M1-M3) and never computes a score. No network beyond this local server. */
(() => {
'use strict';
const EMT = window.EMT;
const TKEY = 'em-tutor-v1', PKEY = 'em-practice-v1';
const app = document.getElementById('app');
const el = (tag, attrs, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (v === null || v === undefined || v === false) continue; if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); } for (const c of kids.flat()) if (c !== null && c !== undefined && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c))); return e; };
const readJSON = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
const writeJSON = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
const when = t => { const d = new Date(t); return Number.isFinite(d.getTime()) ? d.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' }) : '–'; };
const STATUS = { NOT_ASSESSED: 'noch nicht geprüft', INDEPENDENT_PARTIAL: 'begonnen, noch nicht gelöst', ASSISTED: 'mit Hilfe gelöst', INDEPENDENT_PASS: 'heute ohne Hilfe gelöst', RETEST_DUE: 'spätere Prüfung fällig', RETAINED_ON_LATER_DAY: 'an einem späteren Tag erneut ohne Hilfe gelöst' };
const BASIS = { none: 'keine selbstständige richtige Lösung', recognition_only: 'nur Wiedererkennen (Auswahl) geprüft', production: 'selbst erzeugte Lösung geprüft' };
const PRODUCTS = [['interactive', 'Interaktiv', 'Erklären, vorhersagen, experimentieren, üben – im Browser'], ['textbook', 'Lehrbuch (PDF)', 'Herleitungen und Erklärungen zum Lesen'], ['workbook', 'Arbeitsbuch (PDF)', 'Aufgaben mit Lösungen zum Ausdrucken'], ['anki', 'Anki-Paket', 'Karten für Anki – Anki plant die Wiederholung']];
const HELP = ['hint', 'solution', 'tutor'];

/* ------------------------------------------------------------ learner state of this origin */
const workbenchEvents = tr => (((readJSON(TKEY) || {}).tracks || {})[tr.store_key] || { events: [] }).events.filter(e => e.type !== 'decision');
function practiceRecord(u) {
  const rec = (((readJSON(PKEY) || {}).units) || {})[u.practice_store.unit_id];
  return rec && rec.assessment_revision === u.practice_store.assessment_revision ? rec : { events: [], policy: [] };
}
/* Explorable free text is never graded: only verified attempts may change a competency state (unverified ones are counted). */
const verifiedOnly = ev => ev.filter(e => e.type !== 'attempt' || (e.diagnosis && e.diagnosis.result !== 'unverified'));

function kcRows(tr, ev, labels, source, extraUnverified) {
  const T = Object.fromEntries(tr.tasks.map(t => [t.id, t]));
  const usable = source === 'explorable' ? verifiedOnly(ev) : ev;
  const st = EMT.kcStatus(tr, usable), basis = EMT.kcEvidenceBasis(tr, usable);
  return tr.kcs.map(kc => {
    let assisted = 0, unassisted = 0, unverified = 0, helps = 0;
    ev.forEach((e, i) => {
      const task = T[e.task]; if (!task || task.kc_id !== kc.id) return;
      if (HELP.includes(e.type)) { helps++; return; }
      if (e.type !== 'attempt' || !e.diagnosis || e.diagnosis.result === 'invalid') return;
      if (e.diagnosis.result === 'unverified') unverified++;
      if (EMT.assisted(tr, ev, i)) assisted++; else unassisted++;
    });
    return { id: kc.id, label: labels[kc.id] || kc.label || kc.id, status: st[kc.id], basis: basis[kc.id], assisted, unassisted, unverified, helps, source };
  });
}

/* ------------------------------------------------------------ rules M1-M3 (ordering only; decisions are EMT.decide) */
function recommend(lib) {
  for (const u of lib.units) {
    for (const tr of u.tracks.filter(t => t.relation === 'prerequisite')) {
      const ev = workbenchEvents(tr), st = EMT.kcStatus(tr.data, ev), d = EMT.decide(tr.data, ev);
      const open = Object.values(st).some(s => !['INDEPENDENT_PASS', 'RETEST_DUE', 'RETAINED_ON_LATER_DAY'].includes(s));
      const task = d.next_task && tr.data.tasks.find(t => t.id === d.next_task);
      if (open && task && task.role !== 'retest') return { rule: 'M1', engine_rule: d.rule, href: tr.href, title: tr.label, task: task.title,
        why: 'Die Voraussetzung (Übungsstrecke) ist noch nicht ohne Hilfe gelöst. Die Übungsstrecke prüft regelbasiert und wählt die nächste Aufgabe selbst.', rationale: d.rationale };
    }
    const rec = practiceRecord(u), d = EMT.decide(u.adaptive_track, rec.policy);
    const tried = new Set(rec.policy.filter(e => e.type === 'attempt').map(e => e.task));
    let next = d.next_task && !tried.has(d.next_task) ? d.next_task : null, rule = d.rule;
    if (!next) { const open = u.adaptive_track.flow.find(id => !tried.has(id)); if (open) { next = open; rule = 'M2-Reihenfolge'; } }
    if (next) { const a = u.assessments.find(x => x.id === next); return { rule: 'M2', engine_rule: rule, href: u.products.interactive + '#' + a.anchor, title: u.title, task: a.title,
      why: 'Voraussetzung gelöst; weiter im Explorable mit der nächsten noch nicht bearbeiteten Aufgabe. Freitext wird nicht automatisch bewertet – vergleichen Sie danach selbst mit der Musterlösung.', rationale: d.rationale }; }
  }
  return { rule: 'M3', engine_rule: 'RE', href: '#lernstand', title: 'Lernstand', task: 'Alle Aufgaben einmal bearbeitet',
    why: 'Alles einmal bearbeitet. Behalten zeigt erst ein späterer Abruf: Anki-Karten wiederholen; fällige Prüfaufgaben stehen unten (nur zur Information).', rationale: '' };
}

function lastActivity(lib) {
  let best = null;
  for (const u of lib.units) {
    for (const tr of u.tracks) for (const e of workbenchEvents(tr)) if (!best || e.t > best.t) {
      const task = tr.data.tasks.find(t => t.id === e.task); best = { t: e.t, where: tr.label, task: task ? task.title : e.task, href: tr.href, type: e.type };
    }
    for (const e of practiceRecord(u).policy) if (!best || e.t > best.t) {
      const a = u.assessments.find(x => x.id === e.task); best = { t: e.t, where: u.title + ' (Interaktiv)', task: a ? a.title : e.task, href: u.products.interactive + (a ? '#' + a.anchor : ''), type: e.type };
    }
  }
  return best;
}

function dueRetests(lib) {
  const out = [];
  for (const u of lib.units) for (const tr of u.tracks) {
    const st = EMT.kcStatus(tr.data, workbenchEvents(tr));
    for (const kc of tr.data.kcs) if (st[kc.id] === 'RETEST_DUE') {
      const task = tr.data.tasks.find(t => t.role === 'retest' && t.kc_id === kc.id) || tr.data.tasks.find(t => t.role === 'retest');
      out.push({ kc: kc.label, task: task ? task.title : null, href: tr.href, where: tr.label });
    }
  }
  return out;
}

/* ------------------------------------------------------------ views */
const ACT = { attempt: 'Versuch', hint: 'Hinweis', solution: 'Lösung angesehen', tutor: 'Tutor-Brief' };
function viewStart(lib) {
  const last = lastActivity(lib), rec = recommend(lib), due = dueRetests(lib);
  const s = el('section', { id: 'start', class: 'm-view', 'aria-labelledby': 'h-start' }, el('h1', { id: 'h-start', class: 'm-h1' }, 'Mastery'),
    el('p', { class: 'm-lead' }, 'Ihre lokale Lernumgebung: eine Einheit, vier Produkte, eine Übungsstrecke, ein Tutor-Brief und ein ehrlicher Lernstand. Alles offline auf diesem Rechner.'));
  s.append(el('div', { class: 'm-grid2' },
    el('article', { class: 'm-card', id: 'continue' }, el('p', { class: 'ds-eyebrow' }, 'Weiter, wo Sie aufgehört haben'),
      last ? [el('h2', { class: 'm-h2' }, last.where), el('p', {}, (ACT[last.type] || last.type) + ' · ' + last.task), el('p', { class: 'm-note' }, when(last.t)),
        el('a', { class: 'ds-btn ds-btn-primary', href: last.href, id: 'continue-link' }, 'Weitermachen')]
        : [el('h2', { class: 'm-h2' }, 'Noch nichts bearbeitet'), el('p', {}, 'Beginnen Sie mit dem empfohlenen nächsten Schritt.')]),
    el('article', { class: 'm-card m-accent', id: 'next', 'data-rule': rec.rule, 'data-engine-rule': rec.engine_rule }, el('p', { class: 'ds-eyebrow' }, 'Nächster empfohlener Schritt'),
      el('h2', { class: 'm-h2' }, rec.task), el('p', {}, rec.title), el('p', { class: 'm-note' }, rec.why),
      el('p', { class: 'm-rule' }, 'Regel ', el('code', {}, rec.rule), ' · Engine-Regel ', el('code', {}, rec.engine_rule), rec.rationale ? ' – ' + rec.rationale : ''),
      el('a', { class: 'ds-btn ds-btn-primary', href: rec.href, id: 'next-link' }, 'Öffnen'))));
  for (const u of lib.units) {
    const card = el('article', { class: 'm-card m-unit', 'data-unit': u.slug },
      el('p', { class: 'ds-eyebrow' }, u.private ? 'Private Einheit (nur auf diesem Rechner)' : 'Einheit'), el('h2', { class: 'm-h2' }, u.title),
      el('p', { class: 'm-badge' }, u.source_mode === 'synthetic' ? 'Synthetische Referenzeinheit' : 'Quellengebundene Einheit', ' · fachliche Prüfung durch Menschen ausstehend'));
    card.append(el('ul', { class: 'm-products' }, PRODUCTS.map(([k, label, note]) => el('li', {},
      el('a', { href: u.products[k], 'data-product': k, download: k === 'anki' ? 'Anki.apkg' : null }, label), el('small', {}, note)))));
    card.append(el('h3', { class: 'm-h3' }, 'Üben mit Rückmeldung'), el('ul', { class: 'm-products' }, u.tracks.map(tr => el('li', {},
      el('a', { href: tr.href, 'data-product': 'workbench' }, tr.label), el('small', {}, 'Regelbasierte Prüfung von Zahlen, Ausdrücken und Rechenschritten; Hinweise; Tutor-Brief.')))));
    s.append(card);
  }
  s.append(el('article', { class: 'm-card', id: 'due' }, el('p', { class: 'ds-eyebrow' }, 'Fällige spätere Prüfungen (nur zur Information)'),
    due.length ? el('ul', {}, due.map(d => el('li', { 'data-due': d.kc }, d.kc + (d.task ? ' – Prüfaufgabe „' + d.task + '“' : '') + ' in ', el('a', { href: d.href }, d.where))))
      : el('p', {}, 'Keine. Eine Prüfaufgabe wird frühestens 20 Stunden nach einer selbstständigen Lösung fällig.'),
    el('p', { class: 'm-note' }, 'Mastery erinnert nicht und plant keine Wiederholungen. Die Wiederholung plant allein Anki (FSRS).')));
  s.append(ankiCard(lib), limitsCard());
  return s;
}

function ankiCard(lib) {
  const box = el('article', { class: 'm-card', id: 'anki' }, el('p', { class: 'ds-eyebrow' }, 'Anki'), el('h2', { class: 'm-h2' }, 'Karten importieren – sicher'));
  for (const u of lib.units) {
    const changed = el('div', { class: 'm-anki-report', 'data-unit': u.slug }, el('p', { class: 'm-note' }, 'Änderungsbericht wird geladen …'));
    box.append(el('p', {}, el('a', { class: 'ds-btn', href: u.products.anki, download: 'Anki.apkg', 'data-product': 'anki' }, 'Anki.apkg herunterladen'), ' ', u.anki.deck, ' · ', String(u.anki.notes), ' Notizen'), changed);
    fetch(u.anki.report, { cache: 'no-store' }).then(r => r.json()).then(rep => {
      const last = (rep.history || []).slice(-1)[0];
      changed.replaceChildren(...[
        el('p', { 'data-restamped': String(rep.restamped.length) }, rep.restamped.length ? 'Letzte Erstellung: ' + rep.restamped.length + ' Notiz(en) neu oder geändert – nur diese aktualisiert der Import.' : 'Letzte Erstellung: keine Notiz geändert – ein erneuter Import ändert nichts.'),
        last ? el('details', {}, el('summary', {}, 'Zuletzt geänderte Notizen (' + when(last.built_at) + ')'), el('ul', {}, last.restamped.slice(0, 40).map(k => el('li', {}, el('code', {}, k))))) : null,
        rep.update_delta.retirement_candidates.length ? el('p', { class: 'm-note' }, rep.update_delta.retirement_candidates.length + ' Notiz(en) gibt es nicht mehr; Anki löscht sie beim Import nicht – bei Bedarf selbst löschen.') : null].filter(Boolean));
    }).catch(() => changed.replaceChildren(el('p', { class: 'm-note' }, 'Kein Änderungsbericht gefunden.')));
  }
  box.append(el('ol', { class: 'm-steps' },
    el('li', {}, 'Anki am Computer öffnen (vorher synchronisieren, falls Sie AnkiWeb nutzen).'),
    el('li', {}, 'Datei → Importieren … → die heruntergeladene Anki.apkg wählen.'),
    el('li', {}, 'Im Importdialog die Voreinstellungen lassen: Notizen aktualisieren „falls neuer“, Notiztypen aktualisieren „falls neuer“. Nichts auf „immer“ stellen.'),
    el('li', {}, 'Importieren. Ihre Wiederholungshistorie und Fälligkeiten bleiben erhalten: Das Paket enthält keine Planungsdaten, Karten werden über stabile IDs wiedererkannt, unveränderte Notizen bleiben unberührt.'),
    el('li', {}, 'Wiederholen in Anki. Mastery plant nichts selbst.')),
    el('p', { class: 'm-note' }, 'Geprüft wurde der Import automatisch gegen eine Wegwerf-Sammlung (Anki 26.9.3, Python-Bibliothek), nicht in der Desktop-App oder auf dem Handy.'));
  return box;
}

function limitsCard() {
  return el('article', { class: 'm-card m-limits', id: 'limits' }, el('p', { class: 'ds-eyebrow' }, 'Ehrliche Grenzen'), el('ul', {},
    el('li', {}, 'Ob Mastery Lernen verbessert, ist nicht gemessen (Lernwirkungsstudie: NOT_RUN). Zustände hier sind Näherungsanzeigen im Produkt.'),
    el('li', {}, 'Die Attention-Einheit ist fachlich nicht unabhängig geprüft; Zahlen sind synthetisch. Quellen stehen im Explorable.'),
    el('li', {}, 'Freitext wird nicht bewertet. Regelbasiert geprüft werden nur Zahlen, Ausdrücke und Rechenschritte der Übungsstrecke.'),
    el('li', {}, 'Ein Lernender, ein Browser: Der Lernstand liegt im Browser dieser Adresse (Port 8765). Anderer Browser oder Port = anderer Lernstand. Regelmäßig sichern.'),
    el('li', {}, 'Nicht getestet: Handy/Tablet, Screenreader im Detail, Import in die Anki-Desktop-App.'),
    el('li', {}, 'Der Tutor ist kein Live-Tutor: Mastery kopiert nur einen Brief. Was Claude oder ChatGPT antworten, prüft Mastery nicht.')));
}

function viewProgress(lib) {
  const s = el('section', { id: 'lernstand', class: 'm-view', 'aria-labelledby': 'h-ls' }, el('h1', { id: 'h-ls', class: 'm-h1' }, 'Lernstand'),
    el('p', { class: 'm-statement', id: 'proximal' }, 'Diese Zustände sind Näherungsanzeigen innerhalb von Mastery – beobachtete Lernhandlungen in diesem Browser, keine Messung von Lernen oder Können. Es gibt bewusst keinen Prozentwert. „Mit Hilfe“ heißt: Hinweis, Lösung oder Tutor-Brief zu dieser Aufgabe oder (bis 20 Stunden davor) zur selben Kompetenz. Behalten wird nur aus selbstständigen richtigen Lösungen mit mindestens 20 Stunden Abstand abgeleitet.'));
  const table = (title, rows, note) => el('div', { class: 'm-card' }, el('h2', { class: 'm-h2' }, title), note ? el('p', { class: 'm-note' }, note) : null,
    el('div', { class: 'm-scroll' }, el('table', { class: 'm-table' }, el('thead', {}, el('tr', {}, ['Kompetenz', 'Zustand', 'Evidenzbasis', 'ohne Hilfe', 'mit Hilfe', 'davon Freitext (unbewertet)', 'Hilfen'].map(h => el('th', { scope: 'col' }, h)))),
      el('tbody', {}, rows.map(r => el('tr', { 'data-kc': r.id, 'data-source': r.source, 'data-status': r.status, 'data-basis': r.basis, 'data-assisted': String(r.assisted), 'data-unassisted': String(r.unassisted), 'data-unverified': String(r.unverified) },
        el('th', { scope: 'row' }, r.label), el('td', {}, STATUS[r.status] || r.status), el('td', {}, BASIS[r.basis] || r.basis), el('td', {}, String(r.unassisted)), el('td', {}, String(r.assisted)), el('td', {}, String(r.unverified)), el('td', {}, String(r.helps))))))));
  for (const u of lib.units) {
    for (const tr of u.tracks) s.append(table('Übungsstrecke: ' + tr.data.title, kcRows(tr.data, workbenchEvents(tr), {}, 'workbench'), 'Regelbasiert geprüft (Zahl, Ausdruck, Rechenschritte).'));
    const labels = Object.fromEntries(u.competencies.map(c => [c.id, c.label]));
    s.append(table('Interaktiv: ' + u.title, kcRows(u.adaptive_track, practiceRecord(u).policy, labels, 'explorable'),
      'Freitext wird nicht bewertet: Versuche zählen als „ohne/mit Hilfe“, ändern aber keinen Zustand. Zuordnung über die erste Kompetenz der Aufgabe.'));
  }
  return s;
}

function viewTutor(lib) {
  return el('section', { id: 'tutor', class: 'm-view', 'aria-labelledby': 'h-tu' }, el('h1', { id: 'h-tu', class: 'm-h1' }, 'Tutor'),
    el('div', { class: 'm-card' }, el('p', {}, 'Bei jeder Aufgabe – in der Übungsstrecke und im Explorable (nach einem eigenen Versuch) – gibt es „Tutor-Brief kopieren“. Der Brief enthält die verbindlichen Tutor-Regeln (R9), die Aufgabe, Ihre Versuche, genutzte Hinweise, die Quellen und Ihre Frage. Fügen Sie ihn in Claude oder ChatGPT ein; erst dann verlässt er den Rechner.'),
      el('ul', {}, el('li', {}, 'Bei Nachweisaufgaben (ähnliche Aufgabe ohne Hinweise, Transfer, spätere Prüfung) enthält der Brief keine Musterlösung.'),
        el('li', {}, 'Ein Tutor-Brief zählt als Hilfe: Die Aufgabe gilt danach als „mit Hilfe“ bearbeitet. Die Lösung zu sehen bleibt Ihre Entscheidung und wird ebenso vermerkt.'),
        el('li', {}, 'Urteile des Tutors über Freitext sind Modelleinschätzungen, keine Korrektur.')),
      el('ul', { class: 'm-products' }, lib.units.flatMap(u => [el('li', {}, el('a', { href: u.products.interactive }, 'Explorable: ' + u.title)), ...u.tracks.map(tr => el('li', {}, el('a', { href: tr.href }, 'Übungsstrecke: ' + tr.label)))]))));
}

/* ------------------------------------------------------------ backup: file export/import and local server copy */
function snapshot() { return { schema: 'mastery-state-v1', saved_at: new Date().toISOString(), origin: location.origin, storage: { [TKEY]: readJSON(TKEY), [PKEY]: readJSON(PKEY) } }; }
function mergeState(o) {
  if (!o || o.schema !== 'mastery-state-v1' || !o.storage) throw new Error('Keine Mastery-Sicherung (mastery-state-v1).');
  let n = 0; const key = (e, a, b) => [e[a], e.type, e[b] || ''].join('|');
  const merge = (cur, add, a, b) => { const have = new Set(cur.map(e => key(e, a, b))); for (const e of add || []) if (e && typeof e === 'object' && typeof e[a] === 'string' && typeof e.type === 'string' && Date.parse(e[a]) <= Date.now() + 3e5 && !have.has(key(e, a, b))) { cur.push(e); have.add(key(e, a, b)); n++; } cur.sort((x, y) => x[a] < y[a] ? -1 : x[a] > y[a] ? 1 : 0); };
  const t = o.storage[TKEY]; if (t && t.schema === 1 && t.tracks) { const d = readJSON(TKEY) || { schema: 1, tracks: {} }; for (const [k, r] of Object.entries(t.tracks)) { const c = (d.tracks[k] = d.tracks[k] || { events: [] }); merge(c.events, r.events, 't', 'task'); } writeJSON(TKEY, d); }
  const p = o.storage[PKEY]; if (p && p.schema === 1 && p.units) { const d = readJSON(PKEY) || { schema: 1, units: {} }; d.units = d.units || {};
    for (const [k, r] of Object.entries(p.units)) { const c = d.units[k]; if (!c) { d.units[k] = { assessment_revision: r.assessment_revision, events: [], policy: [] }; }
      const cur = d.units[k]; if (cur.assessment_revision !== r.assessment_revision) { (d.archived = d.archived || {})[k + '@' + r.assessment_revision] = r; continue; }
      merge(cur.events, r.events, 'at', 'task_id'); merge(cur.policy, r.policy, 't', 'task'); }
    writeJSON(PKEY, d); }
  return n;
}
function postState(msg) {
  const body = JSON.stringify(snapshot());
  return fetch('api/state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, cache: 'no-store' })
    .then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)))
    .then(r => { if (msg) { msg.textContent = 'Am lokalen Server gesichert: ' + when(r.received_at) + '.'; msg.dataset.saved = r.received_at; } return r; })
    .catch(e => { if (msg) msg.textContent = 'Server-Sicherung nicht möglich (' + e.message + '). Datei-Sicherung nutzen.'; });
}
function viewBackup() {
  const msg = el('p', { class: 'm-note', role: 'status', id: 'backup-status' }, 'Noch keine Sicherung in dieser Sitzung.');
  const file = el('input', { type: 'file', accept: '.json,application/json', id: 'backup-import', class: 'ds-sr', onchange: e => { const f = e.target.files[0]; if (!f || f.size > 4e6) return;
    f.text().then(t => { const n = mergeState(JSON.parse(t)); msg.textContent = n + ' Einträge übernommen; vorhandene bleiben erhalten.'; render(); }).catch(err => { msg.textContent = 'Import abgelehnt: ' + err.message; }); } });
  return el('section', { id: 'sicherung', class: 'm-view', 'aria-labelledby': 'h-si' }, el('h1', { id: 'h-si', class: 'm-h1' }, 'Sicherung'),
    el('div', { class: 'm-card' }, el('p', {}, 'Ihr Lernstand liegt im Browser (localStorage) unter dieser Adresse. Die Startseite schickt bei jedem Öffnen eine geprüfte Kopie an den lokalen Mastery-Server (Ordner state/ in Ihrer Bibliothek); `mastery export` schreibt daraus eine Sicherungsdatei. Nichts verlässt den Rechner.'),
      el('div', { class: 'm-row' },
        el('button', { type: 'button', class: 'ds-btn ds-btn-primary', id: 'backup-server', onclick: () => postState(msg) }, 'Jetzt am Server sichern'),
        el('button', { type: 'button', class: 'ds-btn', id: 'backup-export', onclick: () => { const a = el('a', { href: URL.createObjectURL(new Blob([JSON.stringify(snapshot(), null, 1)], { type: 'application/json' })), download: 'mastery-lernstand-' + new Date().toISOString().slice(0, 10) + '.json' }); document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); } }, 'Als Datei exportieren'),
        el('label', { class: 'ds-btn', for: 'backup-import' }, 'Datei importieren'), file), msg,
      el('p', { class: 'm-note' }, 'Die Sicherung enthält Ihre eigenen Antworten und Diagnosen. Import ergänzt nur; vorhandene Einträge bleiben. Aufgaben in geänderter Fassung übernehmen keinen alten Verlauf.')));
}

/* ------------------------------------------------------------ boot */
let LIB = null;
function route() { const id = (location.hash || '#start').slice(1); for (const v of app.querySelectorAll('.m-view')) v.hidden = v.id !== (['start', 'lernstand', 'tutor', 'sicherung'].includes(id) ? id : 'start');
  for (const a of document.querySelectorAll('.m-nav a')) a.setAttribute('aria-current', a.getAttribute('href') === '#' + id ? 'page' : 'false'); }
function render() { app.replaceChildren(viewStart(LIB), viewProgress(LIB), viewTutor(LIB), viewBackup()); route(); app.dataset.ready = '1'; }
window.addEventListener('hashchange', route);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && LIB) { render(); postState(document.getElementById('backup-status')); } });
fetch('library.json', { cache: 'no-store' }).then(r => r.json()).then(async lib => {
  for (const u of lib.units) for (const tr of u.tracks) tr.data = await fetch(tr.json, { cache: 'no-store' }).then(r => r.json());
  LIB = lib; render(); postState(document.getElementById('backup-status'));
}).catch(e => { app.replaceChildren(el('p', { class: 'm-card' }, 'Bibliothek nicht lesbar (' + e.message + '). Bitte mit `mastery start` öffnen – nicht als Datei.')); });
})();
