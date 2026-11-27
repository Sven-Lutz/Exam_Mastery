'use strict';
const $ = selector => document.querySelector(selector);
let deck;
function list(selector, items) {
  $(selector).replaceChildren(...items.map(text => {
    const li = document.createElement('li');
    li.textContent = text;
    return li;
  }));
}
function report(data) {
  $('#total').textContent = deck.cards.length + ' Karten · ' + data.events.length + ' Rückmeldungen';
  list('#counts', Object.entries(data.counts).map(([kind, n]) => kind + ': ' + n));
  list('#affected', data.affected.map(cardLabel));
}
function cardLabel(card) { return card.key + ' · Karte ' + (card.ordinal + 1); }
function show() {
  const card = deck.cards[$('#card').selectedIndex];
  $('iframe').src = deck.package + '/' + card.prefix + '-' + $('#side').value + '-light.html';
}
async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || 'Abruf fehlgeschlagen');
  return data;
}
function status(text) { $('[role=status]').textContent = text; }
async function load() {
  deck = await request('data');
  for (const card of deck.cards) $('#card').add(new Option(cardLabel(card)));
  for (const kind of deck.kinds) $('#kind').add(new Option(kind));
  report(deck.report);
  if (deck.cards.length) { show(); $('button').disabled = false; }
}
$('#side').onchange = show;
$('#card').onchange = show;
$('form').onsubmit = async event => {
  event.preventDefault();
  const card = deck.cards[$('#card').selectedIndex];
  const [, , slug, chapter] = location.pathname.split('/');
  $('button').disabled = true;
  try {
    report(await request('/api/courses/' + slug + '/chapters/' + chapter + '/feedback', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ package: deck.package, key: card.key, ordinal: card.ordinal,
        kind: $('#kind').value, text: $('#text').value })
    }));
    $('#text').value = '';
    status('Feedback lokal gespeichert.');
  } catch (error) { status(error.message); }
  finally { $('button').disabled = false; }
};
load().catch(error => status(error.message));
