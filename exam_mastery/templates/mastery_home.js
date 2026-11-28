/* Mastery V1 home: start / continue / study. Reads library.json and the learner state of this origin (localStorage).
   Decisions come from the tested runtime (assets/em_tutor.js: EMT.decide, EMT.kcStatus, EMT.kcEvidenceBasis); this file
   only orders them (rules M1-M3) and never computes a score. No network beyond this local server. */
(() => {
'use strict';
const EMT = window.EMT;
const TKEY = 'em-tutor-v1', PKEY = 'em-practice-v1', MKEY = 'em-motion-v1', LKEY = 'em-learn-v2';
const app = document.getElementById('app');
const el = (tag, attrs, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (v === null || v === undefined || v === false) continue; if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); } for (const c of kids.flat()) if (c !== null && c !== undefined && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c))); return e; };
const readJSON = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
const writeJSON = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
const when = t => { const d = new Date(t); return Number.isFinite(d.getTime()) ? d.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' }) : '–'; };
const STATUS = { NOT_ASSESSED: 'noch nicht geprüft', INDEPENDENT_PARTIAL: 'begonnen, noch nicht gelöst', ASSISTED: 'mit Hilfe gelöst', INDEPENDENT_PASS: 'heute ohne Hilfe gelöst', RETEST_DUE: 'spätere Prüfung fällig', RETAINED_ON_LATER_DAY: 'an einem späteren Tag erneut ohne Hilfe gelöst' };
const BASIS = { none: 'keine selbstständige richtige Lösung', recognition_only: 'nur Wiedererkennen (Auswahl) geprüft', production: 'selbst erzeugte Lösung geprüft' };
const PRODUCTS = [['interactive', 'Interaktiv', 'Erklären, vorhersagen, experimentieren, üben – im Browser'], ['textbook', 'Lehrbuch (PDF)', 'Herleitungen und Erklärungen zum Lesen'], ['workbook', 'Arbeitsbuch (PDF)', 'Aufgaben mit Lösungen zum Ausdrucken'], ['anki', 'Anki-Paket', 'Karten für Anki – Anki plant die Wiederholung']];

/* ------------------------------------------------------------ learner state of this origin */
const workbenchEvents = tr => (((readJSON(TKEY) || {}).tracks || {})[tr.store_key] || { events: [] }).events.filter(e => e.type !== 'decision');
function practiceRecord(u) {
  const rec = (((readJSON(PKEY) || {}).units) || {})[u.practice_store.unit_id];
  return rec && rec.assessment_revision === u.practice_store.assessment_revision ? rec : { events: [], policy: [] };
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
const ACT = { attempt: 'Versuch', hint: 'Hinweis', solution: 'Lösung angesehen', tutor: 'Tutor-Brief', guided: 'Geführte Hilfe (Voraussetzung)' };
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
  let lastCourse = null;
  const ordered = lib.units.slice().sort((a, b) => (a.course ? 1 : 0) - (b.course ? 1 : 0) || String((a.course || {}).title || '').localeCompare(String((b.course || {}).title || '')) || ((a.chapter || {}).order || 0) - ((b.chapter || {}).order || 0));
  for (const u of ordered) {
    if (u.course && u.course.slug !== lastCourse) { lastCourse = u.course.slug; s.append(el('h2', { class: 'm-h2 m-course-head', 'data-course-head': u.course.slug }, 'Kurs: ' + u.course.title, ' ', el('a', { class: 'm-note', href: '#kurse' }, 'Kursübersicht'))); }
    const card = el('article', { class: 'm-card m-unit', 'data-unit': u.slug, 'data-course': u.course ? u.course.slug : null },
      el('p', { class: 'ds-eyebrow' }, u.course ? 'Kapitel ' + u.chapter.order + ' · ' + u.course.title + ' (privat, nur auf diesem Rechner)' : u.private ? 'Private Einheit (nur auf diesem Rechner)' : 'Einheit'), el('h2', { class: 'm-h2' }, u.title),
      el('p', { class: 'm-badge' }, u.source_mode === 'synthetic' ? 'Synthetische Referenzeinheit' : 'Quellengebundene Einheit', ' · fachliche Prüfung durch Menschen ausstehend'));
    card.append(el('ul', { class: 'm-products' }, PRODUCTS.map(([k, label, note]) => el('li', {},
      el('a', { href: u.products[k], 'data-product': k, download: k === 'anki' ? 'Anki.apkg' : null }, label), el('small', {}, note)))));
    if (u.tracks.length) card.append(el('h3', { class: 'm-h3' }, 'Üben mit Rückmeldung'), el('ul', { class: 'm-products' }, u.tracks.map(tr => el('li', {},
      el('a', { href: tr.href, 'data-product': 'workbench' }, tr.label), el('small', {}, 'Regelbasierte Prüfung von Zahlen, Ausdrücken und Rechenschritten; Hinweise; Tutor-Brief.')))));
    s.append(card);
  }
  if ((lib.motion_demos || []).length) s.append(el('article', { class: 'm-card', id: 'motion-demos' }, el('p', { class: 'ds-eyebrow' }, 'Mastery Motion (Demo-Szenen, synthetische Zahlen)'),
    el('h2', { class: 'm-h2' }, 'Mathematik in Bewegung'),
    el('p', { class: 'm-note' }, 'Schritt für Schritt oder an der Zeitachse ziehen; an Wendepunkten zuerst vorhersagen, dann aufdecken. Formelterme und Bildobjekte sind farbgleich gekoppelt.'),
    el('ul', { class: 'm-products' }, lib.motion_demos.map(d => el('li', {}, el('a', { href: d.href, 'data-motion': d.id }, d.title), el('small', {}, d.claim))))));
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
    el('li', {}, 'Der Tutor ist kein Live-Tutor: Mastery kopiert nur einen Brief. Was Claude oder ChatGPT antworten, prüft Mastery nicht.'),
    el('li', {}, 'Kurse: Import, Inventar, Vollständigkeit, Kapitelplan, Pakete und Bau laufen offline und ohne Modell. Das Erarbeiten eines Kapitels braucht eine Claude-Code-Sitzung (Ihr Abo) oder einen Menschen – Mastery ruft selbst kein Modell auf.')));
}

/* ------------------------------------------------------------ Lernstand: one evidence ledger, every number explains itself */
/* The ledger (assets/mastery_ledger.js, parity-tested with mastery/ledger.py) merges all learner stores of this browser.
   This view only presents it: every number is a button that names its rule, the events behind it and what it does not
   measure. No percentage, no score, no streak. */
