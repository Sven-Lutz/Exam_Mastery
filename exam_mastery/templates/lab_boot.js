'use strict';
// =====================================================================================
// Start
// =====================================================================================
const LABS = [attention, typeof crfLab !== 'undefined' && crfLab, typeof rnnLab !== 'undefined' && rnnLab, typeof spanLab !== 'undefined' && spanLab].filter(Boolean);
function boot() {
  const m = location.hash.match(/lab=([\w-]+)/);
  let cur = LABS.find(l => m && l.id === m[1]) || LABS[0];
  if (store.get('reduced', false)) document.body.classList.add('reduced');
  const nav = h('nav', {'aria-label': 'Labore'});
  const wrap = h('div', {class: 'lab-wrap'});
  const rm = h('button', {'aria-pressed': String(document.body.classList.contains('reduced')), onclick: () => { document.body.classList.toggle('reduced'); const on = document.body.classList.contains('reduced'); rm.setAttribute('aria-pressed', String(on)); store.set('reduced', on); }}, 'Bewegung reduzieren');
  const share = h('button', {onclick: () => { try { navigator.clipboard.writeText(location.href).then(() => toast('Link mit exaktem Zustand kopiert')); } catch (e) { toast('Kopieren nicht möglich – Adresszeile verwenden'); } }}, 'Zustand teilen');
  const top = h('header', {class: 'lab-top'}, h('span', {class: 'brand'}, 'Interaktives Labor'), h('span', {class: 'mute'}, UNIT.chapter || ''), nav,
    h('span', {class: 'right'}, rm, share, h('a', {class: 'btn', href: 'index.html'}, '← Lernplattform')));
  document.body.replaceChildren(top, wrap);
  function open(lab, keepHash) {
    cur = lab;
    if (!keepHash) history.replaceState(null, '', '#lab=' + lab.id);
    nav.replaceChildren(...LABS.map(l => h('button', {'aria-current': l === cur ? 'page' : false, onclick: () => open(l)}, l.title)));
    const sh = Shell(lab);
    wrap.replaceChildren(h('div', {class: 'lab-head'}, h('h1', {}, lab.title), h('p', {html: lab.intro})), h('div', {class: 'lab-grid'}, sh.stage, sh.side));
    typeset(wrap);
    document.body.dataset.ready = '1';
  }
  open(cur, true);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
