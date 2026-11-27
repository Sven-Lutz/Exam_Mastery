"""Build the reference visualisations (deterministic, offline, no model call).
Usage: python scripts/build_reference_scenes.py <out_dir> [<cash-flow lab json of a delivered chapter>] [<fonts dir>]
Without a chapter lab the cash-flow scene uses the engine's test data (labelled as such).
The collection is an overview, not a course: its labs record attempts under the context 'referenz', so they never
appear as progress of a chapter, and the start page shows the experiments instead of a progress table."""
import json
import shutil
import sys
import time
from pathlib import Path

from exam_mastery.labs import build as B

out = Path(sys.argv[1]); t0 = time.perf_counter()
fonts_src = Path(sys.argv[3]) if len(sys.argv) > 3 else None
if fonts_src and fonts_src.is_dir():
    (out / 'assets' / 'fonts').mkdir(parents=True, exist_ok=True)
    for f in fonts_src.glob('*.woff2'):
        shutil.copy2(f, out / 'assets' / 'fonts' / f.name)
fonts = (out / 'assets' / 'fonts').is_dir()
specs = [B.mlp_spec(), B.chord_spec()]
if len(sys.argv) > 2 and sys.argv[2]:
    s = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); m = s['model']
    specs.append(B.cashflow_spec(s['id'], s['title'], s['kc_ids'], s['sources'], m['orders'], m['delay'], m['cost'], m['invest'],
                                 m.get('start_cash', 0), m.get('unit', 'k€'), s.get('course', '')))
else:
    specs.append(B.cashflow_spec('demo/cashflow', 'Liquiditätsplanung (Testdaten)', ['demo/liquidity'], ['Testdaten der Engine'],
                                 [0, 100, 180, 190, 210, 230, 250, 270], 5, [102, 122, 172, 152, 242, 152, 162, 172], [200, 500, 300, 140]))
# editorial titles for the overview (the lab pages keep their full titles)
EDIT = {'mlp': ('Wie ein Netz aus einem Fehler lernt', 'Vorwärtsrechnung, Verlust, Kettenregel und ein Gradientenschritt – jede Zahl erscheint an ihrem Ort im Netz.'),
        'chord': ('Rechtecke auf einer geschlossenen Kurve', 'Jedes Punktpaar wird zu einem Punkt im Raum. Treffen sich zwei Paare im selben Punkt, bilden ihre vier Punkte ein Rechteck.'),
        'cashflow': ('Warum Wachstum Geld kostet', 'Verkäufe werden erst nach dem Zahlungsziel zu Geld. Der tiefste Punkt der Liquiditätskurve ist der Finanzierungsbedarf.')}
from exam_mastery.learning import tracks as TR, render as TRR
ent = None
if len(sys.argv) > 2 and sys.argv[2]:
    _m = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))['model']; ent = {k: _m[k] for k in ('orders', 'delay', 'cost', 'invest')}
CASE = {'machine_learning': 'Diagnosefall: Faktor x₁ im Gradienten vergessen – der Pfad im Netz wird markiert.',
        'business_economics': 'Diagnosefall: Endsaldo statt Tiefpunkt – Kontrast und neues Zahlungsziel.',
        'mathematics': 'Diagnosefall: Beweis ohne die Voraussetzung „gleich lang“ – Gegenbeispiel Parallelogramm.'}
CASE_BY_TRACK = {'ai/attention-track': 'Diagnosefall: Skalierung mit √d_k vergessen oder Maske erst nach Softmax – die Gewichte der Fehlrechnung werden gezeigt.'}
DOM = {'machine_learning': 'Machine Learning', 'business_economics': 'Finanzierung', 'mathematics': 'Mathematik'}
track_items = []
for t in TR.all_tracks(ent):
    pth = TRR.write(t, out / 'lernstrecken', context='referenz', lab_href='../labs/' + t['lab'].replace('/', '__') + '.html', fonts='../assets/fonts' if fonts else None)
    track_items.append({'href': 'lernstrecken/' + pth.name, 'title': t['title'], 'domain': DOM[t['domain']], 'case': CASE_BY_TRACK.get(t['id'], CASE[t['domain']])})
items = []
for sp in specs:
    p = B.render(sp, out / 'labs', context='referenz', fonts='../assets/fonts' if fonts else None, back_label='Alle Experimente')
    t, x = EDIT.get(sp['model']['kind'], (None, None))
    items.append({'spec': sp, 'href': 'labs/' + p.name, 'title': t, 'teaser': x})
B.gallery(out, items, 'Exam Mastery · Labor', 'Referenzsammlung mathematischer Experimente',
          'Mathematik, die man <em>beim Rechnen</em> sieht.',
          'Drei Experimente und drei adaptive Lernstrecken. In den Experimenten spielt jedes Objekt eine Rolle in einer Rechnung: Gewichte, Punkte, Zahlungen. '
          'Bild und Formel sind gekoppelt – jede Zahl stammt aus demselben geprüften Modell wie die Engine.',
          notes=['Jede Visualisierung rechnet mit demselben Referenzmodell wie die Engine (Python); der Browser spiegelt es und wird bei jedem Build dagegen getestet.',
                 'Die Rechtecksuche ist numerische Exploration mit sichtbarem Restfehler – sie veranschaulicht einen Satz, sie beweist ihn nicht.',
                 'Alles läuft lokal und offline. Versuche in diesen Experimenten werden getrennt von Kursen gespeichert und nie als Kursfortschritt gezählt.'],
          version='v0.19', fonts='assets/fonts' if fonts else None, tracks=track_items)
print(json.dumps({'out': str(out), 'labs': [i['href'] for i in items], 'seconds': round(time.perf_counter() - t0, 3)}, ensure_ascii=False))