const PRODUCT = { workbench: 'Übungsstrecke', explorable: 'Interaktiv', motion: 'Mastery Motion', chapter_app: 'Kapitel-App' };
const LKIND = { attempt: 'Versuch', prediction: 'Vorhersage', reveal: 'Aufgedeckt', mission: 'Auftrag geprüft', view: 'Abschnitt geöffnet', self_rating: 'Selbsteinschätzung (Karte)', exam: 'Probeklausur', unknown: 'unbekannter Eintrag' };
const HELPNAME = { hint: 'Hinweis', solution: 'Lösung angesehen', tutor: 'Tutor-Brief', guided: 'Geführte Hilfe', support: 'Beispiel/Kontrast gezeigt' };
const RESULT = { correct: 'richtig', incorrect: 'nicht richtig', partial: 'teilweise', invalid: 'nicht lesbar', unverified: 'unbewertet (Freitext)', wrong: 'falsch', met: 'erreicht', not_met: 'nicht erreicht', skipped_prediction: 'ohne Vorhersage' };
const SOURCE = { deterministic: 'regelbasiert', unjudged: 'nicht bewertet', self_report: 'Selbstauskunft', agent_judgement: 'Sprachmodell außerhalb von Mastery' };
const ROLE = { practice: 'Übung', evidence: 'Nachweisaufgabe', retest: 'spätere Prüfung' };
const TQ = { date_only: 'nur Datum bekannt', invalid: 'Zeitangabe unlesbar', missing: 'ohne Zeitangabe', future: 'Zeit liegt in der Zukunft – nicht gewertet' };
const NOT_GENERAL = 'Gezählt werden beobachtete Handlungen in diesem Browser. Lernwirkung ist nicht gemessen (NOT_RUN); was Sie außerhalb von Mastery können, sieht Mastery nicht.';
const WHY = {
  unassisted: ['Versuche ohne Hilfe', 'Alle geprüften oder unbewerteten Versuche dieser Kompetenz (nicht lesbare Eingaben ausgenommen), vor denen es weder zu derselben Aufgabe eine Hilfe gab noch in den 20 Stunden davor eine Hilfe zu einer Aufgabe derselben Kompetenz. Richtig oder falsch spielt hier keine Rolle.', 'Ob der Versuch richtig war; ob Sie die Aufgabe heute ohne Mastery lösen könnten.'],
  assisted: ['Versuche mit Hilfe', 'Versuche dieser Kompetenz, vor denen zur selben Aufgabe ein Hinweis, die Lösung, ein Tutor-Brief, eine geführte Hilfe oder ein automatisch gezeigtes Beispiel lag – oder in den 20 Stunden davor eine solche Hilfe zu einer Aufgabe derselben Kompetenz.', 'Wie viel die Hilfe beigetragen hat. Jede Hilfe macht den Versuch „mit Hilfe“, auch eine kleine.'],
  unverified: ['davon Freitext, unbewertet', 'Versuche, deren Antwort Freitext war. Mastery bewertet Freitext nicht; diese Versuche ändern keinen Zustand.', 'Ob die Antwort fachlich stimmt.'],
  retries: ['wiederholte Versuche', 'Versuche an einer Aufgabe, an der es vorher schon einen Versuch gab (Wiederholung derselben Aufgabe).', 'Ob die Wiederholung besser war.'],
  hint: ['Hinweise', 'Geöffnete Hinweise zu Aufgaben dieser Kompetenz (jede Stufe einzeln).', 'Ob der Hinweis verstanden wurde.'],
  solution: ['Lösung angesehen', 'Wie oft die Musterlösung einer Aufgabe dieser Kompetenz geöffnet wurde.', 'Ob die Lösung nachvollzogen wurde.'],
  tutor: ['Tutor-Briefe', 'Erstellte oder gesendete Tutor-Briefe zu Aufgaben dieser Kompetenz. Was der Tutor (ein Sprachmodell außerhalb von Mastery) antwortet, sieht Mastery nicht.', 'Inhalt und Qualität des Tutor-Gesprächs.'],
  guided: ['Geführte Hilfen', 'Geöffnete Voraussetzungs-Lektionen, Kontrollfragen dazu und Fehlstrategie-Beispiele für Aufgaben dieser Kompetenz.', 'Ob die Voraussetzung jetzt sitzt.'],
  support: ['Beispiele/Kontraste', 'Nach einer falschen Antwort automatisch gezeigte durchgerechnete Beispiele, Kontraste oder Schrittfokus für diese Kompetenz.', 'Ob das Beispiel gelesen wurde.'],
  independent: ['selbstständig richtig', 'Regelbasiert als richtig geprüfte Versuche ohne Hilfe (gleiche Regel wie oben), mit lesbarer Zeit, nicht in der Zukunft, aus der aktuellen Aufgabenfassung.', 'Behalten über die Zeit und Transfer auf neue Aufgabentypen.'],
  first_independent: ['erste selbstständige Lösung', 'Zeitpunkt des frühesten selbstständig richtigen Versuchs dieser Kompetenz.', 'Wie sicher die Lösung war.'],
  latest_independent: ['letzte selbstständige Lösung', 'Zeitpunkt des jüngsten selbstständig richtigen Versuchs dieser Kompetenz.', 'Ob Sie es heute noch können.'],
  delayed: ['späterer Nachweis', 'Erste selbstständig richtige Lösung einer anderen Aufgabe derselben Kompetenz, mindestens 20 Stunden nach einer früheren selbstständigen Lösung (echte verstrichene Zeit, keine Kalendertage). Die Stunden zählen ab der frühesten passenden Lösung.', 'Langfristiges Behalten; eine einzelne spätere Lösung ist eine Stichprobe.'],
  status: ['Zustand', 'Regel der Übungslogik (policy.kc_status, im Browser EMT.kcStatus): kein Versuch → noch nicht geprüft; nur falsch → begonnen; nur mit Hilfe richtig → mit Hilfe gelöst; selbstständig richtig → heute ohne Hilfe; ≥ 20 h danach → spätere Prüfung fällig; zwei selbstständige Lösungen verschiedener Aufgaben ≥ 20 h auseinander → an einem späteren Tag erneut gelöst.', 'Ein Zustand ist keine Note und keine Wahrscheinlichkeit, dass Sie es können.'],
  basis: ['Evidenzbasis', 'Woraus die selbstständigen Lösungen bestehen: nur Auswahl-/Ankreuzaufgaben → nur Wiedererkennen; mindestens eine selbst erzeugte Zahl, ein Ausdruck oder Rechenschritte → Produktion.', 'Ob ein Beweis oder eine Begründung selbst konstruiert werden kann (Freitext wird nicht bewertet).'],
  store_read: ['gelesene Einträge', 'Alle Einträge dieses Speichers in diesem Browser (localStorage), unverändert gelesen.', 'Einträge in anderen Browsern, auf anderen Geräten oder unter anderen Ports.'],
  store_included: ['in der Zeitleiste', 'Einträge, die als Lernhandlung in die Zeitleiste eingehen – auch unbekannte oder alte, dann gekennzeichnet.', 'Ob die Handlung lernwirksam war.'],
  store_excluded: ['ausgelassen', 'Einträge, die keine eigene Lernhandlung sind: Entscheidungen der Übungslogik (engine_decision), doppelte Einträge des Aktionsprotokolls im Explorable (mirror_duplicate, dieselbe Handlung steht im Entscheidungsprotokoll) und unlesbare Einträge (malformed).', 'Nichts davon wird gelöscht; der Speicher bleibt unverändert.'],
  coverage_with: ['mit selbst erzeugter Lösung', 'Kompetenzen dieses Kapitels, für die es mindestens eine selbstständig richtige, regelbasiert geprüfte Lösung mit Produktion (Zahl, Ausdruck, Rechenschritte) gibt – in Übungsstrecke oder Interaktiv.', 'Ob die Kompetenz vollständig beherrscht wird; eine Lösung ist eine Stichprobe.'],
  coverage_without: ['ohne selbst erzeugte Lösung', 'Kompetenzen dieses Kapitels ohne selbstständig richtige Produktion: nicht bearbeitet, nur mit Hilfe, nur Wiedererkennen oder nur unbewerteter Freitext.', 'Was Sie außerhalb von Mastery dazu schon können.'],
  motion_predictions: ['Vorhersagen', 'Abgegebene Vorhersagen vor dem Aufdecken in dieser Szene (aktuelle Szenenfassung).', 'Können: Vorhersagen sind Lernhandlungen, kein Nachweis.'],
  motion_correct: ['davon zutreffend', 'Vorhersagen, die der Szenen-Prüfer als zutreffend erkannt hat (regelbasiert).', 'Verständnis; eine Vorhersage kann geraten sein.'],
  motion_reveals: ['aufgedeckt', 'Aufgedeckte Schritte, auch ohne Vorhersage.', 'Ob der Schritt verstanden wurde.'],
  motion_missions: ['Aufträge geprüft', 'Abgegebene Regler-Aufträge dieser Szene.', 'Können außerhalb der Szene.'],
  motion_met: ['davon erreicht', 'Aufträge, deren Zielbedingung der Szenen-Prüfer als erfüllt erkannt hat.', 'Ob der Weg dorthin verstanden wurde.'],
  timeline: ['Einträge', 'Lernhandlungen in der Zeitleiste nach den gewählten Filtern.', 'Lernzeit oder Aufmerksamkeit.'],
  anki_cards: ['Karten', 'Karten aus Mastery-Stapeln („Exam Mastery::…“) in der von Ihnen exportierten Anki-Datei.', 'Karten außerhalb der Mastery-Stapel; Können.'],
  anki_reviews: ['Wiederholungen', 'Einträge der Anki-Wiederholungshistorie (revlog) zu diesen Karten mit Antwortknopf; manuelle Umplanungen nicht mitgezählt.', 'Lernerfolg. Anki-Planungsdaten sind kein Kompetenznachweis.'],
  anki_lapses: ['Lapses', 'Anki-Zähler „lapses“ der Karte: wie oft eine gelernte Karte vergessen wurde (Taste „Nochmal“ in der Wiederholung).', 'Ob Sie die Kompetenz beherrschen.'],
  anki_interval: ['aktuelles Intervall', 'Anki-Feld „ivl“: Abstand bis zur nächsten Wiederholung in Tagen, von Anki/FSRS geplant.', 'Behalten: das Intervall ist eine Planungsgröße.'],
};
let LEDGER = null, PROGRESS = null, TL_FILTER = { course: '', unit: '', product: '' }, TL_LIMIT = 100;
function ledgerNow(lib) {
  const storage = { [TKEY]: readJSON(TKEY), [PKEY]: readJSON(PKEY), [MKEY]: readJSON(MKEY), [LKEY]: readJSON(LKEY) };
  LEDGER = window.MasteryLedger.buildLedger(storage, lib); PROGRESS = window.MasteryLedger.summarize(LEDGER, lib);
  return [LEDGER, PROGRESS];
}
function taskTitles(lib) {
  const out = {};
  for (const u of lib.units) {
    for (const tr of u.tracks) for (const t of tr.data.tasks) out['em-tutor-v1\u0000' + tr.store_key + '\u0000' + t.id] = t.title;
    for (const a of u.assessments) out['em-practice-v1\u0000' + u.practice_store.unit_id + '\u0000' + a.id] = a.title;
  }
  return out;
}
/* A number with its "Woher?" button: data-num, data-why = rule key; refs = ledger ids behind it. */
function num(value, why, refs, box) {
  const b = el('button', { type: 'button', class: 'm-n', 'data-num': String(value), 'data-why': why, 'aria-label': value + ' – Woher?', title: 'Woher?' }, String(value));
  b.addEventListener('click', () => explain(box, why, refs || [], value)); return b;
}
function stampText(iso) { return iso ? when(iso) : '–'; }
function dateCell(iso, why, refs, box) {
  if (!iso) return '–';
  const b = el('button', { type: 'button', class: 'm-n m-date', 'data-num': iso, 'data-why': why, title: 'Woher?' }, stampText(iso));
  b.addEventListener('click', () => explain(box, why, refs || [], stampText(iso))); return b;
}
function explain(box, why, refs, value) {
  const [title, rule, not] = WHY[why], byId = Object.fromEntries((LEDGER ? LEDGER.events : []).map(e => [e.id, e]));
  box.hidden = false;
  box.replaceChildren(el('p', { class: 'm-why-h' }, el('strong', {}, 'Woher? '), title + ': ' + value),
    el('p', {}, el('strong', {}, 'Regel: '), rule),
    refs.length ? el('details', { open: refs.length <= 8 ? true : null }, el('summary', {}, 'Daten: ' + refs.length + ' Einträge aus Ihrem Browser'),
      el('ul', { class: 'm-why-refs' }, refs.slice(0, 50).map(id => { const e = byId[id]; return el('li', {}, e ? stampText(e.at) + ' · ' + (e.kind === 'help' ? HELPNAME[e.help] : LKIND[e.kind] || e.type) + (e.result ? ' · ' + (RESULT[e.result] || e.result) : '') + ' · ' : '', el('code', {}, id)); })))
      : el('p', {}, el('strong', {}, 'Daten: '), 'keine passenden Einträge.'),
    el('p', { class: 'm-not' }, el('strong', {}, 'Was das nicht misst: '), not + ' ' + NOT_GENERAL),
    el('button', { type: 'button', class: 'ds-btn m-why-close', onclick: () => { box.hidden = true; } }, 'Schließen'));
  box.focus();
}
const whyBox = () => el('div', { class: 'm-why', role: 'region', 'aria-label': 'Woher? Erklärung', tabindex: '-1', hidden: true });
const unitHead = u => u.course ? 'Kurs ' + u.course.title + ' · Kapitel ' + u.chapter.order + ': ' + u.title : 'Einheit: ' + u.title;

