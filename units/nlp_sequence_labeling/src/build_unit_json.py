"""Authoring source for units/nlp_sequence_labeling/unit.json (run: python units/nlp_sequence_labeling/src/build_unit_json.py).

TeX is written in raw strings; the generated JSON is the build input. Numbers in solutions are recomputed by
exam_mastery.reference_unit.verify; a mismatch fails the build.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v5_attention as V5  # noqa: E402
import v5_exam_worked as V5W  # noqa: E402
import v7_tasks as V7  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / 'unit.json'
L3 = ['O', 'B-LOC', 'I-LOC']
L7 = ['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC']

KCS = {
    'spans': 'Spannenkodierung (IO, BIO, BILOU)',
    'birnn': 'Abhängigkeitsbereich und BiRNN',
    'attention': 'Self-Attention',
    'position': 'Positionsinformation',
    'decoding': 'Labelabhängigkeiten und Viterbi',
    'prf': 'Precision, Recall, F1',
    'prf-edge': 'Grenzfälle mit Nenner 0',
    'prf-level': 'Phrasen- vs. Token-Zählung',
    'micro-macro': 'Micro- und Macro-Mittelung',
}

T = []  # workbook tasks
T.append(dict(id='S1', stage='independent', kc='spans', title='BIO lesen und Labels zählen',
    prompt=r'(a) Wie viele Labels braucht BILOU für \(K=5\) Entitätstypen? (b) Welche Spannen liest <code>conlleval</code> aus der Folge <code>O I-LOC I-LOC B-LOC</code> über den Wörtern \(w_1\dots w_4\)?',
    givens={'K': 5, 'scheme': 'BILOU'},
    answers=[dict(label='(a) Anzahl Labels', type='num', check='labels:BILOU:5', diagnoses=[dict(value='11', msg=r'Das ist BIO (\(2K+1\)). BILOU hat vier Labels je Typ: \(4K+1\).')]),
             dict(label='(b) Spannen', type='choice', options=[r'\([w_2\,w_3]\)LOC und \([w_4]\)LOC', r'nur \([w_4]\)LOC – ein I am Anfang ist ungültig und wird verworfen', r'\([w_2\,w_3\,w_4]\)LOC'], correct=0,
                  diagnoses=[dict(value='1', msg=r'<code>conlleval</code> verwirft nichts: Ein <code>I-X</code>, das keine Spanne fortsetzt, eröffnet eine neue.'), dict(value='2', msg=r'<code>B-LOC</code> beginnt immer eine neue Spanne.')])],
    hints=[r'BILOU: B, I, L, U je Typ, dazu O.', r'Lesen Sie Wort für Wort: Wo beginnt eine Spanne?'],
    solution=r'(a) \(4\cdot5+1=21\). (b) \(w_1\) ist O. \(w_2\) ist <code>I-LOC</code> ohne Vorgänger desselben Typs und eröffnet daher eine Spanne, die \(w_3\) fortsetzt. \(w_4\) ist <code>B-LOC</code> und beginnt eine neue: \([w_2\,w_3]\)LOC und \([w_4]\)LOC.',
    rubric=['4K+1 (1 P.)', 'I ohne Vorgänger eröffnet Spanne (1 P.)', 'B beginnt neue Spanne (1 P.)']))
T.append(dict(id='G1', stage='guided', kc='birnn', title='Selbst weiterrechnen: Position 2',
    prompt=r'Berechnen Sie im Experiment für „Washington <b>state</b>“ den Vorwärtszustand \(h^{\rightarrow}_2=\tanh(0{,}5\,h^{\rightarrow}_1+e_2)\) mit \(h^{\rightarrow}_1=(0{,}7616;\,0)\) und \(e_2=(0,-1)\). Vier Nachkommastellen.',
    answers=[dict(label='erste Komponente', type='num', check='toy:fw:state:2:0', diagnoses=[dict(value='0.7616', msg=r'Das ist \(h^{\rightarrow}_1\). Der alte Zustand wird mit 0,5 multipliziert: \(\tanh(0{,}5\cdot0{,}7616+0)\).')]),
             dict(label='zweite Komponente', type='num', check='toy:fw:state:2:1', diagnoses=[dict(value='0.7616', msg=r'Vorzeichen: \(e(\text{state})=(0,-1)\), und \(\tanh(-1)=-\tanh(1)\).')])],
    hints=[r'Komponentenweise: \(0{,}5\cdot(0{,}7616;\,0)+(0;\,-1)=(0{,}3808;\,-1)\).', r'Dann \(\tanh(0{,}3808)\) und \(\tanh(-1)\).'],
    solution=r'\(0{,}5\,h^{\rightarrow}_1+e_2=(0{,}3808;\,-1)\), also \(h^{\rightarrow}_2=(\tanh 0{,}3808;\ \tanh(-1))=(0{,}3634;\,-0{,}7616)\). Mit „signed“: \((0{,}3634;\,+0{,}7616)\). Ab Position 2 unterscheiden sich die Sätze – dort hat der Vorwärtszustand das unterschiedliche Wort gelesen.',
    rubric=['Dämpfung 0,5 auf den alten Zustand', 'Komponentenweise tanh', 'Deutung: Unterschied erst ab Position 2']))
T.append(dict(id='W1', stage='worked', kc='birnn', title='Durchgerechnet: Parameter eines CoNLL-Taggers',
    prompt=r'BiRNN-Tagger für CoNLL-2003 (vier Typen PER, ORG, LOC, MISC; Vorlesung PDF-S. 11) in BIO-Kodierung, Einbettung \(d=100\), Zustand \(d_h=128\) je Richtung. Wie viele Parameter hat er ohne Einbettungsmatrix?',
    givens={'d': 100, 'dh': 128, 'K': 4},
    steps=[dict(s=r'\(|\mathcal L|=2K+1=2\cdot4+1=9\)', why='Je Typ ein B- und ein I-Label, dazu O.'),
           dict(s=r'Eine Richtung: \(128^2+128\cdot100+128=16\,384+12\,800+128=29\,312\)', why=r'\(W\in\mathbb R^{d_h\times d_h}\), \(U\in\mathbb R^{d_h\times d}\), \(b\in\mathbb R^{d_h}\).'),
           dict(s=r'Zwei Richtungen: \(2\cdot29\,312=58\,624\)', why='Vorwärts- und Rückwärts-RNN haben eigene Parameter.'),
           dict(s=r'Ausgabe: \(9\cdot256+9=2\,313\)', why=r'\(W_o\) hat \(2d_h=256\) Spalten, weil es den verketteten Zustand liest.'),
           dict(s=r'Summe: \(58\,624+2\,313=60\,937\)', why=r'Probe: \(2(d_h^2+d_hd+d_h)+|\mathcal L|(2d_h+1)\).')],
    answers=[dict(label=r'Selbsterklärung: Warum hat \(W_o\) hier 256 und nicht 128 Spalten?', type='choice', options=[r'Weil \(W_o\) den verketteten Zustand \([h^{\rightarrow};h^{\leftarrow}]\in\mathbb R^{2d_h}\) liest', r'Weil BIO doppelt so viele Labels hat wie IO', r'Weil der Bias mitgezählt wird'], correct=0)],
    result_check='params:100:128:9',
    solution=r'\(|\mathcal L|=2\cdot4+1=9\). Je Richtung \(128^2+128\cdot100+128=29\,312\), beide Richtungen \(58\,624\). Ausgabe \(W_o\in\mathbb R^{9\times256}\) plus Bias: \(9\cdot256+9=2\,313\). Summe \(60\,937\). Selbsterklärung: \(W_o\) hat 256 Spalten, weil der Klassifikator \(h^{\mathrm{bi}}_t\in\mathbb R^{2d_h}\) liest.',
    rubric=['Labelzahl 2K+1', 'zwei Richtungen ohne geteilte Parameter', 'W_o mit 2d_h Spalten', 'Summe']))
T.append(dict(id='B1', stage='independent', kc='birnn', title='Parameter eines kleineren Taggers',
    prompt=r'BiRNN-Tagger mit drei Entitätstypen in BIO, Einbettung \(d=50\), Zustand \(d_h=64\) je Richtung. Wie viele Parameter ohne Einbettungsmatrix?',
    givens={'d': 50, 'dh': 64, 'K': 3},
    answers=[dict(label='Parameter', type='num', check='params:50:64:7', diagnoses=[dict(value='15175', msg=r'\(W_o\) liest \([h^{\rightarrow};h^{\leftarrow}]\) und hat \(2d_h\) Spalten, nicht \(d_h\).'), dict(value='8263', msg='Es gibt zwei RNNs mit getrennten Parametern; Sie haben eine Richtung gezählt.')])],
    hints=[r'Erst \(|\mathcal L|\) für drei Typen.', r'Je Richtung \(d_h^2+d_hd+d_h\); Ausgabe \(|\mathcal L|(2d_h+1)\).'],
    solution=r'\(|\mathcal L|=2\cdot3+1=7\). Je Richtung \(64^2+64\cdot50+64=4\,096+3\,200+64=7\,360\); beide \(14\,720\). Ausgabe \(7\cdot128+7=903\). Summe \(15\,623\).',
    rubric=['Labelzahl (1 P.)', 'zwei Richtungen (1 P.)', 'W_o mit 2d_h Spalten (1 P.)', 'Summe (1 P.)']))
T.append(dict(id='B2', stage='faded', kc='birnn', title='Rückwärts rechnen mit einem fehlenden Schritt',
    prompt=r'Rückwärts-RNN des Experiments, \(h^{\leftarrow}_t=\tanh(0{,}8\,h^{\leftarrow}_{t+1}+e_t)\), \(h^{\leftarrow}_3=0\), Satz „Washington state“. Bestimmen Sie die zweite Komponente von \(h^{\leftarrow}_1\).',
    steps=[dict(s=r'\(h^{\leftarrow}_2=\tanh(0{,}8\cdot0+(0,-1))=(0;\,-0{,}7616)\)', why='Die Rückwärtsrichtung beginnt beim letzten Wort, mit Startzustand 0.'),
           dict(s=r'\(0{,}8\,h^{\leftarrow}_2+e_1=(0;\,-0{,}6093)+(1;\,0)=(1;\,-0{,}6093)\)', why='Alten Zustand dämpfen, Einbettung von „Washington“ addieren.'),
           dict(s=r'\(h^{\leftarrow}_1=(\tanh 1;\ \ ?\ )\)', why='Ihr Schritt.', blank=True)],
    answers=[dict(label=r'zweite Komponente von \(h^{\leftarrow}_1\)', type='num', check='toy:bw:state:1:1', diagnoses=[dict(value='0.5436', msg=r'Vorzeichen prüfen: Das Argument ist \(-0{,}6093\).'), dict(value='-0.6093', msg=r'Das ist das Argument; es fehlt \(\tanh\).')])],
    hints=[r'\(\tanh(-0{,}6093)\); \(\tanh\) ist ungerade.'],
    solution=r'\(\tanh(-0{,}6093)\approx-0{,}5436\), also \(h^{\leftarrow}_1=(0{,}7616;\,-0{,}5436)\). Das Minuszeichen stammt von „state“ an Position 2 und erreicht Position 1 nur über die Rückwärtsrekursion.',
    rubric=['Rekursion von rechts', 'Wert ±0,0005', 'Herkunft des Vorzeichens']))
T.append(dict(id='AT1', stage='faded', kc='attention', title='Self-Attention von Hand',
    prompt=r'Drei Token mit \(x_1=(1,0)\), \(x_2=(0,1)\), \(x_3=(1,1)\); \(W_Q=W_K=W_V=I\), \(d_k=2\). Berechnen Sie das Gewicht \(\alpha_{33}\), mit dem Token 3 auf sich selbst achtet, und die erste Komponente von \(o_3\).',
    data={'X': [[1, 0], [0, 1], [1, 1]], 'i': 3},
    steps=[dict(s=r'\(q_3=(1,1)\); \(q_3^\top k_j=1,\ 1,\ 2\) für \(j=1,2,3\)', why=r'Mit \(W=I\) sind Anfrage, Schlüssel und Wert die Eingaben selbst.'),
           dict(s=r'\(e_{3j}=q_3^\top k_j/\sqrt2=0{,}7071;\ 0{,}7071;\ 1{,}4142\)', why=r'Skalierung mit \(\sqrt{d_k}=\sqrt2\).'),
           dict(s=r'\(\alpha_{33}=\dfrac{e^{1{,}4142}}{2e^{0{,}7071}+e^{1{,}4142}}=\ ?\)', why='Ihr Schritt: Softmax über die drei Energien.', blank=True)],
    answers=[dict(label=r'\(\alpha_{33}\)', type='num', check='attn:AT1:w:2', diagnoses=[dict(value='0.5761', msg=r'Sie haben ohne \(\sqrt{d_k}\) skaliert (Energien 1, 1, 2).'), dict(value='0.5', msg=r'Das ist \(2/(1+1+2)\) – die Softmax normiert \(e^{e_{ij}}\), nicht die Energien selbst.')]),
             dict(label=r'erste Komponente von \(o_3\)', type='num', check='attn:AT1:o:0')],
    hints=[r'\(e^{0{,}7071}\approx2{,}0281\), \(e^{1{,}4142}\approx4{,}1133\).', r'\(o_3=\alpha_{31}v_1+\alpha_{32}v_2+\alpha_{33}v_3\) mit \(v_j=x_j\).'],
    solution=r'\(\alpha_{3\cdot}=(2{,}0281;\,2{,}0281;\,4{,}1133)/8{,}1695=(0{,}2483;\,0{,}2483;\,0{,}5035)\). \(o_3=0{,}2483\,(1,0)+0{,}2483\,(0,1)+0{,}5035\,(1,1)=(0{,}7517;\,0{,}7517)\). Token 3 achtet am stärksten auf sich selbst, weil \(q_3\) mit \(k_3\) das größte Skalarprodukt hat.',
    rubric=['Energien mit Skalierung', 'Softmax korrekt normiert', 'gewichtete Summe']))
T.append(dict(id='PO1', stage='independent', kc='position', title='Reihenfolge und relative Position',
    prompt=r'(a) Ein Self-Attention-Modell ohne Positionskodierung verarbeitet „Marry kills John“ und „John kills Marry“. Was gilt für den Ausgabevektor von „John“? (b) RoPE mit \(\theta=0{,}5\), \(q=k=(1,0)\): Berechnen Sie die Ähnlichkeit \(\big(R(m\theta)q\big)^\top R(n\theta)k\) für \(m=2\), \(n=5\).',
    givens={'theta': 0.5, 'm': 2, 'n': 5},
    answers=[dict(label='(a)', type='choice', options=['In beiden Sätzen identisch', 'Verschieden, weil „John“ an anderer Stelle steht', 'Nur der Vektor von „kills“ ist identisch'], correct=0,
                  diagnoses=[dict(value='1', msg=r'Ohne Positionskodierung ist Self-Attention permutations-äquivariant (Satz 4): Die Stelle eines Tokens geht nicht ein.'), dict(value='2', msg='Satz 4 gilt für jedes Token, nicht nur für das mittlere.')]),
             dict(label='(b) Ähnlichkeit', type='num', check='rope:0.5:2:5', diagnoses=[dict(value='-0.8011', msg=r'Das ist \(\cos(5\cdot0{,}5)\): Es zählt der Abstand \(n-m\), nicht die absolute Position \(n\).')])],
    hints=[r'Satz 4.', r'\(q^\top R((n-m)\theta)k=\cos((n-m)\theta)\) für \(q=k=(1,0)\).'],
    solution=r'(a) Identisch: \(\operatorname{Att}(PX)=P\operatorname{Att}(X)\), der Vektor wandert nur mit dem Token. (b) \(q^\top R((5-2)\cdot0{,}5)k=\cos(1{,}5)\approx0{,}0707\). Gleicher Wert für \(m=4,n=7\): nur der Abstand zählt.',
    rubric=['Satz 4 angewandt', 'Drehungen zusammengefasst', 'Wert']))
T.append(dict(id='C1', stage='independent', kc='decoding', title='Gierig gegen Viterbi',
    prompt=r'Emissionswerte \(s_t(\ell)\) für „in New York“ mit Labels O, B-LOC, I-LOC: in (2; 0; 0,5), New (0,3; 1,0; 1,2), York (0; 0,2; 1,5). Übergänge: verboten sind Start→I-LOC und O→I-LOC, alle anderen 0. (a) Welche Folge wählt die gierige Dekodierung? (b) Welchen Score hat die beste gültige Folge?',
    data={'labels': L3, 'emissions': [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]]},
    answers=[dict(label='(a) gierig', type='choice', options=['O I-LOC I-LOC', 'O B-LOC I-LOC', 'O B-LOC B-LOC'], correct=0),
             dict(label='(b) bester Score', type='num', check='viterbi:C1', diagnoses=[dict(value='4.7', msg='Das ist der Score der gierigen, aber ungültigen Folge.')])],
    hints=['(a) Je Wort das Maximum.', '(b) Prüfen Sie O B-LOC I-LOC gegen O B-LOC B-LOC.'],
    solution=r'(a) Je Wort das Maximum: O (2), I-LOC (1,2), I-LOC (1,5) – Score 4,7, aber O→I-LOC ist verboten. (b) Gültige Kandidaten: O B-LOC I-LOC mit \(2+1{,}0+1{,}5=4{,}5\); O B-LOC B-LOC mit 3,2; O O I-LOC verboten; O O O mit 2,3. Viterbi wählt O B-LOC I-LOC, Score 4,5.',
    rubric=['gierige Folge', 'Übergangsregel angewandt', 'bester Score']))
T.append(dict(id='B3', stage='hint', kc='prf-edge', title='Ein System, das nichts ausgibt',
    prompt=r'Ein Satz enthält 3 Gold-Entitäten; das System gibt keine aus. Bestimmen Sie \(F_1\) mit der Zählform und entscheiden Sie, ob \(P\) definiert ist.',
    answers=[dict(label=r'\(F_1\)', type='num', check='f1:0:0:3'),
             dict(label=r'Ist \(P\) definiert?', type='choice', options=[r'ja, \(P=0\)', r'ja, \(P=1\)', r'nein, \(P=0/0\)'], correct=2,
                  diagnoses=[dict(value='0', msg=r'Es gibt keine Ausgabe, über die man einen Anteil bilden könnte: \(\mathrm{TP}+\mathrm{FP}=0\). 0 wäre eine Konvention.')])],
    hints=['TP, FP, FN aufschreiben.', 'Fall (iii) der Tabelle.'],
    solution=r'TP = FP = 0, FN = 3. \(P=0/0\) nicht definiert, \(R=0/3=0\), Zählform \(F_1=0/(0+0+3)=0\). \(2PR/(P+R)\) ist hier nicht anwendbar.',
    rubric=['Zählungen', 'P undefiniert begründet', 'F1 = 0 über Zählform']))
T.append(dict(id='B4', stage='independent', kc='prf-level', title='Phrasen- und Token-Ebene',
    prompt=r'Gold: <code>[Angela Merkel]PER besuchte gestern die [Siemens AG]ORG in [München]LOC .</code><br>System: <code>[Angela Merkel]PER besuchte gestern die [Siemens]ORG AG in [München]ORG .</code><br>Berechnen Sie \(F_1\) auf Phrasen- und auf Token-Ebene.',
    data={'tokens': ['Angela', 'Merkel', 'besuchte', 'gestern', 'die', 'Siemens', 'AG', 'in', 'München', '.'], 'gold': ['B-PER', 'I-PER', 'O', 'O', 'O', 'B-ORG', 'I-ORG', 'O', 'B-LOC', 'O'], 'pred': ['B-PER', 'I-PER', 'O', 'O', 'O', 'B-ORG', 'O', 'O', 'B-ORG', 'O']},
    answers=[dict(label=r'\(F_1\) Phrasen', type='num', check='span_f1:B4', diagnoses=[dict(value='2/5', msg='Der Typfehler bei München zählt auf Phrasen-Ebene als FP <em>und</em> FN.'), dict(value='1/2', msg='Auch der Grenzfehler bei „Siemens AG“ zählt doppelt: FP für [Siemens], FN für [Siemens AG].')]),
             dict(label=r'\(F_1\) Token', type='num', check='token_f1:B4', diagnoses=[dict(value='3/4', msg='Das ist die Precision. Recall: 3 von 5 Gold-Token.')])],
    hints=['Spannen als (Anfang, Ende, Typ) auflisten.', 'Token: 5 Gold-Entitätstoken, 4 System-Entitätstoken.'],
    solution=r'Phrasen: Gold {[Angela Merkel]PER, [Siemens AG]ORG, [München]LOC}, System {[Angela Merkel]PER, [Siemens]ORG, [München]ORG}: TP = 1, FP = 2, FN = 2, \(F_1=2/6=1/3\). Token: TP = 3 (Angela, Merkel, Siemens), FP = 1 (München als ORG), FN = 2 (AG; München als LOC): \(F_1=6/9=2/3\).',
    rubric=['Spannenmengen (1 P.)', 'Doppelzählung (2 P.)', 'Token-Zählung (1 P.)', 'beide Werte (1 P.)']))
T.append(dict(id='B5', stage='error', kc='prf-level', title='Fehleranalyse: eine Zähltabelle',
    prompt=r'Eine Kommilitonin wertet B4 auf Phrasen-Ebene so aus:<br>TP: <code>[Angela Merkel]PER</code> · FP: <code>[Siemens]ORG</code> · FN: <code>[Siemens AG]ORG</code>, <code>[München]LOC</code><br>und erhält \(P=\tfrac12\), \(R=\tfrac13\). Welche Aussage beschreibt ihren Fehler genau?',
    answers=[dict(label='Fehler', type='choice', options=['Die System-Spanne [München]ORG fehlt in ihrer FP-Liste.', 'Die Gold-Spanne [Siemens AG]ORG fehlt in ihrer FN-Liste.', 'Sie hat [Siemens]ORG als FP gezählt, obwohl es ein Teiltreffer ist.', 'Sie hat True Negatives mitgezählt.'], correct=0,
                  diagnoses=[dict(value='1', msg='[Siemens AG]ORG steht in ihrer FN-Liste.'), dict(value='2', msg='Auf Phrasen-Ebene gibt es keine Teiltreffer; [Siemens]ORG ist korrekt ein FP.'), dict(value='3', msg='TN kommen in P und R nicht vor.')])],
    hints=['Gehen Sie die drei System-Spannen durch: In welcher Liste steht jede?'],
    solution=r'Jede System-Spanne muss genau einmal als TP oder FP erscheinen. Das System gibt drei Spannen aus; in ihren Listen stehen zwei ([Angela Merkel] als TP, [Siemens] als FP). [München]ORG fehlt als FP. Richtig: FP = 2, \(P=\tfrac13\). Die FN-Liste ist korrekt.',
    rubric=['Prüfprinzip: jede System-Spanne genau einmal', 'fehlende FP-Zählung benannt', 'korrigiertes P']))
T.append(dict(id='B6', stage='transfer', kc='micro-macro', title='Eine seltene Klasse fällt aus',
    prompt=r'PER: TP 80, FP 10, FN 20; LOC: TP 50, FP 25, FN 5; MISC: TP 0, FP 3, FN 7. (a) Micro-\(F_1\), (b) Macro-\(F_1\), (c) das exakte Gewicht \(w_{\mathrm{MISC}}\) von MISC in Micro-\(F_1\) als gewichtetem Mittel der Typ-\(F_1\)-Werte.',
    data={'counts': '80,10,20;50,25,5;0,3,7', 'k': 2},
    answers=[dict(label=r'(a) Micro-\(F_1\)', type='num', check='micro:80,10,20;50,25,5;0,3,7'),
             dict(label=r'(b) Macro-\(F_1\)', type='num', check='macro:80,10,20;50,25,5;0,3,7', diagnoses=[dict(value='0.8057', msg=r'Das ist das Mittel über PER und LOC. MISC hat \(F_1=0\) und zählt mit.')]),
             dict(label=r'(c) \(w_{\mathrm{MISC}}\)', type='num', check='microweight:80,10,20;50,25,5;0,3,7:2', diagnoses=[dict(value='7/162', msg=r'Das ist der Gold-Anteil (Support) von MISC. Micro gewichtet mit \(D_k=2\mathrm{TP}_k+\mathrm{FP}_k+\mathrm{FN}_k\).')])],
    hints=['Micro: Zählungen addieren, dann Zählform.', r'\(D_k=2\mathrm{TP}_k+\mathrm{FP}_k+\mathrm{FN}_k\); \(w_k=D_k/\sum_l D_l\).'],
    solution=r'\(D=(190,\ 130,\ 10)\), \(\sum D=330\). Typ-\(F_1\): PER \(160/190\approx0{,}8421\), LOC \(100/130\approx0{,}7692\), MISC \(0/10=0\). (a) Micro \(=(160+100+0)/330=26/33\approx0{,}7879\). (b) Macro \(\approx0{,}5371\). (c) \(w_{\mathrm{MISC}}=10/330=1/33\approx0{,}0303\) – nicht der Gold-Anteil \(7/162\approx0{,}0432\). Macro zeigt den Ausfall, weil MISC dort ein Drittel Gewicht hat.',
    rubric=['Micro (1 P.)', 'Macro (1 P.)', 'Gewicht über D_k statt Support (2 P.)']))
T.append(dict(id='F1', stage='transfer', kc='decoding', title='Fallstudie: was Viterbi repariert',
    prompt=r'Nutzen Sie die Fallstudie in Abschnitt 13 (gierige gegen Viterbi-Dekodierung). (a) Phrasen-\(F_1\) nach Viterbi. (b) Wie viele Grenzfehler bleiben nach Viterbi? (c) Warum repariert Viterbi den Fehler bei „Berlin .“ nicht?',
    answers=[dict(label=r'(a) Phrasen-\(F_1\) (Viterbi)', type='num', check='case:viterbi:span_f1', diagnoses=[dict(value='8/17', msg='Das ist der Wert der gierigen Dekodierung.')]),
             dict(label='(b) Grenzfehler', type='num', check='case:viterbi:boundary'),
             dict(label='(c)', type='choice', options=['<code>B-LOC I-LOC</code> ist eine gültige Folge; die Übergangsregel verbietet sie nicht', 'Viterbi berücksichtigt das letzte Wort eines Satzes nicht', 'Der Satzpunkt ist kein Token'], correct=0)],
    hints=['Lesen Sie die Tabelle der Fallstudie für „Viterbi“.'],
    solution=r'(a) Nach Viterbi: TP = 5, FP = 3, FN = 3, \(F_1=10/16=5/8\) (gierig: TP = 4, FP = 5, FN = 4, \(8/17\)). (b) 2 Grenzfehler: [Barack]PER statt [Barack Obama]PER und [Berlin .]LOC statt [Berlin]LOC. (c) Harte Übergangsregeln schließen nur ungültige Folgen aus; <code>B-LOC I-LOC</code> ist gültig. Nur bessere Emissionen (oder gelernte Übergangswerte, die „. “ als Fortsetzung bestrafen) ändern das.',
    rubric=['F1 nach Viterbi', 'Grenzfehler gezählt', 'Begründung gültig/ungültig']))
T.append(dict(id='B7', stage='transfer', kc='prf', title='Beweisaufgabe',
    prompt=r'Zeigen Sie für \(P,R\in(0,1]\): \(F_1\le 2\min(P,R)\). Was folgt für ein System, das jedes Wort als Entität markiert?',
    answers=[dict(label='Selbstbewertung nach Lösung', type='self')],
    hints=[r'O. B. d. A. \(P\le R\); mit \(P+R&gt;0\) multiplizieren.'],
    solution=r'Sei \(P\le R\) (Symmetrie). \(\tfrac{2PR}{P+R}\le 2P\iff 2PR\le 2P(P+R)\iff 0\le 2P^2\) – wahr. Markiert ein System alles, ist \(R\) nahe 1, \(P\) gleich dem Anteil der Entitätstoken; \(F_1\) bleibt unter dem Doppelten davon.',
    rubric=['WLOG begründet', 'Äquivalenzumformung mit positivem Faktor', 'Interpretation']))

# ---- v4 workbook expansion (Issue #7 P0.3) ----
T += [
 dict(id='S0', stage='recall', kc='spans', title='Selbsterklärung: wozu L- und U-?',
      prompt=r'BIO kann jede Spannenmenge eindeutig darstellen (Satz A). Welche zusätzliche Information liefert BILOU dem Klassifikator?',
      answers=[dict(label='Antwort', type='choice', options=['Das Spannenende und Einwort-Spannen sind direkt als eigenes Label markiert', 'BILOU kann Spannen darstellen, die BIO nicht darstellen kann', 'BILOU braucht weniger Labels als BIO'], correct=0,
                    diagnoses=[dict(value='1', msg='Beide Schemata sind auf gültigen Folgen eindeutig; BILOU drückt keine zusätzlichen Spannenmengen aus.'), dict(value='2', msg=r'BILOU hat \(4K+1\), BIO \(2K+1\) Labels.')])],
      hints=['Vergleichen Sie, was der Klassifikator an der letzten Position einer Spanne vorhersagen muss.'],
      solution=r'BILOU markiert das letzte Wort einer Mehrwortspanne (L-) und Einwortspannen (U-) explizit. Darstellbar sind dieselben Spannenmengen wie mit BIO; der Unterschied liegt im Lernsignal: Der Klassifikator muss Spannenenden direkt vorhersagen, statt sie implizit aus dem folgenden Label zu erschließen.',
      rubric=['richtige Option (1 P.)', 'Begründung: gleiche Ausdruckskraft, anderes Lernsignal (1 P.)']),
 dict(id='S2', stage='independent', kc='spans', title='Kodieren: BIO',
      prompt=r'Satz: <code>Tickets nach New York und Boston</code> mit den Gold-Spannen [New York]CITY und [Boston]CITY. Geben Sie die BIO-Folge an (Labels durch Leerzeichen getrennt).',
      answers=[dict(label='BIO-Folge', type='seq', check='bio:6:2-4-CITY,5-6-CITY:BIO')],
      hints=['Jede Spanne beginnt mit B-, setzt sich mit I- fort.'],
      solution=r'<code>O O B-CITY I-CITY O B-CITY</code>. „Boston“ bekommt B-CITY, weil es eine neue Spanne beginnt; I-CITY wäre gültig nur direkt nach einem CITY-Label.',
      rubric=['Spannenanfänge mit B- (1 P.)', 'Fortsetzung mit I- (1 P.)', 'Rest O (1 P.)']),
 dict(id='S3', stage='independent', kc='spans', title='Kodieren: BILOU',
      prompt=r'Gleicher Satz wie S2. Geben Sie die BILOU-Folge an.',
      answers=[dict(label='BILOU-Folge', type='seq', check='bio:6:2-4-CITY,5-6-CITY:BILOU')],
      hints=['Zweiwortspanne: B- dann L-. Einwortspanne: U-.'],
      solution=r'<code>O O B-CITY L-CITY O U-CITY</code>. „New York“ ist eine Zweiwortspanne (B-, L-), „Boston“ eine Einwortspanne (U-).',
      rubric=['B/L für Mehrwortspanne (1 P.)', 'U für Einwortspanne (1 P.)']),
 dict(id='S4', stage='error', kc='spans', title='Code lesen: ein abweichender Decoder',
      prompt=r'Ein Team dekodiert BIO so:<pre><code>def spans(tags):\n    out, start = [], None\n    for i, t in enumerate(tags + ["O"]):\n        if start is not None and not t.startswith("I-"):\n            out.append((start, i)); start = None\n        if t.startswith("B-"):\n            start = i\n    return out</code></pre>Was liefert der Code für <code>O I-LOC I-LOC</code>, und wie unterscheidet sich das von <code>conlleval</code>?',
      answers=[dict(label='Antwort', type='choice', options=['[] – der Code verwirft Spannen ohne B-, conlleval liest [w₂ w₃]LOC', '[(1, 3)] – wie conlleval', 'einen Fehler (Exception)'], correct=0,
                    diagnoses=[dict(value='1', msg='start wird nur bei B- gesetzt; ein I- ohne vorheriges B- öffnet hier keine Spanne.'), dict(value='2', msg='Der Code läuft fehlerfrei durch; er ignoriert die I-Labels nur.')])],
      hints=['Verfolgen Sie die Variable start über die drei Labels.'],
      solution=r'<code>start</code> wird nur bei <code>B-</code> gesetzt. Bei <code>O I-LOC I-LOC</code> bleibt <code>start=None</code>, die Ausgabe ist <code>[]</code>. <code>conlleval</code> liest dagegen ein <code>I-LOC</code> ohne Vorgänger als neue Spanne: [w₂ w₃]LOC. Dieselben Vorhersagen ergeben mit beiden Decodern verschiedene Recall-Werte – eine typische, schwer zu entdeckende Quelle nicht vergleichbarer Ergebnisse. Der Typ wird von diesem Code übrigens gar nicht ausgegeben.',
      rubric=['Ausgabe [] (1 P.)', 'Unterschied zu conlleval (1 P.)', 'Folge für Vergleichbarkeit (1 P.)']),
 dict(id='W1F', stage='faded', kc='birnn', title='Parameterzahl mit ausgeblendetem Schritt',
      prompt=r'BiRNN-Tagger mit zwei Entitätstypen in BIO, \(d=200\), \(d_h=100\) je Richtung. Ergänzen Sie den fehlenden Schritt und die Summe.',
      givens={'d': 200, 'dh': 100, 'K': 2},
      steps=[dict(s=r'\(|\mathcal L|=2\cdot2+1=5\)', why='BIO mit zwei Typen.'),
             dict(s=r'Eine Richtung: \(100^2+100\cdot200+100=30\,100\); beide: \(60\,200\)', why=r'\(W,U,b\) je Richtung, keine geteilten Parameter.'),
             dict(s=r'Ausgabe: \(\ ?\ \)', why=r'Ihr Schritt: \(W_o\) liest \(h^{\mathrm{bi}}\).', blank=True)],
      answers=[dict(label='Parameter gesamt', type='num', check='params:200:100:5', diagnoses=[dict(value='60705', msg=r'\(W_o\) hat \(2d_h=200\) Spalten: Ausgabe \(5\cdot200+5\).')])],
      hints=[r'\(|\mathcal L|(2d_h+1)\).'],
      solution=r'Ausgabe \(5\cdot(2\cdot100+1)=1\,005\). Summe \(60\,200+1\,005=61\,205\).',
      rubric=['Ausgabeschicht mit 2d_h Spalten (1 P.)', 'Summe (1 P.)']),
 dict(id='R1', stage='proof', kc='birnn', title='Beweis: Abhängigkeitsbereich des Rückwärts-RNN',
      prompt=r'Beweisen Sie ohne Rückgriff auf Satz 1 per Induktion über \(s=T,T-1,\dots,1\): \(h^{\leftarrow}_s\) ist eine Funktion von \(x_s,\dots,x_T\).',
      answers=[dict(label='Selbstbewertung nach Lösung', type='self')],
      hints=[r'Anfang bei \(s=T\) mit \(h^{\leftarrow}_{T+1}=0\).'],
      solution=r'Anfang \(s=T\): \(h^{\leftarrow}_T=\tanh(W\prime\cdot0+U\prime e_T+b\prime)\) hängt nur von \(x_T\) ab. Schritt \(s+1\to s\): Nach Annahme ist \(h^{\leftarrow}_{s+1}=G_{s+1}(x_{s+1},\dots,x_T)\). Einsetzen: \(h^{\leftarrow}_s=\tanh\big(W\prime G_{s+1}(x_{s+1},\dots,x_T)+U\prime e_s+b\prime\big)=:G_s(x_s,\dots,x_T)\); kein \(x_r\) mit \(r&lt;s\) kommt vor. \(\square\)',
      rubric=['Induktionsanfang mit Startzustand (1 P.)', 'Induktionsschritt sauber eingesetzt (2 P.)', 'Schlussfolgerung über fehlende linke Wörter (1 P.)']),
 dict(id='T1', stage='transfer', kc='birnn', title='Transfer: Live-Tagging mit Vorausschau',
      prompt=r'Ein Diktiersystem darf das Label von Wort \(t\) erst ausgeben, wenn zwei weitere Wörter gesprochen sind (Vorausschau \(k=2\)). Es nutzt ein Vorwärts-RNN, das zum Zeitpunkt der Ausgabe \(h^{\rightarrow}_{t+2}\) liest. Von welchen Eingaben kann das Label für \(t=4\) in einem Satz mit \(T=10\) Wörtern abhängen?',
      answers=[dict(label='Indizes', type='set', check='deplook:10:4:2', diagnoses=[])],
      hints=[r'Satz 1 auf Position \(t+k\) anwenden.'],
      solution=r'Das System liest \(h^{\rightarrow}_{6}\); nach Satz 1 hängt es von \(x_1,\dots,x_6\) ab, also Indizes 1, 2, 3, 4, 5, 6. Gegenüber einem reinen Vorwärts-Tagger gewinnt es zwei Wörter rechten Kontext, um den Preis von zwei Wörtern Latenz – der Kompromiss aus Abschnitt 5(a).',
      rubric=['Satz 1 auf t+k angewandt (1 P.)', 'Menge korrekt (1 P.)', 'Latenz-Kontext-Abwägung benannt (1 P.)']),
 dict(id='AT0', stage='worked', kc='attention', title='Durchgerechnet: Attention mit zwei Schlüsseln',
      prompt=r'Anfrage \(q=(1,0)\), Schlüssel \(k_1=(1,0)\), \(k_2=(0,1)\), Werte \(v_1=(2,0)\), \(v_2=(0,4)\), \(d_k=2\). Berechnen Sie die Ausgabe.',
      steps=[dict(s=r'Energien: \(q^\top k_1/\sqrt2=1/\sqrt2\approx0{,}7071\), \(q^\top k_2/\sqrt2=0\)', why=r'Skalarprodukt, durch \(\sqrt{d_k}\) geteilt.'),
             dict(s=r'Softmax: \(e^{0{,}7071}\approx2{,}0281\), \(e^0=1\); \(\alpha_1=2{,}0281/3{,}0281\approx0{,}6698\), \(\alpha_2\approx0{,}3302\)', why='Exponentieren und auf Summe 1 normieren.'),
             dict(s=r'Ausgabe: \(o=0{,}6698\,(2,0)+0{,}3302\,(0,4)=(1{,}3395;\ 1{,}3210)\)', why='Gewichtete Summe der Werte.')],
      answers=[dict(label=r'Selbsterklärung: Warum ist \(\alpha_1&gt;\alpha_2\), obwohl \(v_2\) die größere Norm hat?', type='choice', options=['Die Gewichte hängen von Anfrage und Schlüsseln ab, nicht von den Werten', r'Weil \(v_1\) zuerst kommt', r'Weil durch \(\sqrt{d_k}\) geteilt wird'], correct=0)],
      solution=r'Energien \(0{,}7071\) und \(0\); Gewichte \(0{,}6698\) und \(0{,}3302\); Ausgabe \((1{,}3395;\ 1{,}3210)\). Die Werte bestimmen, <em>was</em> gemischt wird, die Schlüssel, <em>wie stark</em>: \(q\) ist parallel zu \(k_1\), daher \(\alpha_1&gt;\alpha_2\), unabhängig von der Norm der Werte.',
      rubric=['Energien', 'Softmax', 'gewichtete Summe', 'Rolle von Schlüssel vs. Wert']),
 dict(id='AT2', stage='independent', kc='attention', title='Attention selbstständig',
      prompt=r'Anfrage \(q=(2,1)\), Schlüssel und Werte \(k_1=v_1=(1,0)\), \(k_2=v_2=(0,2)\), \(d_k=2\). Bestimmen Sie \(\alpha_1\) und die erste Komponente der Ausgabe \(o\).',
      answers=[dict(label=r'\(\alpha_1\)', type='num', check='attnq:2,1|1,0;0,2:0', diagnoses=[dict(value='0.7311', msg=r'Sie haben \(q^\top k_2\) mit \(k_2=(0,1)\) gerechnet. Der Schlüssel ist \((0,2)\): \(q^\top k_2=2\).')]),
               dict(label=r'\(o\), erste Komponente', type='num', check='attno:2,1|1,0;0,2:0')],
      hints=[r'\(q^\top k_1=2\), \(q^\top k_2=2\).'],
      solution=r'\(q^\top k_1=2\cdot1+1\cdot0=2\), \(q^\top k_2=2\cdot0+1\cdot2=2\); nach Skalierung beide \(1{,}4142\). Gleiche Energien ergeben gleiche Gewichte: \(\alpha_1=\alpha_2=0{,}5\). \(o=0{,}5\,(1,0)+0{,}5\,(0,2)=(0{,}5;\ 1)\), erste Komponente \(0{,}5\). Gleich lange Projektionen bedeuten gleiche Aufmerksamkeit – auch wenn \(q\) nicht genau in eine der beiden Richtungen zeigt.',
      rubric=['Skalarprodukte', 'Gewichte', 'Ausgabe', 'Deutung']),
 dict(id='AT3', stage='proof', kc='attention', title='Beweis: Varianz des Skalarprodukts',
      prompt=r'Zeigen Sie: Sind \(q_1,\dots,q_d,k_1,\dots,k_d\) unabhängig mit Erwartungswert 0 und Varianz 1, so hat \(q^\top k\) die Varianz \(d\). Welche Annahme benutzen Sie an welcher Stelle?',
      answers=[dict(label='Selbstbewertung nach Lösung', type='self')],
      hints=[r'\(\operatorname{Var}(XY)\) für unabhängige \(X,Y\) mit \(\mathbb E X=\mathbb E Y=0\).'],
      solution=r'Für jedes \(i\): \(\mathbb E[q_ik_i]=\mathbb E[q_i]\mathbb E[k_i]=0\) (Unabhängigkeit). \(\operatorname{Var}(q_ik_i)=\mathbb E[q_i^2k_i^2]-0=\mathbb E[q_i^2]\mathbb E[k_i^2]=1\) (Unabhängigkeit, \(\mathbb E[q_i^2]=\operatorname{Var}q_i=1\) wegen Mittelwert 0). Die Summanden sind paarweise unkorreliert (verschiedene unabhängige Variablen), also addieren sich die Varianzen: \(\operatorname{Var}(q^\top k)=d\). \(\square\)',
      rubric=['Erwartungswert 0 (1 P.)', 'Varianz je Summand mit benannter Annahme (2 P.)', 'Additivität mit Begründung (1 P.)']),
 dict(id='AT4', stage='transfer', kc='attention', title='Transfer: Parameter mit Ausgabematrix',
      prompt=r'Ein Transformer-Attention-Block mit \(n=d=128\) und \(h=4\) Köpfen hat Projektionen \(W_Q,W_K,W_V\) (je Kopf \(128\times32\)) und eine Ausgabematrix \(W_O\in\mathbb R^{128\times128}\). Wie viele Gewichte (ohne Bias) hat er?',
      answers=[dict(label='Gewichte', type='num', check='int:65536', diagnoses=[dict(value='49152', msg=r'Sie haben \(W_O\) vergessen: \(3\cdot128^2+128^2\).')])],
      hints=[r'Je Projektionsart \(4\cdot128\cdot32=128^2\).'],
      solution=r'Je Projektionsart \(4\cdot128\cdot32=16\,384=128^2\), drei Arten: \(49\,152\). Dazu \(W_O\): \(16\,384\). Summe \(65\,536\). Die Aufteilung in Köpfe ändert die Zahl nicht; erst \(W_O\) kommt hinzu (Abschnitt 6).',
      rubric=['Köpfe ändern Anzahl nicht (1 P.)', 'W_O gezählt (1 P.)', 'Summe (1 P.)']),
 dict(id='PO2', stage='independent', kc='position', title='Sinus-Kodierung ausrechnen',
      prompt=r'Mit \(d_{\text{model}}=4\): Berechnen Sie \(\mathrm{POS}(5,0)\) und \(\mathrm{POS}(5,1)\) (Bogenmaß, vier Nachkommastellen).',
      answers=[dict(label=r'\(\mathrm{POS}(5,0)\)', type='num', check='sinpos:5:0:4'), dict(label=r'\(\mathrm{POS}(5,1)\)', type='num', check='sinpos:5:1:4')],
      hints=[r'\(d=0\): \(\sin(5/10000^0)\); \(d=1\): \(\cos(5/10000^{0})\).'],
      solution=r'\(\mathrm{POS}(5,0)=\sin(5)\approx-0{,}9589\), \(\mathrm{POS}(5,1)=\cos(5)\approx0{,}2837\). Beide Komponenten gehören zur schnellsten Frequenz \(\omega=1\); das Paar liegt auf dem Einheitskreis: \(0{,}9589^2+0{,}2837^2\approx1\).',
      rubric=['Exponent 0 bei d=0 und d=1 (1 P.)', 'Werte (1 P.)', 'Einheitskreis-Deutung (1 P.)']),
 dict(id='PO3', stage='proof', kc='position', title='Beweis: RoPE hängt nur vom Abstand ab',
      prompt=r'Zeigen Sie für 2D-Vektoren \(q,k\) und Drehmatrizen \(R(\varphi)\): \(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R((n-m)\theta)k\). Welche zwei Eigenschaften von Drehungen benutzen Sie?',
      answers=[dict(label='Selbstbewertung nach Lösung', type='self')],
      hints=[r'\((AB)^\top=B^\top A^\top\).'],
      solution=r'\(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R(m\theta)^\top R(n\theta)k\). Drehmatrizen sind orthogonal mit \(R(\varphi)^\top=R(-\varphi)\), und Drehungen addieren sich: \(R(a)R(b)=R(a+b)\). Also \(q^\top R(-m\theta)R(n\theta)k=q^\top R((n-m)\theta)k\). \(\square\) Folge: Verschiebt man beide Positionen um denselben Betrag, bleibt die Ähnlichkeit gleich.',
      rubric=['Transposition (1 P.)', 'Orthogonalität (1 P.)', 'Gruppeneigenschaft (1 P.)', 'Folgerung (1 P.)']),
 dict(id='PO4', stage='transfer', kc='position', title='Transfer: längere Eingaben als im Training',
      prompt=r'Ein Tagger mit <em>gelernten</em> absoluten Positionsvektoren für Positionen 1–512 soll Dokumente mit 600 Wörtern markieren. Was ist das unmittelbare Problem?',
      answers=[dict(label='Antwort', type='choice', options=['Für Positionen 513–600 existiert kein gelernter Vektor', 'Die Softmax wird instabil', 'Self-Attention wird zu einem RNN'], correct=0)],
      hints=['Folie PDF-S. 67: Nachteile gelernter Positionsvektoren.'],
      solution=r'Gelernte Positionsvektoren sind eine Tabelle mit fester Länge: Für Positionen über 512 gibt es keinen Eintrag (Vorlesung: „limited length“). Sinus-Kodierungen sind für jede Position definiert, RoPE kodiert relative Abstände; ob ein Modell auf längere Folgen tatsächlich verallgemeinert, ist damit noch nicht garantiert.',
      rubric=['fehlender Tabelleneintrag (1 P.)', 'Alternative benannt mit Einschränkung (1 P.)']),
 dict(id='C0', stage='worked', kc='decoding', title='Durchgerechnet: Viterbi-Tabelle',
      prompt=r'Emissionen wie in Abb. 9.1 („in New York“, Labels O, B-LOC, I-LOC; erlaubte Übergänge 0, verbotene \(-\infty\)). Füllen Sie die Viterbi-Tabelle \(\delta_t(\ell)\) und lesen Sie den besten Pfad ab.',
      steps=[dict(s=r'\(t=1\): \(\delta_1=(2;\ 0;\ -\infty)\)', why='Start→I-LOC verboten.'),
             dict(s=r'\(t=2\): \(\delta_2(\text{O})=2+0{,}3=2{,}3\); \(\delta_2(\text{B})=2+1{,}0=3{,}0\); \(\delta_2(\text{I})=\delta_1(\text{B})+1{,}2=1{,}2\)', why='I-LOC nur aus B-LOC (aus O verboten); O und B-LOC aus dem besten Vorgänger O.'),
             dict(s=r'\(t=3\): \(\delta_3(\text{O})=3{,}0+0=3{,}0\); \(\delta_3(\text{B})=3{,}0+0{,}2=3{,}2\); \(\delta_3(\text{I})=\max(3{,}0;1{,}2)+1{,}5=4{,}5\)', why='Bester Vorgänger ist jeweils B-LOC.'),
             dict(s=r'Rückverfolgung: I-LOC ← B-LOC ← O', why='Rückzeiger vom Maximum 4,5.')],
      answers=[dict(label=r'Selbsterklärung: Warum ist \(\delta_2(\text{I-LOC})=1{,}2\) und nicht \(2+1{,}2=3{,}2\)?', type='choice', options=['O → I-LOC ist verboten; nur B-LOC → I-LOC ist erlaubt', 'Weil 1,2 die Emission ist', 'Weil Viterbi nur den letzten Schritt betrachtet'], correct=0)],
      solution=r'\(\delta_1=(2;0;-\infty)\), \(\delta_2=(2{,}3;\ 3{,}0;\ 1{,}2)\), \(\delta_3=(3{,}0;\ 3{,}2;\ 4{,}5)\). Bester Pfad O B-LOC I-LOC mit Score 4,5. \(\delta_2(\text{I-LOC})\) kann nur aus B-LOC kommen: \(0+1{,}2=1{,}2\).',
      rubric=['Startbedingung', 'Übergangsregel in Zeile 2', 'Maximum je Zelle', 'Rückverfolgung']),
 dict(id='C2', stage='independent', kc='decoding', title='Score und Wahrscheinlichkeit',
      prompt=r'Gleiche Emissionen wie C1/Abb. 9.1. Berechnen Sie die Zustandssumme \(Z\) über alle gültigen Folgen und die Wahrscheinlichkeit \(p(y^\ast\mid x)\) des besten Pfades (vier Nachkommastellen).',
      data={'labels': L3, 'emissions': [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]]},
      answers=[dict(label=r'\(Z\)', type='num', check='crfz:C2', tol=0.01), dict(label=r'\(p(y^\ast\mid x)\)', type='num', check='crfprob:C2', diagnoses=[dict(value='1', msg='Der Score ist nicht normiert; die Wahrscheinlichkeit vergleicht mit allen gültigen Pfaden.')])],
      hints=[r'Forward-Algorithmus: \(\alpha_1=(e^2;\ e^0;\ 0)\).', r'\(\alpha_3=(37{,}448;\ 45{,}7391;\ 117{,}0794)\).'],
      solution=r'Forward: \(\alpha_1=(7{,}3891;\ 1;\ 0)\), \(\alpha_2=(11{,}324;\ 22{,}8038;\ 3{,}3201)\), \(\alpha_3=(37{,}448;\ 45{,}7391;\ 117{,}0794)\); \(Z=\sum\alpha_3\approx200{,}2664\) (13 gültige Pfade). \(p=e^{4{,}5}/200{,}2664\approx0{,}4495\). Der beste Pfad ist also der wahrscheinlichste, aber das Modell ist sich alles andere als sicher.',
      rubric=['Forward-Rekursion (2 P.)', 'Z (1 P.)', 'p (1 P.)', 'Deutung Score vs. Wahrscheinlichkeit (1 P.)']),
 dict(id='C3', stage='error', kc='decoding', title='Fehleranalyse: „Der Score ist die Log-Wahrscheinlichkeit“',
      prompt=r'Jemand schreibt: „Das CRF normiert global, also ist \(S(x,y^\ast)=4{,}5\) direkt \(\log p(y^\ast\mid x)\).“ Berechnen Sie das korrekte \(\log p(y^\ast\mid x)\) für C1/C2.',
      data={'labels': L3, 'emissions': [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]], 'tag': 'C3'},
      answers=[dict(label=r'\(\log p(y^\ast\mid x)\)', type='num', check='crflogp:C3', diagnoses=[dict(value='4.5', msg=r'Das ist der Score. \(\log p=S-\log Z\).')])],
      hints=[r'\(\log p=S-\log Z\).'],
      solution=r'\(\log p=S-\log Z=4{,}5-\log 200{,}2664\approx4{,}5-5{,}2996=-0{,}7996\). Der Fehler: „global normiert“ bezieht sich auf die Wahrscheinlichkeit (9.2); der Score (9.1) ist eine unnormierte Summe. Ein Score kann beliebig groß sein, ein Log-Wahrscheinlichkeitswert ist immer \(\le0\).',
      rubric=['Formel log p = S − log Z (2 P.)', 'Wert (1 P.)', 'Fehler benannt (1 P.)']),
 dict(id='C4', stage='transfer', kc='decoding', title='Transfer: medizinische Entitäten',
      prompt=r'Ein Tagger für Arztbriefe hat die Typen DRUG und DOSE in BIO. Ein BiRNN gibt für „Ibuprofen 400 mg“ gierig <code>B-DRUG I-DOSE I-DOSE</code> aus. Was liefert Viterbi mit harten BIO-Regeln mindestens?',
      answers=[dict(label='Antwort', type='choice', options=['Eine gültige Folge; ob „400 mg“ als DOSE erkannt wird, hängt von den Emissionen ab', 'Garantiert B-DRUG B-DOSE I-DOSE', 'Garantiert B-DRUG I-DRUG I-DRUG'], correct=0)],
      hints=['Welche Übergänge sind in der gierigen Folge verboten?'],
      solution=r'<code>B-DRUG → I-DOSE</code> ist verboten. Viterbi wählt die beste <em>gültige</em> Folge; welche das ist (z. B. <code>B-DRUG B-DOSE I-DOSE</code> oder <code>B-DRUG I-DRUG I-DRUG</code>), entscheiden die Emissionswerte. Garantiert ist nur die Gültigkeit – wie in der Fallstudie.',
      rubric=['verbotener Übergang erkannt (1 P.)', 'nur Gültigkeit garantiert (1 P.)']),
 dict(id='P0', stage='worked', kc='prf', title='Durchgerechnet: F1 aus Aufwand pro Treffer',
      prompt=r'Ein System hat 6 Treffer, 2 falsche Alarme, 4 verpasste Entitäten. Leiten Sie \(F_1\) über den mittleren Aufwand her.',
      steps=[dict(s=r'\(1/P=(6+2)/6=4/3\)', why='Ausgaben pro Treffer.'), dict(s=r'\(1/R=(6+4)/6=5/3\)', why='Gold pro Treffer.'),
             dict(s=r'Mittel: \((4/3+5/3)/2=3/2\)', why='Durchschnittlicher Aufwand.'), dict(s=r'\(F_1=2/3\approx0{,}6667\)… Kontrolle: \(2\cdot6/(12+2+4)=12/18=2/3\)', why='Kehrwert; Zählform zur Probe.')],
      answers=[dict(label='Selbsterklärung: Warum taucht TN nirgends auf?', type='choice', options=['Weder Ausgaben noch Gold zählen nicht-vorhandene, nicht-vorhergesagte Spannen', 'TN ist hier zufällig 0', 'Weil TN in R steckt'], correct=0)],
      solution=r'\(1/P=4/3\), \(1/R=5/3\), Mittel \(3/2\), \(F_1=2/3\); Probe mit der Zählform \(12/18=2/3\). TN tritt nicht auf, weil beide Aufwände nur Ausgaben und Gold-Entitäten zählen.',
      rubric=['beide Aufwände', 'Mittel und Kehrwert', 'Probe']),
 dict(id='P1', stage='independent', kc='prf', title='F1 berechnen',
      prompt=r'TP = 7, FP = 3, FN = 7. Berechnen Sie \(P\), \(R\) und \(F_1\) (Bruch oder vier Nachkommastellen).',
      answers=[dict(label=r'\(F_1\)', type='num', check='f1:7:3:7', diagnoses=[dict(value='0.6', msg=r'Das ist das arithmetische Mittel von \(P=0{,}7\) und \(R=0{,}5\).')])],
      hints=['Zählform.'],
      solution=r'\(P=7/10=0{,}7\), \(R=7/14=0{,}5\), \(F_1=14/(14+3+7)=14/24=7/12\approx0{,}5833\) – unter dem arithmetischen Mittel \(0{,}6\).',
      rubric=['P und R', 'F1', 'Vergleich mit Mittel']),
 dict(id='P2', stage='independent', kc='prf', title=r'\(F_\beta\) für recall-kritische Anwendungen',
      prompt=r'Ein Anonymisierungssystem muss möglichst alle Personennamen finden. \(P=0{,}8\), \(R=0{,}5\). Berechnen Sie \(F_2\).',
      answers=[dict(label=r'\(F_2\)', type='num', check='fbeta:4/5:1/2:2', diagnoses=[dict(value='0.6154', msg=r'Das ist \(F_1\). Für \(F_2\): \(\beta^2=4\).')])],
      hints=[r'\(F_\beta=(1+\beta^2)PR/(\beta^2P+R)\).'],
      solution=r'\(F_2=\frac{5\cdot0{,}8\cdot0{,}5}{4\cdot0{,}8+0{,}5}=\frac{2}{3{,}7}\approx0{,}5405\). Kleiner als \(F_1\approx0{,}6154\), weil das schwache \(R\) stärker zählt – passend zur Anforderung „alle Namen finden“.',
      rubric=['Formel mit β²=4', 'Wert', 'Deutung']),
 dict(id='P3', stage='proof', kc='prf', title='Beweis: F1 liegt über dem Minimum',
      prompt=r'Zeigen Sie für \(P,R\in(0,1]\): \(F_1\ge\min(P,R)\). Wo nutzen Sie \(P,R&gt;0\)?',
      answers=[dict(label='Selbstbewertung nach Lösung', type='self')],
      hints=[r'O. B. d. A. \(P\le R\); mit \(P+R\) multiplizieren.'],
      solution=r'Sei \(P\le R\). \(\frac{2PR}{P+R}\ge P\iff 2PR\ge P(P+R)\) (Multiplikation mit \(P+R&gt;0\)) \(\iff PR\ge P^2\iff R\ge P\) (Division durch \(P&gt;0\)) – wahr. \(\square\)',
      rubric=['WLOG (1 P.)', 'beide Umformungen mit Vorzeichenbegründung (2 P.)']),
 dict(id='E1', stage='transfer', kc='prf-edge', title='Konventionen ändern Mittelwerte',
      prompt=r'Drei Testsätze: Satz 1 hat \(F_1=1\), Satz 2 \(F_1=\tfrac12\), Satz 3 hat weder Gold noch Ausgaben. Berechnen Sie den Mittelwert über Sätze (a) mit <code>zero_division=0</code> und (b) mit <code>np.nan</code> (Satz fällt heraus).',
      answers=[dict(label='(a)', type='num', check='mean:1,1/2,0'), dict(label='(b)', type='num', check='mean:1,1/2')],
      hints=[r'Fall (v): Satz 3 ist \(0/0\).'],
      solution=r'(a) \((1+0{,}5+0)/3=1/2\). (b) \((1+0{,}5)/2=3/4\). Dieselben Vorhersagen ergeben je nach Konvention 0,5 oder 0,75. Deshalb gehört die Konvention in jeden Bericht; die Zählform über das ganze Korpus vermeidet das Problem.',
      rubric=['(a)', '(b)', 'Folgerung']),
 dict(id='L1', stage='independent', kc='prf-level', title='Teilüberlappung zählen',
      prompt=r'Gold: <code>Die [Deutsche Bank]ORG sitzt in [Frankfurt am Main]LOC .</code><br>System: <code>Die [Deutsche Bank]ORG sitzt in [Frankfurt]LOC am Main .</code><br>Phrasen- und Token-\(F_1\)?',
      data={'tokens': ['Die', 'Deutsche', 'Bank', 'sitzt', 'in', 'Frankfurt', 'am', 'Main', '.'], 'gold': ['O', 'B-ORG', 'I-ORG', 'O', 'O', 'B-LOC', 'I-LOC', 'I-LOC', 'O'], 'pred': ['O', 'B-ORG', 'I-ORG', 'O', 'O', 'B-LOC', 'O', 'O', 'O']},
      answers=[dict(label=r'Phrasen-\(F_1\)', type='num', check='span_f1:L1'), dict(label=r'Token-\(F_1\)', type='num', check='token_f1:L1')],
      hints=['Phrasen: Frankfurt ≠ Frankfurt am Main.'],
      solution=r'Phrasen: TP = 1 (Deutsche Bank), FP = 1 ([Frankfurt]LOC), FN = 1 ([Frankfurt am Main]LOC): \(2/4=1/2\). Token: TP = 3 (Deutsche, Bank, Frankfurt), FP = 0, FN = 2 (am, Main): \(6/8=3/4\).',
      rubric=['Phrasen', 'Token', 'Grenzfehler doppelt gezählt']),
 dict(id='M0', stage='worked', kc='micro-macro', title='Durchgerechnet: Micro als gewichtetes Mittel',
      prompt=r'PER: TP 45, FP 5, FN 5 · LOC: 30, 10, 10 · ORG: 20, 15, 15 · MISC: 1, 4, 9. Zeigen Sie, dass Micro-\(F_1\) das mit \(D_k\) gewichtete Mittel der Typ-\(F_1\) ist.',
      steps=[dict(s=r'\(D=(100;\ 80;\ 70;\ 15)\), \(\sum D=265\)', why=r'\(D_k=2\mathrm{TP}_k+\mathrm{FP}_k+\mathrm{FN}_k\).'),
             dict(s=r'\(F_{1,k}=(0{,}9;\ 0{,}75;\ 0{,}5714;\ 0{,}1333)\)', why='Zählform je Typ.'),
             dict(s=r'\(\sum_k \tfrac{D_k}{265}F_{1,k}=\tfrac{90+60+40+2}{265}=\tfrac{192}{265}\approx0{,}7245\)', why=r'\(D_kF_{1,k}=2\mathrm{TP}_k\).')],
      answers=[dict(label='Selbsterklärung: Warum hat MISC in Micro so wenig Gewicht?', type='choice', options=[r'Weil \(D_{\mathrm{MISC}}=15\) klein ist gegenüber \(\sum D=265\)', 'Weil MISC schlecht erkannt wird', 'Weil Micro O mitzählt'], correct=0)],
      solution=r'\(D=(100;80;70;15)\), Gewichte \(D_k/265\); \(D_kF_{1,k}=2\mathrm{TP}_k\) ergibt \(192/265\approx0{,}7245\) – identisch mit der gepoolten Zählform. MISC hat Gewicht \(15/265\approx0{,}0566\).',
      rubric=['D_k', 'Typ-F1', 'Identität']),
 dict(id='M1', stage='independent', kc='micro-macro', title='Support-gewichtetes Macro',
      prompt=r'Zählungen wie in B6 (PER 80/10/20, LOC 50/25/5, MISC 0/3/7). Berechnen Sie das support-gewichtete Macro-\(F_1\) (Gewicht \(\mathrm{TP}_k+\mathrm{FN}_k\)).',
      answers=[dict(label='support-gewichtet', type='num', check='weighted:80,10,20;50,25,5;0,3,7', diagnoses=[dict(value='26/33', msg=r'Das ist Micro (Gewichte \(D_k\)), nicht Support.')])],
      hints=['Support: 100, 55, 7.'],
      solution=r'Support \(100,\ 55,\ 7\) (Summe 162). \((100\cdot0{,}8421+55\cdot0{,}7692+7\cdot0)/162\approx0{,}7810\). Drei verschiedene Mittel derselben Zählungen: Micro \(0{,}7879\), support-gewichtet \(0{,}7810\), Macro \(0{,}5371\).',
      rubric=['Support je Typ', 'Wert', 'Vergleich der drei Mittel']),
 dict(id='M2', stage='transfer', kc='micro-macro', title='Transfer: Kennzahl wählen',
      prompt=r'Ein Krankenhaus will überwachen, ob ein NER-System <em>seltene</em> Medikamentennamen zuverlässig erkennt. Häufige Typen (Datum, Person) machen 90 % der Entitäten aus. Welche Kennzahl berichten Sie zuerst?',
      answers=[dict(label='Antwort', type='choice', options=['Macro-F1 (und F1 je Typ)', 'Micro-F1', 'Token-Accuracy einschließlich O'], correct=0)],
      hints=['Wer dominiert Micro?'],
      solution=r'Macro-\(F_1\) gibt jedem Typ gleiches Gewicht, ein Ausfall der seltenen Klasse wird sichtbar; zusätzlich \(F_1\) je Typ. Micro wird von den 90 % häufigen Entitäten dominiert; Accuracy mit O ist durch die vielen O-Token fast immer hoch (Satz 7).',
      rubric=['Macro mit Begründung', 'warum nicht Micro/Accuracy']),
]

for _t in T:  # code listings need real newlines (raw strings keep \n literally)
    if _t['id'] == 'S4':
        _t['prompt'] = _t['prompt'].replace(r'\\n', r'\n')

def item(id, kc, prompt, answers, solution, transfer=False, data=None):
    d = dict(id=id, kc=kc, prompt=prompt, answers=answers, solution=solution)
    if transfer: d['transfer'] = True
    if data: d['data'] = data
    return d

A = [
 item('A1', 'spans', r'Wie viele Labels braucht BIO für \(K=7\) Typen?', [dict(label='Anzahl', type='num', check='labels:BIO:7')], r'\(2\cdot7+1=15\).'),
 item('A2', 'spans', r'Ein Tagger gibt <code>B-PER I-LOC</code> über zwei Wörtern aus. Welche Spannen liest <code>conlleval</code>?', [dict(label='Antwort', type='choice', options=[r'\([w_1]\)PER und \([w_2]\)LOC', r'\([w_1\,w_2]\)PER', 'keine – die Folge ist ungültig'], correct=0)], r'<code>I-LOC</code> setzt keine LOC-Spanne fort und eröffnet daher eine neue.', transfer=True),
 item('A3', 'birnn', r'BiRNN-Tagger: \(d=300\), \(d_h=200\) je Richtung, vier Typen in BIO. Parameter ohne Einbettung?', [dict(label='Parameter', type='num', check='params:300:200:9')], r'Je Richtung \(40\,000+60\,000+200=100\,200\); beide \(200\,400\); Ausgabe \(9\cdot401=3\,609\); Summe \(204\,009\).'),
 item('A4', 'birnn', r'Ein Sprachassistent muss das Label von Wort \(t\) ausgeben, bevor Wort \(t+1\) gesprochen ist. Welche Architektur erfüllt das ohne Änderung?', [dict(label='Antwort', type='choice', options=['BiRNN im Standardaufbau über den ganzen Satz', 'Vorwärts-RNN mit Softmax je Wort', 'BiRNN mit CRF im Standardaufbau'], correct=1)], r'Nur das Vorwärts-RNN: \(h^{\rightarrow}_t\) braucht \(x_1..x_t\) (Satz 1). Die Standard-BiRNN-Varianten brauchen über \(h^{\leftarrow}\) das Satzende (Satz 2).', transfer=True),
 item('A5', 'attention', r'Unter den Annahmen von Satz 3 und \(d_k=64\): Welche Varianz hat \(q^\top k\) (ohne Skalierung)?', [dict(label='Varianz', type='num', check='int:64')], r'\(d_k=64\); nach Division durch \(\sqrt{64}=8\) ist sie 1.'),
 item('A6', 'attention', r'Anfrage \(q=(2,0)\), Schlüssel \(k_1=(1,0)\), \(k_2=(0,1)\), \(d_k=2\). Welches Gewicht \(\alpha_1\) erhält \(k_1\)?', [dict(label=r'\(\alpha_1\)', type='num', check='attnq:2,0|1,0;0,1:0')], r'Energien \(2/\sqrt2=1{,}4142\) und 0; \(\alpha_1=e^{1{,}4142}/(e^{1{,}4142}+1)\approx0{,}8044\).', transfer=True),
 item('A7', 'position', r'Self-Attention ohne Positionskodierung: Vertauscht man zwei Token einer Eingabe, was passiert mit den Ausgabevektoren?', [dict(label='Antwort', type='choice', options=['Sie werden genauso vertauscht, sonst ändert sich nichts', 'Alle Ausgaben ändern sich', 'Die Ausgaben bleiben an ihren Positionen unverändert'], correct=0)], r'Satz 4: \(\operatorname{Att}(PX)=P\operatorname{Att}(X)\).'),
 item('A8', 'position', r'RoPE mit \(\theta=0{,}25\), \(q=k=(1,0)\), Query an Position 1, Key an Position 5. Ähnlichkeit?', [dict(label='Ähnlichkeit', type='num', check='rope:0.25:1:5')], r'\(\cos((5-1)\cdot0{,}25)=\cos 1\approx0{,}5403\).', transfer=True),
 item('A9', 'decoding', r'Emissionen für „nach New York“ (O, B-LOC, I-LOC): nach (1,5; 0,2; 0,1), New (0,4; 0,9; 1,1), York (0,1; 0,3; 1,4). Verboten: Start→I-LOC, O→I-LOC. Score der besten gültigen Folge?', [dict(label='Score', type='num', check='viterbi:A9')], r'Gierig O I-LOC I-LOC ist ungültig. Beste gültige Folge O B-LOC I-LOC mit \(1{,}5+0{,}9+1{,}4=3{,}8\).', data={'labels': L3, 'emissions': [[1.5, 0.2, 0.1], [0.4, 0.9, 1.1], [0.1, 0.3, 1.4]]}),
 item('A10', 'decoding', r'Was garantiert ein CRF mit harten BIO-Übergangsregeln?', [dict(label='Antwort', type='choice', options=['Keine ungültige BIO-Folge wird ausgegeben', 'Alle Spannengrenzen sind richtig', 'Gierige Dekodierung wäre immer schlechter'], correct=0)], r'Nur Gültigkeit. Grenzen und Typen hängen von den Emissionen ab; Ratinov &amp; Roth (2009) fanden gierige Dekodierung vergleichbar.', transfer=True),
 item('A11', 'prf', r'TP = 12, FP = 4, FN = 8. \(F_1\)?', [dict(label=r'\(F_1\)', type='num', check='f1:12:4:8')], r'\(24/(24+4+8)=2/3\).'),
 item('A12', 'prf', r'Ein System markiert fast alles: \(P=0{,}2\), \(R=1\). Ein Kollege berichtet „im Mittel 0,6“. Welcher \(F_1\)-Wert ist korrekt?', [dict(label=r'\(F_1\)', type='num', check='fpr:1/5:1')], r'\(2\cdot0{,}2\cdot1/1{,}2=1/3\); \(F_1\le2P=0{,}4\).', transfer=True),
 item('A13', 'prf-edge', r'Gold enthält 3 Entitäten, das System gibt keine aus. \(F_1\) (Zählform)?', [dict(label=r'\(F_1\)', type='num', check='f1:0:0:3')], r'\(0/(0+0+3)=0\); \(P=0/0\) ist nicht definiert.'),
 item('A14', 'prf-edge', r'Kein Gold, keine Ausgabe. Was gilt für \(F_1\)?', [dict(label='Antwort', type='choice', options=[r'\(F_1=1\), weil kein Fehler gemacht wurde', r'\(F_1=0\), weil TP = 0', r'\(F_1=0/0\); ein Wert entsteht nur durch eine genannte Konvention'], correct=2)], r'Fall (v): auch die Zählform ist \(0/0\).'),
 item('A15', 'prf-level', r'Gold: <code>Der [FC Bayern München]ORG gewann in [Dortmund]LOC gegen [Borussia Dortmund]ORG .</code><br>System: <code>Der [FC Bayern]ORG [München]LOC gewann in [Dortmund]LOC gegen [Borussia Dortmund]PER .</code><br>Phrasen-\(F_1\)?', [dict(label=r'Phrasen-\(F_1\)', type='num', check='span_f1:A15')], r'TP = 1, FP = 3, FN = 2: \(2/7\).', data={'tokens': ['Der', 'FC', 'Bayern', 'München', 'gewann', 'in', 'Dortmund', 'gegen', 'Borussia', 'Dortmund', '.'], 'gold': ['O', 'B-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'B-LOC', 'O', 'B-ORG', 'I-ORG', 'O'], 'pred': ['O', 'B-ORG', 'I-ORG', 'B-LOC', 'O', 'O', 'B-LOC', 'O', 'B-PER', 'I-PER', 'O']}),
 item('A16', 'prf-level', r'Gleicher Satz wie A15. Token-\(F_1\)?', [dict(label=r'Token-\(F_1\)', type='num', check='token_f1:A15')], r'TP = 3, FP = 3, FN = 3: \(6/12=1/2\).', transfer=True),
 item('A17', 'micro-macro', r'PER: TP 60, FP 15, FN 10; ORG: TP 40, FP 20, FN 30; LOC: TP 70, FP 5, FN 5. Micro-\(F_1\)?', [dict(label=r'Micro-\(F_1\)', type='num', check='micro:60,15,10;40,20,30;70,5,5')], r'TP 170, FP 40, FN 45: \(340/425=0{,}8\).'),
 item('A18', 'micro-macro', r'Gleiche Zählungen wie A17. Macro-\(F_1\)?', [dict(label=r'Macro-\(F_1\)', type='num', check='macro:60,15,10;40,20,30;70,5,5')], r'PER \(120/145\), ORG \(80/130\), LOC \(140/150\); Mittel \(\approx0{,}7921\).'),
]
B = [
 item('B-1', 'spans', r'Wie viele Labels braucht BILOU für \(K=3\) Typen?', [dict(label='Anzahl', type='num', check='labels:BILOU:3')], r'\(4\cdot3+1=13\).'),
 item('B-2', 'spans', r'„Termine am Montag Dienstag“ mit zwei Spannen [Montag]DAY, [Dienstag]DAY. Welches Schema kann das <em>nicht</em> von einer Spanne [Montag Dienstag]DAY unterscheiden?', [dict(label='Antwort', type='choice', options=['IO', 'BIO', 'BILOU'], correct=0)], r'IO ergibt in beiden Fällen <code>DAY DAY</code> (Satz A).', transfer=True),
 item('B-3', 'birnn', r'BiRNN-Tagger: \(d=64\), \(d_h=32\) je Richtung, zwei Typen in BIO. Parameter ohne Einbettung?', [dict(label='Parameter', type='num', check='params:64:32:5')], r'\(|\mathcal L|=5\). Je Richtung \(1\,024+2\,048+32=3\,104\); beide \(6\,208\); Ausgabe \(5\cdot65=325\); Summe \(6\,533\).'),
 item('B-4', 'birnn', r'Zwei Sätze mit je 8 Wörtern unterscheiden sich nur im 5. Wort. An welchen Positionen \(t\) ist \(h^{\rightarrow}_t\) garantiert gleich? (Indizes, kommagetrennt)', [dict(label='Positionen', type='set', check='dep:8:4:forward')], r'\(t=1,2,3,4\) nach Satz 1.', transfer=True),
 item('B-5', 'attention', r'Multi-Head mit Verkettung ohne Ausgabematrix: \(n=d=512\), \(h=8\) Köpfe. Wie viele Parameter haben alle Query-Projektionen zusammen?', [dict(label='Parameter', type='num', check='int:262144')], r'\(8\) Köpfe je \(512\times64\): \(8\cdot32\,768=262\,144=512^2\) – so viele wie eine einzelne \(512\times512\)-Projektion.'),
 item('B-6', 'attention', r'Warum teilt man die Skalarprodukte durch \(\sqrt{d_k}\)?', [dict(label='Antwort', type='choice', options=[r'Unter Unabhängigkeitsannahmen hat \(q^\top k\) Varianz \(d_k\); die Division bringt sie auf 1 und hält die Softmax aus der Sättigung', r'Damit die Gewichte sich zu 1 summieren', r'Weil die Werte \(v_j\) sonst zu groß werden'], correct=0)], r'Satz 3; die Normierung auf Summe 1 leistet die Softmax selbst.', transfer=True),
 item('B-7', 'position', r'Trigonometrische Kodierung mit \(d_{\text{model}}=4\): Berechnen Sie \(\mathrm{POS}(3,2)\).', [dict(label=r'\(\mathrm{POS}(3,2)\)', type='num', check='sinpos:3:2:4')], r'\(d=2\) gerade: \(\sin(3/10000^{2/4})=\sin(0{,}03)\approx0{,}0300\).'),
 item('B-8', 'position', r'RoPE: Query an Position 3, Key an Position 3 + \(\Delta\). Wovon hängt die Ähnlichkeit \(\big(R(3\theta)q\big)^\top R((3+\Delta)\theta)k\) ab?', [dict(label='Antwort', type='choice', options=[r'nur von \(q\), \(k\) und \(\Delta\)', r'von der absoluten Position 3', r'von der Satzlänge'], correct=0)], r'\(q^\top R(\Delta\theta)k\).', transfer=True),
 item('B-9', 'decoding', r'Emissionen (O, B-LOC, I-LOC): Wort 1 (0,2; 1,0; 0,3), Wort 2 (0,5; 0,1; 0,9), Wort 3 (1,2; 0; 0,4). Verboten: Start→I-LOC, O→I-LOC. Score der besten gültigen Folge?', [dict(label='Score', type='num', check='viterbi:B-9')], r'Gierig B-LOC I-LOC O ist gültig; Viterbi ändert nichts: \(1{,}0+0{,}9+1{,}2=3{,}1\).', data={'labels': L3, 'emissions': [[0.2, 1.0, 0.3], [0.5, 0.1, 0.9], [1.2, 0, 0.4]]}),
 item('B-10', 'decoding', r'Ein Tagger wird mit Gold-Vorgängerlabels trainiert, im Test mit eigenen Vorhersagen betrieben. Wie heißt das Problem?', [dict(label='Antwort', type='choice', options=['Exposure Bias', 'Label Bias', 'Overfitting'], correct=0)], r'Exposure Bias. Label Bias entsteht durch lokale Normierung.', transfer=True),
 item('B-11', 'prf', r'TP = 18, FP = 2, FN = 12. \(F_1\)?', [dict(label=r'\(F_1\)', type='num', check='f1:18:2:12')], r'\(36/50=0{,}72\).'),
 item('B-12', 'prf', r'Ein vorsichtiges System: \(P=0{,}9\), \(R=0{,}3\). \(F_1\)?', [dict(label=r'\(F_1\)', type='num', check='fpr:9/10:3/10')], r'\(2\cdot0{,}27/1{,}2=0{,}45\).', transfer=True),
 item('B-13', 'prf-edge', r'Kein Gold; das System gibt 4 Entitäten aus. Was gilt?', [dict(label='Antwort', type='choice', options=[r'\(P=0/0\), \(R=0\), \(F_1=0\)', r'\(P=0\), \(R=0/0\), \(F_1=0\) (Zählform)', r'\(P=0\), \(R=0\), \(F_1=0/0\)'], correct=1)], r'Fall (iv).'),
 item('B-14', 'prf-edge', r'TP = 0, FP = 2, FN = 5. Was liefert \(2PR/(P+R)\)?', [dict(label='Antwort', type='choice', options=['0', r'\(0/0\), also keinen Wert', r'\(2/7\)'], correct=1)], r'Fall (ii): \(P=R=0\); die Zählform liefert \(0/7=0\).'),
 item('B-15', 'prf-level', r'Gold: <code>[Barack Obama]PER traf [Angela Merkel]PER in [Berlin]LOC</code><br>System: <code>[Barack Obama]PER traf [Angela Merkel]LOC in [Berlin]LOC</code><br>Phrasen-\(F_1\)?', [dict(label=r'Phrasen-\(F_1\)', type='num', check='span_f1:B-15')], r'TP = 2, FP = 1, FN = 1: \(2/3\).', data={'tokens': ['Barack', 'Obama', 'traf', 'Angela', 'Merkel', 'in', 'Berlin'], 'gold': ['B-PER', 'I-PER', 'O', 'B-PER', 'I-PER', 'O', 'B-LOC'], 'pred': ['B-PER', 'I-PER', 'O', 'B-LOC', 'I-LOC', 'O', 'B-LOC']}),
 item('B-16', 'prf-level', r'Gleicher Satz wie B-15. Token-\(F_1\)?', [dict(label=r'Token-\(F_1\)', type='num', check='token_f1:B-15')], r'TP = 3, FP = 2, FN = 2: \(3/5\). Hier ist die Token-Ebene strenger, weil die falsch typisierte Entität zwei Wörter lang ist.', transfer=True),
 item('B-17', 'micro-macro', r'PER: TP 50, FP 10, FN 10; ORG: TP 10, FP 30, FN 10; LOC: TP 90, FP 10, FN 10. Micro-\(F_1\)?', [dict(label=r'Micro-\(F_1\)', type='num', check='micro:50,10,10;10,30,10;90,10,10')], r'TP 150, FP 50, FN 30: \(300/380=15/19\approx0{,}7895\).'),
 item('B-18', 'micro-macro', r'Gleiche Zählungen wie B-17. Wie groß ist das Gewicht von ORG in Micro-\(F_1\) als gewichtetem Mittel der Typ-\(F_1\)-Werte?', [dict(label=r'\(w_{\mathrm{ORG}}\)', type='num', check='microweight:50,10,10;10,30,10;90,10,10:1')], r'\(D=(120;\,60;\,200)\), \(w_{\mathrm{ORG}}=60/380\approx0{,}1579\) – größer als der Gold-Anteil \(20/180\approx0{,}1111\), weil ORG viele Fehlalarme hat.', transfer=True),
]

CASE = {
    'labels': L7,
    'sentences': [
        {'tokens': ['Angela', 'Merkel', 'besuchte', 'Siemens', 'in', 'München', '.'], 'gold': ['B-PER', 'I-PER', 'O', 'B-ORG', 'O', 'B-LOC', 'O'],
         'emissions': [{'B-PER': 2}, {'I-PER': 2}, {'O': 2}, {'B-LOC': 1.4, 'B-ORG': 1.2}, {'O': 2}, {'B-LOC': 2}, {'O': 2}]},
        {'tokens': ['Die', 'Bayern', 'spielen', 'in', 'New', 'York', '.'], 'gold': ['O', 'B-ORG', 'O', 'O', 'B-LOC', 'I-LOC', 'O'],
         'emissions': [{'O': 2}, {'B-ORG': 2}, {'O': 2}, {'O': 2}, {'B-LOC': 2}, {'I-ORG': 1.2, 'I-LOC': 1.0}, {'O': 2}]},
        {'tokens': ['Barack', 'Obama', 'traf', 'Angela', 'Merkel', 'in', 'Berlin', '.'], 'gold': ['B-PER', 'I-PER', 'O', 'B-PER', 'I-PER', 'O', 'B-LOC', 'O'],
         'emissions': [{'B-PER': 2}, {'O': 1.1, 'I-PER': 1.0}, {'O': 2}, {'B-PER': 2}, {'I-PER': 2}, {'O': 2}, {'B-LOC': 2}, {'I-LOC': 1.1, 'O': 1.0}]},
    ]}

def card(key, kc, kind, prompt, answer, why, source, example=None, mistake=None, diagram=None, prereq=None, cloze=None):
    c = dict(key=key, kc=kc, type=kind, prompt=prompt, answer=answer, why=why, source=source)
    for k, v in (('example', example), ('mistake', mistake), ('diagram', diagram), ('prereq', prereq), ('cloze', cloze)):
        if v: c[k] = v
    return c

CARDS = [
 # spans
 card('spans/io-not-injective', 'spans', 'concept', r'Zwei <em>benachbarte</em> Spannen gleichen Typs, [Montag]DAY [Dienstag]DAY: Welche Information geht bei IO-Kodierung verloren?', r'Die Grenze zwischen den Spannen: IO ergibt <code>DAY DAY</code> – genau wie die eine Spanne [Montag Dienstag].', r'IO hat nur ein Label je Typ; Spannenanfänge sind nicht markiert. BIO markiert sie mit B- und ist auf gültigen Folgen umkehrbar (Satz A).', 'Lehrbuch §2, Satz A; Vorlesung PDF-S. 16', diagram='bio_schemes.svg'),
 card('spans/label-count', 'spans', 'cloze', '', '', r'IO: ein Label je Typ; BIO: B und I; BILOU: B, I, L, U – jeweils plus O.', 'Vorlesung PDF-S. 15–18', cloze=r'Mit \(K\) Entitätstypen hat IO {{c1::\(K+1\)}}, BIO {{c1::\(2K+1\)}} und BILOU {{c1::\(4K+1\)}} Labels.'),
 card('spans/conlleval-i', 'spans', 'concept', r'Wie liest das CoNLL-Skript <code>conlleval</code> ein <code>I-LOC</code>, das direkt auf <code>O</code> folgt?', 'Als Beginn einer neuen LOC-Spanne.', r'Die Folge ist ungültig; das Skript repariert sie, statt das Label zu verwerfen. Andere Decoder verwerfen solche Labels – dann sind Ergebnisse nicht vergleichbar (Aufgabe S4).', 'Lehrbuch §2', mistake=r'„Ungültige Labels werden von allen Decodern ignoriert.“'),
 card('spans/encode-mini', 'spans', 'case', r'BIO-Folge für <code>Tickets nach New York und Boston</code> mit [New York]CITY und [Boston]CITY?', r'<code>O O B-CITY I-CITY O B-CITY</code>', r'Jede Spanne beginnt mit B-; „Boston“ beginnt eine neue Spanne und bekommt daher B-, nicht I-.', 'Lehrbuch §2; Aufgabe S2'),
 card('spans/bilou-evidence', 'spans', 'research', r'Welchen Schemavergleich berichten Ratinov &amp; Roth (2009) für ihr NER-System auf CoNLL-2003?', 'BILOU schnitt signifikant besser ab als BIO.', 'BILOU markiert Spannenende und Einwortspannen explizit. Ein Befund zu diesem einen System mit handgebauten Merkmalen, kein allgemeiner Satz.', 'Ratinov &amp; Roth 2009, S. 148, Tab. 2 S. 150'),
 # birnn
 card('birnn/abhaengigkeit-vorwaerts', 'birnn', 'concept', r'Vorwärts-RNN \(h^{\rightarrow}_t=f(h^{\rightarrow}_{t-1},x_t)\): Von welchen Eingaben kann \(h^{\rightarrow}_t\) abhängen?', r'Nur von \(x_1,\dots,x_t\).', r'Induktion über die Rekursion: In der Formel für \(h^{\rightarrow}_t\) kommt kein \(x_s\) mit \(s&gt;t\) vor (Satz 1). Gilt für jede Zelle \(f\), auch LSTM und GRU.', 'SLP3 §14.4.2, Gl. 14.16, S. 313', diagram='dependency_cones.svg', mistake=r'„Ein RNN hat globalen Kontext, also sieht jeder Zustand den ganzen Satz.“'),
 card('birnn/washington', 'birnn', 'case', r'„Washington signed“ gegen „Washington state“: Warum muss ein Tagger, der Wort 1 nur aus \(h^{\rightarrow}_1\) klassifiziert, beiden „Washington“ dasselbe Label geben?', r'\(h^{\rightarrow}_1=\tanh(Ue_1+b)\) ist in beiden Sätzen derselbe Vektor; gleiche Eingabe, gleiche Ausgabe.', r'Das unterscheidende Wort steht an Position 2. Im Lehrbuchbeispiel ist \(h^{\rightarrow}_1=(0{,}7616;\,0)\) in beiden Sätzen.', 'Lehrbuch §4, Abb. 4.1'),
 card('birnn/definition', 'birnn', 'concept', r'Wie ist der Zustand \(h^{\mathrm{bi}}_t\) eines BiRNN definiert, und welche Dimension hat er bei \(d_h\) je Richtung?', r'\(h^{\mathrm{bi}}_t=[h^{\rightarrow}_t;\,h^{\leftarrow}_t]\in\mathbb R^{2d_h}\), aus zwei RNNs mit getrennten Parametern.', r'Die Verkettung vereinigt die Abhängigkeitsbereiche \(\{1,\dots,t\}\) und \(\{t,\dots,T\}\) zum ganzen Satz (Satz 2).', 'Vorlesung PDF-S. 80; SLP3 §14.4.2, S. 313–314'),
 card('birnn/latenz', 'birnn', 'concept', r'Ein BiRNN im <em>Standardaufbau</em> (Rückwärtsrichtung über den ganzen Satz): Wann kann es das Label von Wort \(t\) frühestens ausgeben?', 'Erst wenn der Satz vollständig vorliegt.', r'\(h^{\leftarrow}_t\) hängt vom letzten Wort ab. Varianten mit begrenzter Vorausschau \(k\) geben nach \(k\) weiteren Wörtern aus – mit höchstens \(k\) Wörtern rechtem Kontext.', 'Lehrbuch §5(a); SLP3 §14.4.2, S. 313', example=r'Vorausschau \(k=2\): Label für \(t=4\) sieht \(x_1,\dots,x_6\).'),
 card('birnn/softmax-unabhaengig', 'birnn', 'concept', r'Ein BiRNN-Tagger wählt jedes Label <em>einzeln</em> per Softmax und \(\arg\max\). Was verhindert dann die Ausgabe <code>O I-LOC</code>?', 'Nichts – erst ein strukturierter Decoder (z. B. CRF mit Übergangsregeln) schließt sie aus.', 'Bei unabhängiger Dekodierung hängen die Labels nur über die gemeinsamen Eingaben zusammen, nicht über eine Bewertung ganzer Folgen.', 'Vorlesung PDF-S. 83, 85'),
 card('birnn/params', 'birnn', 'math', r'Parameterzahl eines BiRNN-Taggers (Elman-Zellen, ohne Einbettungsmatrix) mit Einbettung \(d\), Zustand \(d_h\) je Richtung, \(|\mathcal L|\) Labels?', r'\(2(d_h^2+d_hd+d_h)+|\mathcal L|(2d_h+1)\)', r'Je Richtung \(W,U,b\); die Ausgabe \(W_o\) liest den verketteten Zustand mit \(2d_h\) Komponenten. LSTM-Zellen haben etwa viermal so viele rekurrente Parameter.', 'Lehrbuch §5', example=r'\(d=100,\ d_h=128,\ |\mathcal L|=9\): \(60\,937\).'),
 card('birnn/error-wo', 'birnn', 'error', r'Fehler finden: „Die Ausgabeschicht eines BiRNN-Taggers hat \(|\mathcal L|\cdot d_h+|\mathcal L|\) Parameter.“', r'Falsch: \(W_o\) hat \(2d_h\) Spalten, also \(|\mathcal L|(2d_h+1)\) Parameter.', r'Der Klassifikator liest die Verkettung \([h^{\rightarrow}_t;h^{\leftarrow}_t]\), nicht nur eine Richtung.', 'Lehrbuch §5; Aufgabe B1'),
 # attention
 card('attention/formel', 'attention', 'math', r'Skalierte Dot-Product-Attention für \(Q,K,V\) mit Schlüsseldimension \(d_k\)?', r'\(\operatorname{softmax}\!\big(QK^\top/\sqrt{d_k}\big)\,V\), Softmax zeilenweise.', 'Ähnlichkeit je Anfrage-Schlüssel-Paar, normiert zu Gewichten mit Summe 1, dann gewichtete Summe der Werte.', 'Vorlesung PDF-S. 53; SLP3 §7.3, Gl. 7.34, S. 188', diagram='attention_geometry.svg'),
 card('attention/gelernt', 'attention', 'concept', 'Welche Größen einer Self-Attention-Schicht sind gelernte Parameter, welche nicht?', r'Gelernt: \(W_Q,W_K,W_V\) (beim Transformer auch \(W_O\)). Nicht gelernt: die Gewichte \(\alpha_{ij}\).', r'Die \(\alpha_{ij}\) werden für jede Eingabe aus Anfrage und Schlüsseln neu berechnet – darum passen sie sich jedem Satz an.', 'Vorlesung PDF-S. 46', mistake=r'„Die Attention-Gewichte sind trainierte Parameter.“'),
 card('attention/skalierung', 'attention', 'math', r'Unter welchen Annahmen hat \(q^\top k\) mit \(q,k\in\mathbb R^{d_k}\) die Varianz \(d_k\)?', r'Alle Komponenten unabhängig, Erwartungswert 0, Varianz 1.', r'Dann hat jeder Summand \(q_ik_i\) Varianz 1, und die \(d_k\) Summanden sind unkorreliert. Geteilt durch \(\sqrt{d_k}\) ist die Varianz 1. Vaswani et al. formulieren den Effekt vorsichtig als Vermutung („We suspect“).', 'Vaswani et al. 2017, §3.2.1 mit Fn. 1; Lehrbuch Satz 3'),
 card('attention/sharpening', 'attention', 'case', r'Energien \((0{,}7071;\ 0{,}7071;\ 1{,}4142)\) ergeben \(\alpha_3\approx0{,}5035\). Was passiert mit \(\alpha_3\), wenn alle Energien viermal so groß sind?', 'Es wächst stark (gegen 1): Die Softmax wird spitzer und nähert sich einem argmax.', r'Die Softmax hängt von Differenzen ab; viermal größere Differenzen werden exponentiell betont. Ihre Gradienten nach den übrigen Energien werden klein.', 'Lehrbuch §6, Abb. 6.1'),
 card('attention/convex', 'attention', 'concept', r'Wo liegt der Ausgabevektor \(o_i=\sum_j\alpha_{ij}v_j\) relativ zu den Werten \(v_j\)?', r'In der konvexen Hülle der \(v_j\): Gewichte \(\ge0\) mit Summe 1.', 'Self-Attention mischt Werte; sie kann keinen Wert außerhalb ihrer Hülle erzeugen. Neue Richtungen entstehen erst durch Projektionen und Feed-Forward-Schichten.', 'Lehrbuch §6, Abb. 6.1'),
 card('attention/burger', 'attention', 'case', r'Datenbank-Analogie der Vorlesung: Anfrage „burger“, Ähnlichkeiten 0,5 / 0 / 0,5 / 0 zu den Werten 12 / 5 / 10 / 6. Welches Ergebnis liefert die gewichtete Summe?', '11', r'Self-Attention gibt die gewichtete Summe der Werte aus: \(0{,}5\cdot12+0{,}5\cdot10\). Die Gewichte kommen aus der Ähnlichkeit von Anfrage und Schlüssel.', 'Vorlesung PDF-S. 40'),
 card('attention/multihead', 'attention', 'concept', r'Warum ändert die Aufteilung in \(h\) Köpfe mit Verkettung die Zahl der Projektionsparameter nicht?', r'\(h\) Projektionen der Größe \(n\times(d/h)\) haben zusammen \(n\cdot d\) Einträge – so viele wie eine \(n\times d\)-Projektion.', r'Erst die Ausgabematrix \(W_O\in\mathbb R^{d\times d}\) des Transformers fügt \(d^2\) Parameter hinzu.', 'Vorlesung PDF-S. 58; SLP3 Gl. 7.35, S. 188'),
 # position
 card('position/permutation', 'position', 'concept', r'Self-Attention ohne Positionskodierung: Was gilt für \(\operatorname{Att}(PX)\), wenn \(P\) die Token permutiert?', r'\(\operatorname{Att}(PX)=P\operatorname{Att}(X)\) – die Ausgaben werden nur mitpermutiert.', '„Marry kills John“ und „John kills Marry“ geben jedem Wort denselben Vektor; die Reihenfolge ist unsichtbar (Satz 4).', 'Vorlesung PDF-S. 60–62; Lehrbuch Satz 4'),
 card('position/sinus-linear', 'position', 'math', r'Sinus-Kodierung, ein Frequenzpaar \(\omega\): Wie hängt die Kodierung von Position \(i+\Delta\) von der von \(i\) ab?', r'Linear: Drehung um den Winkel \(\omega\Delta\), unabhängig von \(i\).', 'Folgt aus den Additionstheoremen. Die Originalarbeit nennt genau diese Eigenschaft als Motivation.', 'Vaswani et al. 2017, §3.5; Lehrbuch §7'),
 card('position/rope', 'position', 'math', r'RoPE dreht \(q\) um \(m\theta\) und \(k\) um \(n\theta\). Wovon hängt \(\big(R(m\theta)q\big)^\top R(n\theta)k\) ab?', r'Nur von \(q\), \(k\) und dem Abstand \(n-m\): es ist \(q^\top R((n-m)\theta)k\).', r'\(R(\varphi)^\top=R(-\varphi)\) und \(R(a)R(b)=R(a+b)\).', 'Vorlesung PDF-S. 69; Lehrbuch §7'),
 card('position/learned-nachteil', 'position', 'concept', 'Welche zwei Nachteile nennt die Vorlesung für gelernte absolute Positionsvektoren?', 'Begrenzte Länge; große Positionen kommen im Training selten vor.', 'Die Vektoren bilden eine Tabelle fester Länge: Für Positionen über der Trainingslänge existiert kein Eintrag.', 'Vorlesung PDF-S. 67'),
 # decoding (CRF score and probability split, Issue #7)
 card('decoding/crf-score', 'decoding', 'math', r'Wie lautet der <em>Score</em> \(S(x,y)\) einer Labelfolge im linear-chain-CRF – und ist er normiert?', r'\(S(x,y)=\sum_{t=1}^{T}\big(s_t(y_t)+A_{y_{t-1},y_t}\big)\) mit \(y_0=\text{Start}\); <b>nicht</b> normiert.', r'Emissionswerte \(s_t\) aus dem BiRNN plus Übergangswerte \(A\). Der Score ist eine beliebige reelle Zahl; Viterbi maximiert ihn.', 'Lehrbuch §9, Gl. (9.1); SLP3 §18.5', diagram='viterbi_lattice.svg', mistake=r'„Der CRF-Score ist global normiert.“'),
 card('decoding/crf-prob', 'decoding', 'math', r'Wie wird aus dem CRF-Score \(S(x,y)\) eine Wahrscheinlichkeit?', r'\(p(y\mid x)=\exp S(x,y)\,/\,Z(x)\) mit \(Z(x)=\sum_{y\prime\text{ gültig}}\exp S(x,y\prime)\).', r'Normiert wird global über alle (gültigen) Labelfolgen – das unterscheidet das CRF von lokal normierten Schrittmodellen.', 'Lehrbuch §9, Gl. (9.2)', diagram='crf_probabilities.svg'),
 card('decoding/forward-vs-viterbi', 'decoding', 'concept', r'Welche eine Operation unterscheidet den Forward-Algorithmus (für \(Z\)) vom Viterbi-Algorithmus?', r'Summe statt Maximum über die Vorgänger (bei gleicher Rekursion).', r'Viterbi: \(\delta_t=s_t+\max(\delta_{t-1}+A)\). Forward: \(\alpha_t=e^{s_t}\sum\alpha_{t-1}e^{A}\). Beide kosten \(O(T|\mathcal L|^2)\).', 'Lehrbuch §9, Abb. 9.1'),
 card('decoding/prob-mini', 'decoding', 'case', r'Bester Pfad mit Score \(S=4{,}5\), Zustandssumme \(Z\approx200{,}2664\). Wie groß ist \(p(y^\ast\mid x)\)?', r'\(e^{4{,}5}/200{,}2664\approx0{,}4495\).', r'Höchster Score heißt nicht hohe Sicherheit: Mehrere gültige Konkurrenten liegen nur wenig dahinter. \(\log p=S-\log Z\approx-0{,}7996\).', 'Lehrbuch §9; Aufgaben C2, C3'),
 card('decoding/garantie', 'decoding', 'concept', 'Was garantiert Viterbi mit harten BIO-Übergangsregeln – und was nicht?', 'Garantiert: keine ungültige Folge. Nicht garantiert: richtige Grenzen und Typen.', r'Eine gültige, aber falsche Folge wie <code>B-LOC I-LOC</code> über „Berlin .“ bleibt erlaubt (Fallstudie).', 'Lehrbuch §13'),
 card('decoding/label-vs-exposure', 'decoding', 'concept', 'Label Bias und Exposure Bias: Was ist jeweils die Ursache?', 'Label Bias: lokale Normierung je Schritt. Exposure Bias: Training mit Gold-Vorgängern, Test mit eigenen Vorhersagen.', 'Globale Normierung (CRF) adressiert Label Bias, nicht Exposure Bias.', 'Lafferty et al. 2001; Andor et al. 2016, S. 2442; Vorlesung PDF-S. 84'),
 card('decoding/greedy-evidence', 'decoding', 'research', 'Was fanden Ratinov &amp; Roth (2009) zu gieriger Dekodierung gegenüber Viterbi in ihrem NER-System?', 'Vergleichbare Ergebnisse bei weit geringerem Rechenaufwand.', 'Ein empirisches Gegengewicht zu „ein CRF ist immer nötig“ – gebunden an dieses System.', 'Ratinov &amp; Roth 2009, S. 148'),
 # prf
 card('prf/zaehlform', 'prf', 'math', r'\(F_1\) in TP, FP, FN?', r'\(\dfrac{2\mathrm{TP}}{2\mathrm{TP}+\mathrm{FP}+\mathrm{FN}}\)', r'Kehrwert des Mittels von \(1/P\) (Ausgaben pro Treffer) und \(1/R\) (Gold pro Treffer) – das harmonische Mittel.', 'SLP3 §4.9, Gl. 4.42–4.44, S. 114', diagram='f1_contours.svg'),
 card('prf/schranke', 'prf', 'math', r'Welche obere Schranke hat \(F_1\) in Abhängigkeit von \(\min(P,R)\)?', r'\(F_1\le2\min(P,R)\)', 'Eine schwache Größe lässt sich durch eine starke nicht ausgleichen (Satz 6).', 'Lehrbuch Satz 6', example=r'\(P=0{,}1,\ R=1\): \(F_1\approx0{,}182\le0{,}2\).'),
 card('prf/keine-tn', 'prf', 'concept', 'Warum enthalten P, R und F1 bei NER keine True Negatives?', r'Ein TN wäre eine nicht vorhandene, nicht vorhergesagte Spanne – davon gibt es \(T(T+1)/2\) Kandidaten.', 'Bei 30 Wörtern 465 mögliche Spannen; eine Kennzahl mit TN würde von dieser Zahl beherrscht.', 'Lehrbuch §10'),
 card('prf/fbeta', 'prf', 'math', r'Wofür steht \(\beta\) in \(F_\beta=\frac{(1+\beta^2)PR}{\beta^2P+R}\)?', r'\(\beta&gt;1\) gewichtet Recall stärker, \(\beta&lt;1\) Precision; \(\beta=1\) ergibt \(F_1\).', r'Beispiel Anonymisierung (alle Namen finden): \(F_2\) statt \(F_1\).', 'SLP3 §4.9, S. 114; Aufgabe P2'),
 # prf-edge
 card('prf-edge/nichts-ausgegeben', 'prf-edge', 'case', 'Gold hat 3 Entitäten, das System gibt keine aus. P, R und F1?', r'\(P=0/0\) (nicht definiert), \(R=0\), \(F_1=0\) über die Zählform.', 'Ohne Ausgaben gibt es keinen Anteil richtiger Ausgaben; die Zählform hat den Nenner 3.', 'Lehrbuch §10, Fall (iii)'),
 card('prf-edge/tp-null', 'prf-edge', 'concept', r'TP = 0, FP &gt; 0, FN &gt; 0: Was liefert \(2PR/(P+R)\), was die Zählform?', r'\(2PR/(P+R)=0/0\); die Zählform liefert 0.', r'Hier ist \(P=R=0\). Deshalb rechnet man mit der Zählform (Satz 5).', 'Lehrbuch Satz 5, Fall (ii)'),
 card('prf-edge/beide-leer', 'prf-edge', 'concept', r'Weder Gold noch Ausgaben: Welcher \(F_1\)-Wert ist korrekt?', r'Keiner ist erzwungen: \(0/0\). Ein Wert entsteht nur durch eine genannte Konvention.', 'scikit-learn: zero_division = 0, 1 oder NaN; Mittelwerte über Sätze hängen davon ab (Aufgabe E1).', 'scikit-learn 1.9.1; Lehrbuch Fall (v)'),
 # prf-level
 card('prf-level/doppelt', 'prf-level', 'concept', 'Wie zählt ein Typfehler bei richtigen Grenzen auf Phrasen-Ebene?', 'Als ein FP und ein FN.', 'Die System-Spanne passt zu keiner Gold-Spanne exakt, und die Gold-Spanne bleibt unerkannt. Weglassen kostet nur ein FN (Manning 2006).', 'Vorlesung PDF-S. 21; Manning 2006'),
 card('prf-level/rangfolge', 'prf-level', 'case', r'Folienbeispiel „First Bank of Chicago“: System findet [Bank of Chicago] und den Betrag. Phrasen- und Token-\(F_1\)?', r'Phrasen \(1/2\), Token \(8/9\).', 'Phrasen-Zählung bestraft den Grenzfehler doppelt, Token-Zählung belohnt die Teilüberlappung.', 'Vorlesung PDF-S. 21–22'),
 # micro-macro
 card('micro-macro/gewicht', 'micro-macro', 'math', r'Mit welchem Gewicht geht Typ \(k\) in Micro-\(F_1\) als Mittel der Typ-\(F_1\)-Werte ein?', r'\(w_k=D_k/\sum_lD_l\) mit \(D_k=2\mathrm{TP}_k+\mathrm{FP}_k+\mathrm{FN}_k\).', r'Wegen \(D_kF_{1,k}=2\mathrm{TP}_k\). Fehlalarme erhöhen das Gewicht eines Typs – es ist nicht der Gold-Anteil.', 'Lehrbuch §12, Gl. (12.1)'),
 card('micro-macro/error-support', 'micro-macro', 'error', r'Fehler finden: „Micro-\(F_1\) gewichtet MISC mit 7 von 162 Gold-Entitäten“ (PER 80/10/20, LOC 50/25/5, MISC 0/3/7).', r'Falsch: Das Micro-Gewicht ist \(D_{\mathrm{MISC}}/\sum D=10/330\). 7/162 ist der Support-Anteil.', 'Support-Gewichte gehören zum support-gewichteten Macro-F1, nicht zu Micro.', 'Lehrbuch §12; Aufgabe B6'),
 card('micro-macro/unterschied', 'micro-macro', 'concept', 'Was gewichten Micro-F1, Macro-F1 und support-gewichtetes Macro-F1 jeweils?', r'Micro: nach \(D_k\) (jede Entscheidung). Macro: jeden Typ gleich. Support-gewichtet: nach Gold-Anteil.', 'Dieselben Zählungen ergeben drei verschiedene Werte; der Bericht muss die Definition nennen.', 'Lehrbuch §12; Aufgabe M1'),
 card('micro-macro/accuracy', 'micro-macro', 'concept', 'Unter welcher Bedingung ist Micro-F1 gleich der Accuracy?', 'Jedes Token genau ein Gold- und ein System-Label, und alle Klassen einschließlich O werden gepoolt.', 'Dann ist jeder Fehler genau ein FP und ein FN (Satz 7). Deshalb lässt die NER-Auswertung O weg.', 'Lehrbuch Satz 7'),
]

KC_MAP = {
    'spans': dict(sections=['spannen', 'ner'], lecture='PDF-S. 4–18', textbook='SLP3 §9.5.2 S. 239; §18.3 S. 405', research=['ratinov', 'lample', 'conll'], scenes=['spans']),
    'birnn': dict(sections=['tagger', 'rnn', 'birnn'], lecture='PDF-S. 24–29, 77–80', textbook='SLP3 §14.4–14.4.2 S. 312–314', research=['schuster'], scenes=['birnn']),
    'attention': dict(sections=['attention', 'architektur'], lecture='PDF-S. 31–58, 72–76', textbook='SLP3 §7.1–7.3 S. 179–188', research=['vaswani'], scenes=['attention']),
    'position': dict(sections=['position'], lecture='PDF-S. 60–70', textbook='SLP3 §7.4 S. 191–193', research=['vaswani', 'su'], scenes=['attention']),
    'decoding': dict(sections=['struktur', 'fallstudie'], lecture='PDF-S. 82–85', textbook='SLP3 §18.4.5–18.5 S. 411–419; §9.5.3 S. 239–241', research=['lafferty', 'andor', 'ratinov', 'huang', 'lample'], scenes=['viterbi']),
    'prf': dict(sections=['prf'], lecture='PDF-S. 20–21', textbook='SLP3 §4.9 S. 112–114', research=[], scenes=['f1']),
    'prf-edge': dict(sections=['prf'], lecture='– (Vertiefung)', textbook='SLP3 §4.9; scikit-learn zero_division', research=['sklearn'], scenes=['f1']),
    'prf-level': dict(sections=['einheit'], lecture='PDF-S. 21–22', textbook='SLP3 §9.5.4 S. 241', research=['conll', 'manning'], scenes=['counter']),
    'micro-macro': dict(sections=['mittelung'], lecture='– (Vertiefung)', textbook='SLP3 §4.9.1 S. 114–115', research=['opitz'], scenes=['micromacro']),
}

# ---- v5 (Issue #8): Attention-Mikrosequenz, ausführliche Lösungen, Anki-Anreicherung, Labor-Verknüpfung ----
T.extend(V5.TASKS)
T.append(V7.AT10)
A.append(V7.A19)
B.append(V7.B19)
for it in A + B:
    if it['id'] in V5W.W:
        it['worked'] = V5W.W[it['id']]; it['rubric'] = V5W.R[it['id']]
CARDS.extend(V5.CARDS)
for c in CARDS:
    for k, v in V5.CARD_EXTRAS.get(c['key'], {}).items():
        c[k] = v
KC_MAP['attention']['research'] = KC_MAP['attention']['research'] + ['jain', 'wiegreffe']

unit = {
    'id': 'nlp-sequence-labeling', 'version': '7.0.0', 'course': 'Natural Language Processing', 'chapter': '09 Neural Sequence Labeling',
    'title': 'Neuronale Sequenzmarkierung',
    'subtitle': 'NER und Spannen · RNN, BiRNN, Self-Attention, Positionen · CRF und Viterbi · Precision, Recall, F1 · Fallstudie',
    'status': 'Status v7: Referenzsequenz Self-Attention in Prüfung (keine Selbstfreigabe). v1, v3, v4, v5, v6.1: HUMAN_REJECTED.',
    'text': 'text.html', 'kcs': KCS, 'kc_map': KC_MAP,
    'toy': {'emb': {'Washington': [1, 0], 'signed': [0, 1], 'state': [0, -1]}, 'a_fw': 0.5, 'a_bw': 0.8},
    'tasks': T, 'exam_forms': {'A': A, 'B': B}, 'case': CASE, 'cards': CARDS,
    'sources': json.loads((OUT.parent / 'src' / 'sources.json').read_text(encoding='utf-8')) + V5.SOURCES,
    'lab': V5.LAB, 'numeric_examples': [V5.BANK],
}
OUT.write_text(json.dumps(unit, ensure_ascii=False, indent=1), encoding='utf-8')
print('wrote', OUT, len(T), 'tasks', len(A) + len(B), 'exam items', len(CARDS), 'cards')
