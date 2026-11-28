/* Mastery evidence ledger (mastery-ledger-v1) and progress summary (mastery-progress-v1). Pure functions, no DOM, no
   network, no score. Mirrors exam_mastery/mastery/ledger.py; tests require equal output for equal input.
   Reads (never writes) the learner stores em-tutor-v1, em-practice-v1, em-motion-v1, em-learn-v2. State and evidence
   basis per competency come from the tested policy runtime (EMT.kcStatus, EMT.kcEvidenceBasis in em_tutor.js). */
(() => {
'use strict';
const EMT = window.EMT;
const LEDGER_SCHEMA = 'mastery-ledger-v1', PROGRESS_SCHEMA = 'mastery-progress-v1', RULES = 'mastery-ledger-rules-v1';
const STORES = ['em-tutor-v1', 'em-practice-v1', 'em-motion-v1', 'em-learn-v2'];
const HELP = ['hint', 'solution', 'tutor', 'guided', 'support'];          // policy.ASSIST_EVENTS
const MIRROR = { attempt: 'attempt', hint: 'hint', solution_reveal: 'solution', tutor_brief: 'tutor', guided_help: 'guided' };
const MIRROR_WINDOW_MS = 2000, FUTURE_SKEW_MS = 5 * 60000, GAP_MS = 20 * 3600000, HELP_WINDOW_MS = 20 * 3600000;
const SOURCES = ['deterministic', 'agent_judgement', 'self_report'];
const LEARN_KIND = { attempt: 'attempt', hint: 'help', solution: 'help', tutor: 'help', section_open: 'view', card: 'self_rating', exam_start: 'exam', exam_submit: 'exam', exam_self_score: 'exam' };
const MOTION_KIND = { predict: 'prediction', reveal: 'reveal', task_attempt: 'mission' };
const FIELDS = ['id', 'store', 'record', 'list', 'i', 't', 'at', 't_quality', 'archived', 'product', 'course', 'chapter', 'unit', 'task', 'task_type', 'competency', 'help_kc', 'type', 'kind', 'help', 'result', 'assist', 'source', 'role', 'state_input', 'note'];
const TS = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?(Z|[+-]\d{2}:\d{2})?)?$/;
const NOTE_UNKNOWN = 'unbekannter Ereignistyp – unverändert übernommen, zählt nirgends';
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const str = v => typeof v === 'string' ? v : null;
const dict = v => v && typeof v === 'object' && !Array.isArray(v) ? v : {};
const list = v => Array.isArray(v) ? v : [];
const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const sortedEntries = o => Object.keys(o).sort(cmp).map(k => [k, o[k]]);

/* ------------------------------------------------------------ time (same rules as ledger.py) */
function stamp(t, nowMs) {
  if (typeof t !== 'string') return [null, 'missing'];
  const m = TS.exec(t); if (!m) return [null, 'invalid'];
  const [, y, mo, d, hh, mi, ss, frac, tz] = m, Y = +y, MO = +mo, D = +d, H = +(hh || 0), MI = +(mi || 0), S = +(ss || 0);
  if (Y < 1 || MO < 1 || MO > 12 || D < 1 || H > 23 || MI > 59 || S > 59) return [null, 'invalid'];
  const dt = new Date(0); dt.setUTCFullYear(Y, MO - 1, D);
  if (dt.getUTCFullYear() !== Y || dt.getUTCMonth() !== MO - 1 || dt.getUTCDate() !== D) return [null, 'invalid'];
  dt.setUTCHours(H, MI, S, +((frac || '0').slice(0, 3).padEnd(3, '0')));
  let ms = dt.getTime();
  if (tz && tz !== 'Z') { const off = (+tz.slice(1, 3) * 60 + +tz.slice(4, 6)) * 60000; ms = tz[0] === '+' ? ms - off : ms + off; }
  if (ms > nowMs + FUTURE_SKEW_MS) return [ms, 'future'];
  return [ms, hh !== undefined ? 'exact' : 'date_only'];
}
const iso = ms => new Date(ms).toISOString();
function nowMsOf(now) { if (now === undefined || now === null) return Date.now(); const [ms] = stamp(now, Infinity); if (ms === null) throw new Error('now must be an ISO timestamp'); return ms; }
const roleOf = r => r === undefined || r === null ? null : r === 'retest' ? 'retest' : (r === 'similar' || r === 'transfer') ? 'evidence' : 'practice';
const where = u => u ? { unit: u.slug, course: (u.course || {}).slug || null, chapter: (u.chapter || {}).id || null } : { unit: null, course: null, chapter: null };

function index(catalog) {
  const tracks = {}, units = {};
  for (const u of (catalog || {}).units || []) {
    if (!has(units, u.practice_store.unit_id)) units[u.practice_store.unit_id] = u;
    for (const tr of u.tracks || []) if (tr.data && !has(tracks, tr.store_key)) tracks[tr.store_key] = [u, tr];
  }
  return [tracks, units];
}

/* ------------------------------------------------------------ ledger */
function Acc(nowMs) {
  const events = [], stores = {};
  return {
    nowMs, events, stores,
    store(name, present) { return (stores[name] = { store: name, present, records: 0, read: 0, included: 0, excluded: {} }); },
    exclude(name, reason) { const s = stores[name]; s.read++; s.excluded[reason] = (s.excluded[reason] || 0) + 1; },
    add(kw) {
      const [ms, q] = stamp(kw.t, nowMs), ev = {};
      for (const k of FIELDS) ev[k] = kw[k] === undefined ? null : kw[k];
      ev.t = str(kw.t); ev.at = ms !== null ? iso(ms) : null; ev.t_quality = q; ev.archived = !!kw.archived; ev.state_input = false;
      ev._ms = ms; ev.id = kw.store + '#' + kw.record + '#' + kw.list + '#' + kw.i;
      const s = stores[kw.store]; s.read++; s.included++; events.push(ev); return ev;
    },
  };
}
function policyEvent(acc, store, record, lst, i, e, T, w, product, archived, scopeOk) {
  const typ = e.type, task = str(e.task), td = task && has(T, task) ? T[task] : null;
  const kind = typ === 'attempt' ? 'attempt' : HELP.includes(typ) ? 'help' : 'unknown';
  const diag = e.diagnosis && typeof e.diagnosis === 'object' && !Array.isArray(e.diagnosis) ? e.diagnosis : null;
  const result = diag ? str(diag.result) : typ === 'guided' ? str(e.result) : null;
  const helpKc = kind === 'help' ? str(e.kc) : null;
  let source = null, taskType = (td || {}).type || null;
  if (kind === 'attempt') { source = result === 'unverified' ? 'unjudged' : result ? 'deterministic' : null; taskType = (td || {}).type || (diag ? str(diag.method) : null); }
  else if (kind === 'help') source = SOURCES.includes(e.source) ? e.source : typ === 'tutor' ? 'agent_judgement' : 'deterministic';
  let note = null;
  if (kind === 'unknown') note = NOTE_UNKNOWN;
  else if (!scopeOk) note = archived ? 'frühere Aufgabenfassung – nur in der Zeitleiste' : 'Übungsstrecke nicht in der Bibliothek – nur in der Zeitleiste';
  const ev = acc.add(Object.assign({ store, record, list: lst, i, t: e.t, archived, product }, w, {
    task, task_type: taskType, competency: helpKc || (td || {}).kc_id || null, help_kc: helpKc, type: typ, kind,
    help: kind === 'help' ? typ : null, result, source, role: roleOf((td || {}).role), note }));
  ev._task_kc = (td || {}).kc_id || null; ev._valid_attempt = kind === 'attempt' && result !== null;
  return ev;
}
function assist(evs) {
  const seq = evs.filter(e => (e.kind === 'attempt' || e.kind === 'help') && (e.t_quality === 'exact' || e.t_quality === 'date_only'));
  seq.forEach((e, j) => {
    if (e.kind !== 'attempt') return;
    const prev = seq.slice(0, j), kc = e._task_kc;
    const taskHelp = prev.some(p => p.kind === 'help' && p.task === e.task);
    const kcHelp = kc !== null && prev.some(p => p.kind === 'help' && (p._task_kc === kc || p.help_kc === kc) && e._ms - p._ms <= HELP_WINDOW_MS);
    e.assist = taskHelp || kcHelp ? 'assisted' : 'unassisted';
  });
}
function markState(evs, scopeOk, T) {
  for (const e of evs) e.state_input = !!(scopeOk && !e.archived && (e.t_quality === 'exact' || e.t_quality === 'date_only')
    && ((e.kind === 'attempt' && e._valid_attempt && e.task !== null && has(T, e.task) && e.result !== 'unverified')
      || (e.kind === 'help' && ((e.task !== null && has(T, e.task)) || e.help_kc))));
}
function mirrorMatches(policyEvs, mirror) {
  const used = new Set(), dup = new Set();
  for (const [i, m] of mirror) {
    const typ = has(MIRROR, m.type) ? MIRROR[m.type] : null, [ms] = stamp(m.at, Infinity);
    if (!typ || ms === null) continue;
    for (let k = 0; k < policyEvs.length; k++) {
      const p = policyEvs[k];
      if (used.has(k) || p.type !== typ || p.task !== str(m.task_id) || p._ms === null) continue;
      if (Math.abs(p._ms - ms) <= MIRROR_WINDOW_MS) { used.add(k); dup.add(i); break; }
    }
  }
  return dup;
}

function buildLedger(storage, catalog, now) {
  storage = storage || {};
  const nowMs = nowMsOf(now), acc = Acc(nowMs), [tracks, units] = index(catalog);
  const isObj = v => !!v && typeof v === 'object' && !Array.isArray(v);

  const tutor = storage['em-tutor-v1'];
  let s = acc.store('em-tutor-v1', isObj(tutor));
  for (const [key, rec] of sortedEntries(dict(dict(tutor).tracks))) {
    s.records++;
    const [u, tref] = has(tracks, key) ? tracks[key] : [null, null];
    const T = tref ? Object.fromEntries(tref.data.tasks.map(t => [t.id, t])) : {};
    const evs = [];
    list(dict(rec).events).forEach((e, i) => {
      if (!isObj(e) || typeof e.type !== 'string') { acc.exclude('em-tutor-v1', 'malformed'); return; }
      if (e.type === 'decision') { acc.exclude('em-tutor-v1', 'engine_decision'); return; }
      evs.push(policyEvent(acc, 'em-tutor-v1', key, 'events', i, e, T, where(u), 'workbench', false, !!tref));
    });
    assist(evs); markState(evs, !!tref, T);
  }

  const practice = storage['em-practice-v1'];
  s = acc.store('em-practice-v1', isObj(practice));
  if (isObj(practice)) {
    const recs = sortedEntries(dict(practice.units)).map(([k, r]) => [k, r, false]).concat(sortedEntries(dict(practice.archived)).map(([k, r]) => [k, r, true]));
    for (const [key, rec, archived] of recs) {
      s.records++;
      if (!isObj(rec)) continue;
      const uid = archived && key.lastIndexOf('@') >= 0 ? key.slice(0, key.lastIndexOf('@')) : key, u = has(units, uid) ? units[uid] : null;
      const stale = !!u && !archived && rec.assessment_revision !== u.practice_store.assessment_revision, arch = archived || stale;
      const T = u ? Object.fromEntries(u.adaptive_track.tasks.map(t => [t.id, t])) : {}, scopeOk = !!u && !arch;
      const evs = [];
      list(rec.policy).forEach((e, i) => {
        if (!isObj(e) || typeof e.type !== 'string') { acc.exclude('em-practice-v1', 'malformed'); return; }
        evs.push(policyEvent(acc, 'em-practice-v1', key, 'policy', i, e, T, where(u), 'explorable', arch, scopeOk));
      });
      assist(evs); markState(evs, scopeOk, T);
      const mirror = [];
      list(rec.events).forEach((m, i) => { if (!isObj(m) || typeof m.type !== 'string') { acc.exclude('em-practice-v1', 'malformed'); return; } mirror.push([i, m]); });
      const dup = mirrorMatches(evs, mirror);
      for (const [i, m] of mirror) {
        if (dup.has(i)) { acc.exclude('em-practice-v1', 'mirror_duplicate'); continue; }
        const typ = has(MIRROR, m.type) ? MIRROR[m.type] : null, task = str(m.task_id), td = task && has(T, task) ? T[task] : null;
        const kind = typ === 'attempt' ? 'attempt' : HELP.includes(typ) ? 'help' : 'unknown';
        acc.add(Object.assign({ store: 'em-practice-v1', record: key, list: 'events', i, t: m.at, archived: arch, product: 'explorable' }, where(u), {
          task, task_type: null, competency: (td || {}).kc_id || null, type: m.type, kind, help: kind === 'help' ? typ : null,
          source: kind === 'attempt' ? 'unjudged' : kind === 'unknown' ? null : typ === 'tutor' ? 'agent_judgement' : 'deterministic',
          role: roleOf((td || {}).role),
          note: 'nur im Aktionsprotokoll (em-practice-evidence-v1), ohne Gegenstück im Entscheidungsprotokoll – nur in der Zeitleiste' }));
      }
    }
  }

  const motion = storage['em-motion-v1'];
  s = acc.store('em-motion-v1', isObj(motion));
  if (isObj(motion)) {
    const recs = sortedEntries(dict(motion.scenes)).map(([k, r]) => [k, r, false]).concat(sortedEntries(dict(motion.archived)).map(([k, r]) => [k, r, true]));
    for (const [key, rec, archived] of recs) {
      s.records++;
      list(dict(rec).events).forEach((e, i) => {
        if (!isObj(e) || typeof e.type !== 'string') { acc.exclude('em-motion-v1', 'malformed'); return; }
        const kind = has(MOTION_KIND, e.type) ? MOTION_KIND[e.type] : 'unknown';
        let result = null;
        if (kind === 'prediction') result = e.correct === true ? 'correct' : e.correct === false ? 'incorrect' : null;
        else if (kind === 'mission') result = e.met === true ? 'met' : e.met === false ? 'not_met' : null;
        else if (kind === 'reveal') result = e.skipped === true ? 'skipped_prediction' : null;
        acc.add({ store: 'em-motion-v1', record: key, list: 'events', i, t: e.t, archived, product: 'motion', unit: null, course: null, chapter: null,
          task: str(e.question) || str(e.mission) || str(e.step), type: e.type, kind, result,
          source: ['correct', 'incorrect', 'met', 'not_met'].includes(result) ? 'deterministic' : null,
          role: kind !== 'unknown' ? 'practice' : null, note: kind !== 'unknown' ? 'Lernhandlung, kein Kompetenznachweis' : NOTE_UNKNOWN });
      });
    }
  }

  const learn = storage['em-learn-v2'];
  s = acc.store('em-learn-v2', isObj(learn));
  if (isObj(learn)) {
    const helped = new Set(), records = new Set();
    list(learn.events).forEach((e, i) => {
      if (!isObj(e) || typeof e.type !== 'string') { acc.exclude('em-learn-v2', 'malformed'); return; }
      const record = 'chapter:' + (str(e.chapter) || '?'); records.add(record);
      const kind = has(LEARN_KIND, e.type) ? LEARN_KIND[e.type] : 'unknown', item = str(e.item), mode = e.mode;
      const source = kind === 'attempt' ? (mode === 'number' ? 'deterministic' : mode === 'self' ? 'self_report' : null)
        : (kind === 'self_rating' || e.type === 'exam_self_score') ? 'self_report' : kind === 'help' ? 'deterministic' : null;
      const ev = acc.add({ store: 'em-learn-v2', record, list: 'events', i, t: e.t, product: 'chapter_app', unit: null, course: null, chapter: null,
        task: item || str(e.card) || str(e.section), type: e.type, kind, help: kind === 'help' ? e.type : null, result: str(e.result), source,
        note: kind !== 'unknown' ? 'Kapitel-App: ohne Kompetenzzuordnung in Mastery – nur in der Zeitleiste' : NOTE_UNKNOWN });
      const hk = record + '\u0000' + item;
      if (kind === 'help' && item) helped.add(hk);
      if (kind === 'attempt') ev.assist = helped.has(hk) ? 'assisted' : 'unassisted';
    });
    s.records = records.size;
  }

  const order = Object.fromEntries(STORES.map((n, k) => [n, k]));
  acc.events.sort((a, b) => ((a._ms === null) - (b._ms === null)) || ((a._ms === null ? 0 : a._ms) - (b._ms === null ? 0 : b._ms))
    || (order[a.store] - order[b.store]) || cmp(a.record, b.record) || cmp(a.list, b.list) || (a.i - b.i));
  return { schema: LEDGER_SCHEMA, rules: RULES, now: iso(nowMs), stores: STORES.map(n => acc.stores[n]),
    events: acc.events.map(e => Object.fromEntries(FIELDS.map(k => [k, e[k]]))) };
}

/* ------------------------------------------------------------ progress summary */
function scopes(catalog) {
  const out = [];
  for (const u of (catalog || {}).units || []) {
    for (const tr of u.tracks || []) if (tr.data) out.push({ scope: 'workbench:' + tr.store_key, product: 'workbench', store: 'em-tutor-v1', record: tr.store_key, unit: u, track: tr.data, labels: {}, title: tr.label || tr.data.title });
    out.push({ scope: 'explorable:' + u.practice_store.unit_id, product: 'explorable', store: 'em-practice-v1', record: u.practice_store.unit_id, unit: u, track: u.adaptive_track,
      labels: Object.fromEntries((u.competencies || []).map(c => [c.id, c.label])), title: u.title });
  }
  const seen = new Set();
  return out.filter(sc => !seen.has(sc.scope) && seen.add(sc.scope));
}
function raw(e) {
  if (e.kind === 'attempt') return { type: 'attempt', task: e.task, t: e.at, diagnosis: { result: e.result } };
  const r = { type: e.type, task: e.task, t: e.at }; if (e.help_kc) r.kc = e.help_kc; return r;
}
function summarize(ledger, catalog, now) {
  const nowIso = now === undefined || now === null ? ledger.now : iso(nowMsOf(now)), byRecord = {};
  for (const e of ledger.events) (byRecord[e.store + '\u0000' + e.record] = byRecord[e.store + '\u0000' + e.record] || []).push(e);
  const comps = [];
  for (const sc of scopes(catalog)) {
    const evs = (byRecord[sc.store + '\u0000' + sc.record] || []).filter(e => (e.list !== 'events' || sc.store === 'em-tutor-v1') && !e.archived).slice().sort((a, b) => a.i - b.i);
    const state = evs.filter(e => e.state_input), rawEv = state.map(raw), track = sc.track, types = {};
    for (const e of state) if (e.kind === 'attempt' && e.task_type && !has(types, e.task)) types[e.task] = e.task_type;
    const aug = Object.assign({}, track, { tasks: track.tasks.map(t => Object.assign({}, t, { type: t.type || types[t.id] || 'open' })) });
    const status = EMT.kcStatus(aug, rawEv, nowIso), basis = EMT.kcEvidenceBasis(aug, rawEv), u = sc.unit;
    for (const kc of track.kcs) {
      const kid = kc.id;
      const att = evs.filter(e => e.kind === 'attempt' && e.competency === kid && e.result !== null && e.result !== 'invalid' && e.assist !== null);
      const refs = { unassisted: att.filter(e => e.assist === 'unassisted').map(e => e.id), assisted: att.filter(e => e.assist === 'assisted').map(e => e.id),
        unverified: att.filter(e => e.result === 'unverified').map(e => e.id) };
      const seen = new Set(), retries = [];
      for (const e of att) { if (seen.has(e.task)) retries.push(e.id); seen.add(e.task); }
      refs.retries = retries;
      for (const h of HELP) refs[h] = evs.filter(e => e.kind === 'help' && e.help === h && e.competency === kid).map(e => e.id);
      const ind = state.filter(e => e.kind === 'attempt' && e.competency === kid && e.result === 'correct' && e.assist === 'unassisted');
      refs.independent = ind.map(e => e.id);
      const indT = ind.map(e => [stamp(e.at, Infinity)[0], e.task, e.id]).sort((a, b) => (a[0] - b[0]) || cmp(a[1], b[1]) || cmp(a[2], b[2]));
      let delayed = null;
      for (const [t2, k2, id2] of indT) {
        const earlier = indT.filter(([t1, k1]) => k1 !== k2 && t2 - t1 >= GAP_MS).map(x => x[0]);
        if (earlier.length) { delayed = { at: iso(t2), after_hours: Math.floor((t2 - Math.min(...earlier)) / 3600000), ref: id2 }; break; }
      }
      comps.push(Object.assign({ scope: sc.scope, product: sc.product, scope_title: sc.title }, where(u), {
        competency: kid, label: sc.labels[kid] || kc.label || kid, status: status[kid], basis: basis[kid],
        counts: Object.fromEntries(Object.entries(refs).map(([k, v]) => [k, v.length])),
        first_independent: indT.length ? iso(indT[0][0]) : null, latest_independent: indT.length ? iso(indT[indT.length - 1][0]) : null,
        delayed, refs }));
    }
  }
  const rank = { production: 2, recognition_only: 1, none: 0 }, chapters = [];
  for (const u of (catalog || {}).units || []) {
    const items = {}, order = [];
    for (const c of comps) {
      if (c.unit !== u.slug) continue;
      if (!has(items, c.competency)) { items[c.competency] = { competency: c.competency, label: c.label, basis: 'none', attempted: false, scopes: [] }; order.push(c.competency); }
      const it = items[c.competency]; it.scopes.push(c.scope);
      if (rank[c.basis] > rank[it.basis]) it.basis = c.basis;
      it.attempted = it.attempted || (c.counts.unassisted + c.counts.assisted) > 0;
    }
    const rows = order.map(k => items[k]);
    chapters.push(Object.assign(where(u), { title: u.title, items: rows,
      with_production: rows.filter(r => r.basis === 'production').map(r => r.competency), without_production: rows.filter(r => r.basis !== 'production').map(r => r.competency) }));
  }
  const motion = {};
  for (const e of ledger.events) {
    if (e.store !== 'em-motion-v1' || e.archived) continue;
    const m = motion[e.record] = motion[e.record] || { scene: e.record, predictions: [], predictions_correct: [], reveals: [], missions: [], missions_met: [] };
    if (e.kind === 'prediction') { m.predictions.push(e.id); if (e.result === 'correct') m.predictions_correct.push(e.id); }
    else if (e.kind === 'reveal') m.reveals.push(e.id);
    else if (e.kind === 'mission') { m.missions.push(e.id); if (e.result === 'met') m.missions_met.push(e.id); }
  }
  return { schema: PROGRESS_SCHEMA, rules: RULES, now: nowIso, competencies: comps, chapters, motion: Object.keys(motion).sort(cmp).map(k => motion[k]) };
}

window.MasteryLedger = { buildLedger, summarize, stamp, LEDGER_SCHEMA, PROGRESS_SCHEMA, RULES, STORES };
})();