function storesCard(led) {
  const box = whyBox(), NAMES = { 'em-tutor-v1': ['Übungsstrecken', 'Versuche, Hinweise, Lösungen, Tutor-Briefe, geführte Hilfen je Übungsstrecke'], 'em-practice-v1': ['Interaktiv (Explorable)', 'Entscheidungsprotokoll mit Prüfergebnis und datensparsames Aktionsprotokoll (Export em-practice-evidence-v1)'],
    'em-motion-v1': ['Mastery Motion', 'Vorhersagen, Aufdecken, Regler-Aufträge'], 'em-learn-v2': ['Kapitel-App', 'Lernhandlungen der älteren Kapitel-App, falls unter dieser Adresse genutzt'] };
  const byStore = s => led.events.filter(e => e.store === s.store).map(e => e.id);
  return el('div', { class: 'm-card', id: 'sources' }, el('h2', { class: 'm-h2' }, 'Woher kommen die Daten?'),
    el('p', {}, 'Mastery speichert jede Lernhandlung dort, wo sie passiert – getrennt nach Produkt, alle im Browser dieser Adresse. Diese Seite liest alle Speicher, ändert keinen und führt sie zu einem Verlauf zusammen (Lernstand-Register ', el('code', {}, led.schema), '). Jede Zahl ist anklickbar: „Woher?“ nennt Regel, Einträge und was sie nicht misst.'),
    el('p', { class: 'm-note', id: 'mirror-note' }, 'Warum ist ein exportiertes Explorable-Protokoll (em-practice-evidence-v1) manchmal leer, obwohl Sie geübt haben? Übungsstrecken wie Backpropagation speichern ihren Verlauf getrennt (em-tutor-v1). Das Explorable führt zwei Protokolle derselben Handlungen: das Entscheidungsprotokoll mit Prüfergebnis und ein Aktionsprotokoll ohne Antworten für den Export. Hier zählt jede Handlung genau einmal.'),
    el('div', { class: 'm-scroll' }, el('table', { class: 'm-table' }, el('thead', {}, el('tr', {}, ['Speicher', 'Inhalt', 'gelesen', 'in der Zeitleiste', 'ausgelassen'].map(h => el('th', { scope: 'col' }, h)))),
      el('tbody', {}, led.stores.map(s => el('tr', { 'data-store': s.store }, el('th', { scope: 'row' }, NAMES[s.store][0], el('div', {}, el('code', {}, s.store))), el('td', {}, s.present ? NAMES[s.store][1] : 'in diesem Browser nicht vorhanden'),
        el('td', {}, num(s.read, 'store_read', [], box)), el('td', {}, num(s.included, 'store_included', byStore(s), box)),
        el('td', {}, num(Object.values(s.excluded).reduce((a, b) => a + b, 0), 'store_excluded', [], box), Object.keys(s.excluded).length ? el('small', { class: 'm-note' }, ' (' + Object.entries(s.excluded).map(([k, v]) => k + ': ' + v).join(', ') + ')') : null)))))),
    box);
}
function competencyCards(lib, prog) {
  const out = el('div', { id: 'competencies' }, el('h2', { class: 'm-h2' }, 'Je Kompetenz'));
  const HEAD = ['Kompetenz', 'Zustand', 'Evidenzbasis', 'ohne Hilfe', 'mit Hilfe', 'davon Freitext (unbewertet)', 'wiederholt', 'Hilfen', 'selbstständig richtig', 'erste / letzte selbstständige Lösung', 'späterer Nachweis (≥ 20 h)'];
  for (const u of lib.units) {
    const rows = prog.competencies.filter(c => c.unit === u.slug);
    const scopes = [...new Set(rows.map(c => c.scope))];
    const card = el('div', { class: 'm-card', 'data-unit': u.slug, 'data-course': u.course ? u.course.slug : null }, el('h3', { class: 'm-h3' }, unitHead(u)));
    const box = whyBox();
    for (const sc of scopes) {
      const rs = rows.filter(c => c.scope === sc), first = rs[0], src = first.product;
      card.append(el('h4', { class: 'm-h4' }, (PRODUCT[src] || src) + ': ' + first.scope_title),
        el('p', { class: 'm-note' }, src === 'explorable' ? 'Interaktiv: Zahlenaufgaben werden regelbasiert geprüft, Freitext nicht. Zuordnung über die erste Kompetenz der Aufgabe.' : 'Übungsstrecke: Zahl, Ausdruck und Rechenschritte werden regelbasiert geprüft.'),
        el('div', { class: 'm-scroll' }, el('table', { class: 'm-table m-kc' }, el('thead', {}, el('tr', {}, HEAD.map(h => el('th', { scope: 'col' }, h)))),
          el('tbody', {}, rs.map(c => { const n = c.counts, r = c.refs;
            const helps = ['hint', 'solution', 'tutor', 'guided', 'support'].filter(h => n[h]).map(h => el('span', { class: 'm-help' }, num(n[h], h, r[h], box), ' ' + WHY[h][0]));
            return el('tr', { 'data-kc': c.competency, 'data-source': src, 'data-status': c.status, 'data-basis': c.basis, 'data-assisted': String(n.assisted), 'data-unassisted': String(n.unassisted), 'data-unverified': String(n.unverified), 'data-independent': String(n.independent), 'data-delayed': c.delayed ? c.delayed.at : '' },
              el('th', { scope: 'row' }, c.label),
              el('td', {}, el('button', { type: 'button', class: 'm-n m-state', 'data-num': c.status, 'data-why': 'status', onclick: () => explain(box, 'status', r.independent.concat(r.assisted), STATUS[c.status] || c.status) }, STATUS[c.status] || c.status)),
              el('td', {}, el('button', { type: 'button', class: 'm-n m-state', 'data-num': c.basis, 'data-why': 'basis', onclick: () => explain(box, 'basis', r.independent, BASIS[c.basis] || c.basis) }, BASIS[c.basis] || c.basis)),
              el('td', {}, num(n.unassisted, 'unassisted', r.unassisted, box)), el('td', {}, num(n.assisted, 'assisted', r.assisted, box)),
              el('td', {}, num(n.unverified, 'unverified', r.unverified, box)), el('td', {}, num(n.retries, 'retries', r.retries, box)),
              el('td', {}, helps.length ? helps : 'keine'), el('td', {}, num(n.independent, 'independent', r.independent, box)),
              el('td', {}, dateCell(c.first_independent, 'first_independent', r.independent.slice(0, 1), box), c.latest_independent && c.latest_independent !== c.first_independent ? [' / ', dateCell(c.latest_independent, 'latest_independent', r.independent.slice(-1), box)] : null),
              el('td', {}, c.delayed ? [dateCell(c.delayed.at, 'delayed', [c.delayed.ref], box), el('small', { class: 'm-note' }, ' nach ', num(c.delayed.after_hours, 'delayed', [c.delayed.ref], box), ' Stunden')] : 'noch keiner'));
          })))));
    }
    card.append(box); out.append(card);
  }
  return out;
}
function coverageCard(lib, prog) {
  const box = whyBox(), card = el('div', { class: 'm-card', id: 'coverage' }, el('h2', { class: 'm-h2' }, 'Abdeckung je Kapitel'),
    el('p', { class: 'm-note' }, 'Welche Kompetenzen eines Kapitels haben mindestens eine selbst erzeugte, regelbasiert geprüfte Lösung ohne Hilfe – und welche nicht. Keine Quote: Eine Kompetenz ohne Nachweis ist ein Hinweis, wo Sie als Nächstes üben können.'));
  const why = it => it.basis === 'recognition_only' ? 'nur Wiedererkennen geprüft' : it.attempted ? 'nur mit Hilfe, falsch oder unbewertet' : 'noch nicht bearbeitet';
  for (const ch of prog.chapters) {
    const u = lib.units.find(x => x.slug === ch.unit), refsOf = ids => prog.competencies.filter(c => c.unit === ch.unit && ids.includes(c.competency)).flatMap(c => c.refs.independent);
    const withIt = ch.items.filter(i => i.basis === 'production'), without = ch.items.filter(i => i.basis !== 'production');
    card.append(el('section', { class: 'm-cov', 'data-unit': ch.unit, 'data-course': ch.course, 'data-with': String(withIt.length), 'data-without': String(without.length) }, el('h3', { class: 'm-h3' }, unitHead(u)),
      el('p', {}, el('strong', {}, 'Mit selbst erzeugter Lösung: '), num(withIt.length, 'coverage_with', refsOf(ch.with_production), box), withIt.length ? ' – ' + withIt.map(i => i.label).join(', ') : ''),
      el('p', {}, el('strong', {}, 'Ohne: '), num(without.length, 'coverage_without', [], box)),
      without.length ? el('ul', { class: 'm-cov-list' }, without.map(i => el('li', { 'data-competency': i.competency }, i.label, el('small', { class: 'm-note' }, ' – ' + why(i))))) : null));
  }
  card.append(box);
  return card;
}
function timelineCard(lib, led) {
  const titles = taskTitles(lib), box = whyBox(), list = el('ol', { class: 'm-tl', id: 'timeline-list', reversed: true }), count = el('span', { id: 'timeline-count' });
  const courses = [...new Map(lib.units.filter(u => u.course).map(u => [u.course.slug, u.course.title]))];
  const sel = (id, label, opts, key) => el('label', { class: 'm-field-inline' }, label + ' ', el('select', { class: 'm-input', id, onchange: e => { TL_FILTER[key] = e.target.value; TL_LIMIT = 100; draw(); } },
    el('option', { value: '' }, 'alle'), opts.map(([v, t]) => el('option', { value: v, selected: TL_FILTER[key] === v ? true : null }, t))));
  const more = el('button', { type: 'button', class: 'ds-btn', id: 'timeline-more', onclick: () => { TL_LIMIT += 100; draw(); } }, 'Ältere anzeigen');
  const unitName = slug => { const u = lib.units.find(x => x.slug === slug); return u ? (u.course ? u.course.title + ' · ' : '') + u.title : null; };
  function draw() {
    const f = TL_FILTER, evs = led.events.filter(e => (!f.course || e.course === f.course) && (!f.unit || e.unit === f.unit) && (!f.product || e.product === f.product)).slice().reverse();
    count.replaceChildren(num(evs.length, 'timeline', [], box), ' Einträge');
    list.replaceChildren(...evs.slice(0, TL_LIMIT).map(e => {
      const title = titles[e.store + '\u0000' + e.record + '\u0000' + e.task] || e.task, what = e.kind === 'help' ? HELPNAME[e.help] || e.type : LKIND[e.kind] || e.type;
      return el('li', { class: 'm-tl-item', 'data-id': e.id, 'data-product': e.product, 'data-kind': e.kind, 'data-course': e.course, 'data-unit': e.unit },
        el('div', { class: 'm-tl-when' }, e.at ? stampText(e.at) : '–', e.t_quality !== 'exact' ? el('small', { class: 'm-badge' }, TQ[e.t_quality]) : null),
        el('div', { class: 'm-tl-what' }, el('strong', {}, what), title ? ' · ' + title : '', e.result ? ' → ' + (RESULT[e.result] || e.result) : '',
          el('div', { class: 'm-tl-tags' }, el('span', { class: 'm-tag' }, PRODUCT[e.product] || e.product), e.unit ? el('span', { class: 'm-tag' }, unitName(e.unit)) : null,
            e.assist ? el('span', { class: 'm-tag ' + (e.assist === 'assisted' ? 'm-tag-help' : 'm-tag-ind') }, e.assist === 'assisted' ? 'mit Hilfe' : 'ohne Hilfe') : null,
            e.source ? el('span', { class: 'm-tag' }, e.kind === 'help' && e.source === 'deterministic' ? 'vorbereitete Hilfe' : SOURCE[e.source] || e.source) : null,
            e.role ? el('span', { class: 'm-tag' }, ROLE[e.role]) : null, e.archived ? el('span', { class: 'm-tag' }, 'frühere Fassung') : null),
          e.note ? el('small', { class: 'm-note' }, e.note) : null,
          el('small', { class: 'm-prov' }, 'Herkunft: ', el('code', {}, e.id))));
    }));
    more.hidden = evs.length <= TL_LIMIT;
    if (!evs.length) list.replaceChildren(el('li', { class: 'm-note' }, 'Keine Lernhandlungen für diese Auswahl.'));
  }
  draw();
  return el('div', { class: 'm-card', id: 'timeline' }, el('h2', { class: 'm-h2' }, 'Zeitleiste'),
    el('p', { class: 'm-note' }, 'Alle Lernhandlungen dieses Browsers, neueste zuerst. Jeder Eintrag nennt Produkt, Prüfweg (regelbasiert, Selbstauskunft, nicht bewertet, Sprachmodell) und seine Herkunft im Speicher.'),
    el('div', { class: 'm-row m-filters' }, sel('tl-course', 'Kurs', courses, 'course'), sel('tl-unit', 'Kapitel/Einheit', lib.units.map(u => [u.slug, unitName(u.slug)]), 'unit'),
      sel('tl-product', 'Produkt', Object.entries(PRODUCT), 'product'), count), list, more, box);
}
function motionCard(lib, prog) {
  if (!prog.motion.length) return null;
  const box = whyBox();
  return el('div', { class: 'm-card', id: 'motion-progress' }, el('h2', { class: 'm-h2' }, 'Mastery Motion: Vorhersagen'),
    el('p', { class: 'm-note' }, 'Vorhersagen sind Lernhandlungen vor dem Aufdecken, kein Nachweis von Können. Sie ändern keinen Kompetenzzustand und keinen Wert oben.'),
    el('div', { class: 'm-scroll' }, el('table', { class: 'm-table' }, el('thead', {}, el('tr', {}, ['Szene', 'Vorhersagen', 'davon zutreffend', 'aufgedeckt', 'Aufträge geprüft', 'davon erreicht'].map(h => el('th', { scope: 'col' }, h)))),
      el('tbody', {}, prog.motion.map(m => { const d = (lib.motion_demos || []).find(x => x.id === m.scene);
        return el('tr', { 'data-motion-scene': m.scene, 'data-predictions': String(m.predictions.length) }, el('th', { scope: 'row' }, d ? el('a', { href: d.href }, d.title) : m.scene),
          el('td', {}, num(m.predictions.length, 'motion_predictions', m.predictions, box)), el('td', {}, num(m.predictions_correct.length, 'motion_correct', m.predictions_correct, box)),
          el('td', {}, num(m.reveals.length, 'motion_reveals', m.reveals, box)), el('td', {}, num(m.missions.length, 'motion_missions', m.missions, box)), el('td', {}, num(m.missions_met.length, 'motion_met', m.missions_met, box))); })))), box);
}
/* Optional Anki statistics: only from an export file the learner makes and chooses, only after an explicit consent. */
let ANKI_STATS = undefined;
function ankiStatsTable(st, box) {
  const label = el('p', { class: 'm-badge', id: 'anki-stats-label' }, st.label);
  return [label, el('p', { class: 'm-note' }, 'Datei ', el('code', {}, st.file.name), ' · gelesen ' + when(st.imported_at) + ' · Karten anderer Stapel nicht ausgewertet: ', num(st.other_cards_ignored, 'anki_cards', [], box)),
    el('div', { class: 'm-scroll' }, el('table', { class: 'm-table', id: 'anki-stats-decks' }, el('thead', {}, el('tr', {}, ['Stapel', 'Karten', 'Wiederholungen', 'Lapses'].map(h => el('th', { scope: 'col' }, h)))),
      el('tbody', {}, st.decks.map(d => el('tr', { 'data-deck': d.name }, el('th', { scope: 'row' }, d.name), el('td', {}, num(d.cards, 'anki_cards', [], box)), el('td', {}, num(d.reviews, 'anki_reviews', [], box)), el('td', {}, num(d.lapses, 'anki_lapses', [], box))))))),
    el('details', {}, el('summary', {}, 'Je Karte'), el('div', { class: 'm-scroll' }, el('table', { class: 'm-table', id: 'anki-stats-cards' },
      el('thead', {}, el('tr', {}, ['Karte (Vorderseite)', 'Stapel', 'Status in Anki', 'Wiederholungen', 'Lapses', 'Intervall (Tage)', 'zuletzt wiederholt'].map(h => el('th', { scope: 'col' }, h)))),
      el('tbody', {}, st.cards.map(c => el('tr', { 'data-guid': c.note_guid }, el('th', { scope: 'row' }, c.front || '–'), el('td', {}, c.deck), el('td', {}, c.queue),
        el('td', {}, num(c.reviews, 'anki_reviews', [], box)), el('td', {}, num(c.lapses, 'anki_lapses', [], box)), el('td', {}, num(c.interval_days, 'anki_interval', [], box)), el('td', {}, c.last_review ? when(c.last_review) : '–'))))))),
    el('p', { class: 'm-not' }, el('strong', {}, 'Was das nicht misst: '), st.not_measured)];
}
function ankiStatsCard() {
  const box = whyBox(), out = el('div', { id: 'anki-stats-body' }), msg = el('p', { class: 'm-note', role: 'status', id: 'anki-stats-status' });
  const consent = el('input', { type: 'checkbox', id: 'anki-consent', onchange: () => { pick.disabled = !consent.checked; } });
  const pick = el('input', { type: 'file', id: 'anki-file', accept: '.apkg,.colpkg', disabled: true, onchange: e => {
    const f = e.target.files[0]; if (!f || !consent.checked) return;
    if (f.size > 30e6) { msg.textContent = 'Die Datei ist größer als 30 MB. Bitte nur die Mastery-Stapel ohne Medien exportieren.'; return; }
    msg.textContent = 'Datei wird lokal gelesen …';
    f.arrayBuffer().then(buf => { const b = new Uint8Array(buf); let s = ''; for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode.apply(null, b.subarray(i, i + 32768));
      return api('api/anki-stats', { consent: true, filename: f.name, data_base64: btoa(s) }); })
      .then(r => { ANKI_STATS = r.stats; msg.textContent = 'Gelesen. Die temporäre Kopie ist gelöscht; gespeichert sind nur die Zahlen unten.'; draw(); })
      .catch(err => { msg.textContent = 'Nicht gelesen: ' + err.message; });
  } });
  const forget = el('button', { type: 'button', class: 'ds-btn', id: 'anki-forget', onclick: () => api('api/anki-stats/forget').then(() => { ANKI_STATS = null; msg.textContent = 'Anki-Statistik entfernt.'; draw(); }).catch(err => { msg.textContent = 'Nicht möglich: ' + err.message; }) }, 'Anki-Statistik entfernen');
  function draw() { out.replaceChildren(...(ANKI_STATS ? ankiStatsTable(ANKI_STATS, box) : [el('p', { class: 'm-note' }, 'Keine Anki-Statistik geladen.')])); forget.hidden = !ANKI_STATS; }
  if (ANKI_STATS === undefined) fetch('api/anki-stats', { cache: 'no-store' }).then(r => r.ok ? r.json() : { stats: null }).then(j => { ANKI_STATS = j.stats || null; draw(); }).catch(() => { ANKI_STATS = null; draw(); });
  draw();
  return el('div', { class: 'm-card', id: 'anki-stats' }, el('h2', { class: 'm-h2' }, 'Anki-Statistik (optional, nur mit Ihrer Freigabe)'),
    el('p', {}, 'Mastery öffnet Ihre Anki-Sammlung nie. Wenn Sie möchten, exportieren Sie selbst die Mastery-Stapel aus Anki und geben Mastery genau diese Datei. Sie wird lokal in einem temporären Ordner gelesen und danach gelöscht; nur Zählwerte der Stapel „Exam Mastery::…“ bleiben in Ihrer Bibliothek (anki-stats/), bis Sie sie entfernen.'),
    el('ol', { class: 'm-steps' }, el('li', {}, 'Anki: Datei → Exportieren …'), el('li', {}, 'Format „Anki-Stapelpaket (.apkg)“, Stapel „Exam Mastery::…“ wählen, „Planungsdaten einschließen“ ankreuzen, Medien weglassen.'),
      el('li', {}, 'Falls Mastery das Format nicht lesen kann: zusätzlich „Unterstützung für ältere Anki-Versionen“ ankreuzen.'), el('li', {}, 'Hier zustimmen und die Datei wählen.')),
    el('label', { class: 'm-check' }, consent, ' Ich erlaube Mastery, diese von mir exportierte Datei einmal lokal zu lesen.'),
    el('div', { class: 'm-row' }, el('label', { class: 'm-field-inline', for: 'anki-file' }, 'Anki-Export wählen: '), pick, forget), msg, out, box);
}
function viewProgress(lib) {
  const [led, prog] = ledgerNow(lib);
  const s = el('section', { id: 'lernstand', class: 'm-view', 'aria-labelledby': 'h-ls' }, el('h1', { id: 'h-ls', class: 'm-h1' }, 'Lernstand'),
    el('p', { class: 'm-statement', id: 'proximal' }, 'Was Sie hier sehen, sind beobachtete Lernhandlungen in diesem Browser – Näherungsanzeigen innerhalb von Mastery, keine Messung von Lernen oder Können. Es gibt bewusst keinen Prozentwert, keine Punktzahl und keine Serien. „Mit Hilfe“ heißt: Hinweis, Lösung, Tutor-Brief, geführte Hilfe oder gezeigtes Beispiel zu dieser Aufgabe oder (bis 20 Stunden davor) zur selben Kompetenz. Behalten zeigt erst eine selbstständige Lösung nach echter verstrichener Zeit.'),
    el('p', { class: 'm-not', id: 'not-measured' }, el('strong', {}, 'Was das nicht misst: '), 'ob Mastery Ihr Lernen verbessert (nicht untersucht, NOT_RUN); was Sie außerhalb von Mastery, in Anki oder auf Papier können; Lernstände in anderen Browsern, Geräten oder unter anderen Ports; die fachliche Qualität von Freitext.'));
  s.append(storesCard(led), competencyCards(lib, prog), coverageCard(lib, prog));
  const mc = motionCard(lib, prog); if (mc) s.append(mc);
  s.append(timelineCard(lib, led), ankiStatsCard());
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

/* ------------------------------------------------------------ courses: import wizard (local server API, no model calls) */
const PIPE = { NICHT_ERARBEITET: 'Nicht erarbeitet', PAKET_BEREIT: 'Paket bereit', ERARBEITET: 'Erarbeitet', GEBAUT: 'Gebaut', 'PRÜFUNG_AUSSTEHEND': 'Prüfung ausstehend' };
const KIND = { lecture_slides: 'Vorlesungsfolien', script: 'Skript', exercise: 'Übung', solution: 'Lösung', exam: 'Klausur', literature: 'Literatur', notebook: 'Notebook', other: 'Sonstiges' };
const FSTAT = { ok: 'gelesen', no_text: 'ohne Textebene', not_local: 'nicht lokal verfügbar', unsupported: 'nicht unterstützt', unreadable: 'nicht lesbar', ignored: 'ignoriert', symlink_skipped: 'Verknüpfung übersprungen' };
let COURSES = null, COURSE_ERR = null;
function api(path, body) {
  return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}), cache: 'no-store' })
    .then(r => r.json().catch(() => ({})).then(j => r.ok ? j : Promise.reject(new Error(j.error || ('HTTP ' + r.status)))));
}
function busy(btn, msg, text, job) {
  btn.disabled = true; msg.textContent = text; msg.dataset.state = 'busy';
  return job().then(() => reload('#kurse')).then(() => { const m = document.getElementById(msg.id); if (m) { m.textContent = 'Fertig.'; m.dataset.state = 'done'; } })
    .catch(e => { btn.disabled = false; msg.textContent = 'Nicht möglich: ' + e.message; msg.dataset.state = 'error'; });
}
function pipeline(ch) {
  const order = Object.keys(PIPE), at = order.indexOf(ch.status);
  return el('ol', { class: 'm-pipe', 'aria-label': 'Status' }, order.map((k, i) => el('li', { class: i < at ? 'done' : i === at ? 'now' : '', 'aria-current': i === at ? 'step' : null },
    PIPE[k] + (k === 'ERARBEITET' && ch.author_label && i <= at ? ' (' + ch.author_label + ')' : ''))));
}
function chapterAction(c, ch) {
  const msg = el('p', { class: 'm-note', role: 'status', id: 'msg-' + c.slug + '-' + ch.id });
  const base = 'api/courses/' + c.slug + '/chapters/' + ch.id + '/';
  const packetBtn = label => { const b = el('button', { type: 'button', class: 'ds-btn', 'data-action': 'packet', onclick: () => busy(b, msg, 'Paket wird geschrieben …', () => api(base + 'packet')) }, label); return b; };
  const box = el('div', { class: 'm-action' });
  if (ch.stale) box.append(el('p', { class: 'm-badge m-stale', 'data-stale': '1' }, 'Quellen geändert seit dem Paket: ' + ch.stale.sources.slice(0, 4).join(', ') + ' – Paket erneuern und Kapitel überarbeiten.'));
  if (ch.status === 'NICHT_ERARBEITET') box.append(packetBtn('Paket erstellen'));
  if (ch.status === 'PAKET_BEREIT' && ch.instruction) {
    const copy = el('button', { type: 'button', class: 'ds-btn', onclick: () => { try { navigator.clipboard.writeText(ch.instruction.prompt); copy.textContent = 'Kopiert'; } catch (e) { copy.textContent = 'Bitte markieren und kopieren'; } } }, 'Auftrag kopieren');
    box.append(el('div', { class: 'm-instr', 'data-instruction': ch.id },
      el('p', {}, el('strong', {}, 'Erarbeiten: '), ch.instruction.statement),
      el('ol', { class: 'm-steps' }, el('li', {}, 'Terminal öffnen: ', el('code', {}, ch.instruction.command)),
        el('li', {}, 'Diesen Auftrag in die Claude-Code-Sitzung geben: ', el('code', { class: 'm-prompt' }, ch.instruction.prompt), ' ', copy),
        el('li', {}, 'Danach bauen (hier mit „Bauen“ oder im Terminal): ', el('code', {}, ch.instruction.then))),
      el('p', { class: 'm-note' }, 'Ein Mensch kann unit.json und authoring.json ebenso schreiben. Ohne diesen Schritt entsteht kein Kapitel – Mastery erfindet keine Inhalte.')), packetBtn('Paket erneuern'));
  }
  if (ch.status === 'ERARBEITET' || ch.rebuild_needed) { const b = el('button', { type: 'button', class: 'ds-btn ds-btn-primary', 'data-action': 'build', onclick: () => busy(b, msg, 'Vier Produkte werden gebaut (offline) …', () => api(base + 'build')) }, 'Bauen (vier Produkte)'); box.append(b); }
  if (ch.products) box.append(el('ul', { class: 'm-links' }, PRODUCTS.map(([k, label]) => el('li', {}, el('a', { href: ch.products[k], 'data-product': k, download: k === 'anki' ? 'Anki.apkg' : null }, label)))),
    el('p', { class: 'm-note' }, 'Fachliche Prüfung durch Menschen ausstehend; Lernwirkung nicht gemessen.'));
  box.append(msg);
  return box;
}
function coursePanel(c) {
  const n = c.counts, card = el('article', { class: 'm-card m-course', 'data-course': c.slug });
  card.append(el('p', { class: 'ds-eyebrow' }, 'Kurs · importiert ' + when(c.imported_at)), el('h2', { class: 'm-h2' }, c.title),
    el('p', { class: 'm-note' }, 'Quelle (nur gelesen): ', el('code', {}, c.source_root)),
    el('p', { class: 'm-counts', 'data-files': String(n.files), 'data-pages': String(n.pages) }, n.files + ' Dateien · ' + n.pages + ' Seiten/Folien (' + n.text_pages + ' mit Text, ' + n.vision_pages + ' brauchen Bildverständnis) · ' +
      Object.entries(n.kinds).map(([k, v]) => v + ' ' + (KIND[k] || k)).join(', ')));
  const msg = el('p', { class: 'm-note', role: 'status', id: 'msg-course-' + c.slug });
  const row = el('div', { class: 'm-row' });
  if (n.not_local) {
    const b = el('button', { type: 'button', class: 'ds-btn ds-btn-primary', id: 'materialize-' + c.slug, onclick: () => busy(b, msg, 'Dateien werden aus iCloud geladen …', () => api('api/courses/' + c.slug + '/materialize', { consent: true })) }, n.not_local + ' Datei(en) aus iCloud herunterladen');
    card.append(el('div', { class: 'm-icloud', 'data-not-local': String(n.not_local) }, el('p', {}, el('strong', {}, n.not_local + ' Datei(en) nicht lokal verfügbar. '), 'Sie liegen nur als iCloud-Platzhalter vor; Mastery hat sie nicht geöffnet. Auf Ihren Klick lädt macOS sie herunter (brctl download); nichts wird gelöscht oder verändert.'), b));
  }
  const re = el('button', { type: 'button', class: 'ds-btn', 'data-action': 'reimport', onclick: () => busy(re, msg, 'Kursordner wird neu eingelesen …', () => api('api/courses/' + c.slug + '/reimport')) }, 'Neu einlesen (Änderungen erkennen)');
  row.append(re); card.append(row, msg);
  const main = c.warnings.filter(w => w.severity !== 'info'), info = c.warnings.filter(w => w.severity === 'info');
  card.append(el('h3', { class: 'm-h3' }, 'Vollständigkeit (' + main.length + ' Warnungen, ' + info.length + ' Hinweise)'),
    main.length ? el('ul', { class: 'm-warn' }, main.map(w => el('li', { 'data-code': w.code, class: 'sev-' + w.severity }, w.message))) : el('p', {}, 'Keine Warnungen.'),
    info.length ? el('details', {}, el('summary', {}, info.length + ' Hinweise'), el('ul', { class: 'm-warn' }, info.map(w => el('li', { 'data-code': w.code }, w.message)))) : null);
  card.append(el('details', { class: 'm-inv' }, el('summary', {}, 'Inventar: ' + c.files.length + ' Dateien'), el('div', { class: 'm-scroll' }, el('table', { class: 'm-table' },
    el('thead', {}, el('tr', {}, ['Datei', 'Art', 'Seiten', 'mit Text', 'Bildverständnis', 'Status'].map(h => el('th', { scope: 'col' }, h)))),
    el('tbody', {}, c.files.map(f => el('tr', { 'data-file': f.rel_path, 'data-status': f.status, 'data-kind': f.kind },
      el('th', { scope: 'row' }, f.rel_path), el('td', { title: f.kind_basis || '' }, KIND[f.kind] || f.kind), el('td', {}, f.pages == null ? '–' : String(f.pages)),
      el('td', {}, f.text_pages == null ? '–' : String(f.text_pages)), el('td', {}, f.pages == null ? '–' : String(f.vision_pages)),
      el('td', {}, (FSTAT[f.status] || f.status) + (f.duplicate_of ? ' · Duplikat' : '')))))))));
  const ids = c.chapters.map(ch => ch.id), planMsg = el('p', { class: 'm-note', role: 'status', id: 'msg-plan-' + c.slug });
  const rows = c.chapters.map(ch => {
    const title = el('input', { type: 'text', class: 'm-input', value: ch.title, 'aria-label': 'Titel von ' + ch.id, 'data-field': 'title', maxlength: '120' });
    const skip = el('input', { type: 'checkbox', 'data-field': 'skip', 'aria-label': 'Kapitel überspringen', checked: ch.skip });
    const order = el('input', { type: 'number', class: 'm-input m-num', value: String(ch.order), 'aria-label': 'Reihenfolge', 'data-field': 'order', min: '1' });
    const merge = el('select', { class: 'm-input', 'data-field': 'merge_into', 'aria-label': 'Zusammenführen mit' }, el('option', { value: '' }, '—'), ids.filter(x => x !== ch.id).map(x => el('option', { value: x }, x)));
    return el('tr', { 'data-chapter': ch.id, 'data-status': ch.status, class: ch.skip ? 'm-skip' : '' },
      el('td', {}, order), el('td', {}, title, el('div', { class: 'm-note' }, ch.sources.length + ' Quelle(n) · ' + ch.exercises.length + ' Übung(en) · ' + ch.solutions.length + ' Lösung(en)' + (ch.merged.length ? ' · zusammengeführt: ' + ch.merged.join(', ') : '')),
        ch.competencies_proposed.length ? el('details', {}, el('summary', {}, ch.competencies_proposed.length + ' Kompetenzen (Vorschlag)'), el('ul', {}, ch.competencies_proposed.map(k => el('li', { 'data-competency': k.id }, k.text, el('small', { class: 'm-note' }, ' – ' + k.basis + ', ' + k.provenance.map(p => p.rel_path.split('/').pop() + (p.page ? ' S. ' + p.page : '')).join('; ')))))) : null),
      el('td', {}, el('label', { class: 'm-check' }, skip, ' überspringen'), el('div', {}, merge)),
      el('td', {}, pipeline(ch), ch.skip ? el('p', { class: 'm-note' }, 'Übersprungen') : chapterAction(c, ch)));
  });
  const save = el('button', { type: 'button', class: 'ds-btn', id: 'plan-save-' + c.slug, onclick: () => {
    const ov = {};
    for (const tr of rows) { const id = tr.dataset.chapter, ch = c.chapters.find(x => x.id === id), o = {};
      const v = f => tr.querySelector('[data-field="' + f + '"]');
      if (v('title').value.trim() && v('title').value.trim() !== ch.title) o.title = v('title').value.trim();
      if (v('skip').checked !== !!ch.skip) o.skip = v('skip').checked;
      if (Number(v('order').value) !== ch.order) o.order = Number(v('order').value);
      if (v('merge_into').value) o.merge_into = v('merge_into').value;
      if (Object.keys(o).length) ov[id] = o; }
    busy(save, planMsg, 'Plan wird gespeichert …', () => api('api/courses/' + c.slug + '/plan', { overrides: { chapters: ov } }));
  } }, 'Planänderungen speichern');
  card.append(el('h3', { class: 'm-h3' }, 'Kapitelplan (Vorschlag – bearbeitbar)'),
    el('p', { class: 'm-note' }, 'Ein Kapitel pro Vorlesung; Übungen nach Titel, Inhalt oder Nummer zugeordnet; Klausuren gehören zu allen Kapiteln. Kompetenzen sind Vorschläge aus Folientiteln und Lernziel-Folien – deterministisch, ohne Modell.'),
    el('div', { class: 'm-scroll' }, el('table', { class: 'm-table m-plan' }, el('thead', {}, el('tr', {}, ['Nr.', 'Kapitel', 'Bearbeiten', 'Status und nächster Schritt'].map(h => el('th', { scope: 'col' }, h)))), el('tbody', {}, rows))),
    el('div', { class: 'm-row' }, save), planMsg);
  return card;
}
function viewCourses() {
  const msg = el('p', { class: 'm-note', role: 'status', id: 'import-status' });
  const path = el('input', { type: 'text', class: 'm-input m-wide', id: 'import-path', placeholder: '/Users/…/Studium/Kursordner', 'aria-describedby': 'import-help', autocomplete: 'off', spellcheck: 'false' });
  const title = el('input', { type: 'text', class: 'm-input', id: 'import-title', placeholder: 'optional', maxlength: '120' });
  const consent = el('input', { type: 'checkbox', id: 'import-materialize' });
  const run = el('button', { type: 'button', class: 'ds-btn ds-btn-primary', id: 'import-run', onclick: () => {
    if (!path.value.trim()) { msg.textContent = 'Bitte einen Ordnerpfad eingeben.'; return; }
    busy(run, msg, 'Kursordner wird gelesen (das kann bei großen Kursen eine Minute dauern) …', () => api('api/import', { path: path.value.trim(), title: title.value.trim() || null, materialize: consent.checked }));
  } }, 'Importieren');
  const s = el('section', { id: 'kurse', class: 'm-view', 'aria-labelledby': 'h-ku' }, el('h1', { id: 'h-ku', class: 'm-h1' }, 'Kurse'),
    el('p', { class: 'm-lead' }, 'Lehrveranstaltung importieren: Mastery liest Ihren Kursordner (Folien, Skripte, Übungen, Lösungen, Literatur, Altklausuren), zeigt, was erkannt wurde, prüft die Vollständigkeit, schlägt Kapitel und Kompetenzen vor und bereitet für jedes Kapitel ein Authoring-Paket vor.'),
    el('div', { class: 'm-card m-accent', id: 'import' }, el('h2', { class: 'm-h2' }, 'Kurs importieren'),
      el('label', { class: 'm-field', for: 'import-path' }, 'Ordnerpfad (Finder: Ordner wählen, ⌥⌘C kopiert den Pfad)'), path,
      el('label', { class: 'm-field', for: 'import-title' }, 'Titel des Kurses'), title,
      el('div', {}, el('label', { class: 'm-check' }, consent, ' iCloud-Platzhalter in diesem Ordner herunterladen (Ihre Zustimmung; sonst werden sie nur aufgelistet)')),
      el('div', { class: 'm-row' }, run), msg,
      el('p', { class: 'm-note', id: 'import-help' }, 'Nur Ordner in Ihrem Benutzerordner. Mastery liest nur und schreibt nichts in den Kursordner; Inventar, Pakete und Produkte liegen in Ihrer Bibliothek unter courses/. Erneuter Import desselben Ordners erkennt Änderungen.')));
  if (COURSE_ERR) s.append(el('p', { class: 'm-card' }, 'Kursdaten nicht verfügbar (' + COURSE_ERR + '). Bitte Mastery mit `mastery start` öffnen.'));
  for (const c of COURSES || []) s.append(coursePanel(c));
  if (COURSES && !COURSES.length) s.append(el('p', { class: 'm-note', id: 'no-courses' }, 'Noch kein Kurs importiert.'));
  return s;
}
function loadCourses() { return fetch('api/courses', { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))).then(j => { COURSES = j.courses; COURSE_ERR = null; }).catch(e => { COURSES = []; COURSE_ERR = e.message; }); }
function reload(hash) {
  return Promise.all([fetch('library.json', { cache: 'no-store' }).then(r => r.json()).then(async lib => { for (const u of lib.units) for (const tr of u.tracks) tr.data = await fetch(tr.json, { cache: 'no-store' }).then(r => r.json()); LIB = lib; }), loadCourses()])
    .then(() => { const y = window.scrollY; render(); if (hash && location.hash !== hash) location.hash = hash; window.scrollTo(0, y); });
}

/* ------------------------------------------------------------ backup: file export/import and local server copy */
function snapshot() { return { schema: 'mastery-state-v1', saved_at: new Date().toISOString(), origin: location.origin, storage: { [TKEY]: readJSON(TKEY), [PKEY]: readJSON(PKEY), [MKEY]: readJSON(MKEY), [LKEY]: readJSON(LKEY) } }; }
/* File export: the raw stores (re-importable) plus the derived ledger and summary for reading; import ignores `derived`. */
function exportFile() { const snap = snapshot(), led = window.MasteryLedger.buildLedger(snap.storage, LIB); return Object.assign(snap, { derived: { note: 'Abgeleitet aus storage, beim Import ignoriert und neu berechnet.', ledger: led, progress: window.MasteryLedger.summarize(led, LIB) } }); }
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
  const m = o.storage[MKEY]; if (m && m.schema === 1 && m.scenes) { const d = readJSON(MKEY) || { schema: 1, scenes: {} }; d.scenes = d.scenes || {};
    for (const [k, r] of Object.entries(m.scenes)) { if (!r || typeof r.revision !== 'string') continue; const cur = d.scenes[k] = d.scenes[k] || { revision: r.revision, events: [] };
      if (cur.revision !== r.revision) { (d.archived = d.archived || {})[k + '@' + r.revision] = r; continue; }
      merge(cur.events, (r.events || []).filter(e => e && ['predict', 'reveal', 'task_attempt'].includes(e.type)), 't', 'question'); }
    writeJSON(MKEY, d); }
  const l = o.storage[LKEY]; if (l && l.schema === 2 && Array.isArray(l.events)) { const d = readJSON(LKEY) || { schema: 2, created: new Date().toISOString(), events: [], prefs: {} }; d.events = Array.isArray(d.events) ? d.events : [];
    const key = e => [e.t, e.type, e.item || '', e.section || '', e.card || '', e.result || ''].join('|'), have = new Set(d.events.map(key));
    for (const e of l.events) if (e && typeof e === 'object' && typeof e.t === 'string' && typeof e.type === 'string' && Date.parse(e.t) <= Date.now() + 3e5 && !have.has(key(e))) { d.events.push(e); have.add(key(e)); n++; }
    d.events.sort((x, y) => x.t < y.t ? -1 : x.t > y.t ? 1 : 0); writeJSON(LKEY, d); }
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
        el('button', { type: 'button', class: 'ds-btn', id: 'backup-export', onclick: () => { const a = el('a', { href: URL.createObjectURL(new Blob([JSON.stringify(exportFile(), null, 1)], { type: 'application/json' })), download: 'mastery-lernstand-' + new Date().toISOString().slice(0, 10) + '.json' }); document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); } }, 'Als Datei exportieren'),
        el('label', { class: 'ds-btn', for: 'backup-import' }, 'Datei importieren'), file), msg,
      el('p', { class: 'm-note' }, 'Die Sicherung enthält Ihre eigenen Antworten und Diagnosen. Import ergänzt nur; vorhandene Einträge bleiben. Aufgaben in geänderter Fassung übernehmen keinen alten Verlauf.')));
}

/* ------------------------------------------------------------ boot */
let LIB = null;
function route() { const id = (location.hash || '#start').slice(1); for (const v of app.querySelectorAll('.m-view')) v.hidden = v.id !== (['start', 'kurse', 'lernstand', 'tutor', 'sicherung'].includes(id) ? id : 'start');
  for (const a of document.querySelectorAll('.m-nav a')) a.setAttribute('aria-current', a.getAttribute('href') === '#' + id ? 'page' : 'false'); }
function render() { app.replaceChildren(viewStart(LIB), viewCourses(), viewProgress(LIB), viewTutor(LIB), viewBackup()); route(); app.dataset.ready = '1'; }
window.addEventListener('hashchange', route);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && LIB) { render(); postState(document.getElementById('backup-status')); } });
reload().then(() => postState(document.getElementById('backup-status'))).catch(e => { app.replaceChildren(el('p', { class: 'm-card' }, 'Bibliothek nicht lesbar (' + e.message + '). Bitte mit `mastery start` öffnen – nicht als Datei.')); });
})();
