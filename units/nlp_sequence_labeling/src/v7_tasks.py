"""v7 (Issue #10): Transferaufgabe der Referenzsequenz und zwei neue, unabhängige Klausuraufgaben.

AT10 kehrt die Rechenrichtung um (Ausgabe → Gewichte → Scores → Query). Die Klausuraufgaben A19/B-19 nutzen andere
Daten und andere Prüfroutinen (keine Wiederverwendung der Übung). Alle Zahlen werden von verify() nachgerechnet.
"""

AT10 = dict(
    id='AT10', stage='transfer', kc='attention', title='Transfer: Attention rückwärts rechnen',
    prompt=r'''Drei Wörter A, B, C mit Values \(v_A=(2,0)\), \(v_B=(0,2)\), \(v_C=(0,0)\) und Keys \(k_A=(1,0)\), \(k_B=(0,1)\), \(k_C=(0,0)\); \(d_k=2\).
Ein Modell soll für das betrachtete Wort die Ausgabe \(o=(1;\,0{,}5)\) erzeugen.<br>
(a) Liegt \(o\) in der konvexen Hülle der Values? Bestimmen Sie die Gewichte \(w=(w_A,w_B,w_C)\).<br>
(b) Bestimmen Sie Scores mit \(s_C=0\), die bei \(T=1\) genau diese Gewichte liefern. Geben Sie \(s_A\) an.<br>
(c) Welche Query \(q=(q_1,q_2)\) erzeugt diese Scores? Geben Sie \(q_1\) an.<br>
(d) Mit derselben Query, aber \(T=0{,}5\): Welche erste Komponente hat die Ausgabe jetzt?<br>
(e) Welche Query liefert bei \(T=0{,}5\) wieder genau \(o=(1;\,0{,}5)\)? Geben Sie \(q_1\) an.''',
    answers=[dict(label=r'(b) \(s_A\)', type='num', check='ln:2', diagnoses=[dict(value='0.5', msg=r'Das ist \(w_A\), nicht der Score. Scores sind Logarithmen von Gewichtsverhältnissen: \(s_A-s_C=\ln(w_A/w_C)\).')]),
             dict(label=r'(c) \(q_1\)', type='num', check='sqrt2ln:2:1', diagnoses=[dict(value='0.6931', msg=r'Sie haben die Skalierung vergessen: \(s_A=q^\top k_A/\sqrt2\), also \(q_1=\sqrt2\,s_A\).')]),
             dict(label=r'(d) \(o_1\) bei \(T=0{,}5\)', type='num', check='mean:4/3', diagnoses=[dict(value='1', msg=r'Bei halber Temperatur verdoppeln sich alle Scores; die Gewichte ändern sich.')]),
             dict(label=r'(e) \(q_1\) bei \(T=0{,}5\)', type='num', check='sqrt2ln:2:1/2')],
    hints=[r'Schreiben Sie \(o=w_Av_A+w_Bv_B+w_Cv_C\) komponentenweise auf; \(w_C=1-w_A-w_B\).',
           r'Aus \(w_j=e^{s_j}/Z\) folgt \(s_j-s_l=\ln(w_j/w_l)\) – der Nenner kürzt sich.',
           r'Mit \(k_C=0\) ist \(s_C=0\) automatisch; \(s_A=q_1/\sqrt2\), \(s_B=q_2/\sqrt2\).',
           r'Satz 6.1 (b): \(\lambda q\) bei \(T\) wirkt wie \(q\) bei \(T/\lambda\).'],
    lab={'lab': 'attention', 'item': 'c-target', 'label': 'Labor, Challenge „Punktlandung“ (gleiche Idee, andere Zahlen)'},
    solution=r'(a) ja, \(w=(0{,}5;\,0{,}25;\,0{,}25)\); (b) \(s_A=\ln2\approx0{,}6931\), \(s_B=0\); (c) \(q=(\sqrt2\ln2;\,0)\), \(q_1\approx0{,}9803\); (d) \(o_1=4/3\approx1{,}3333\); (e) \(q_1=\ln2/\sqrt2\approx0{,}4901\).',
    worked=r'''<b>(a) Hülle und Gewichte.</b> Gesucht sind \(w_A,w_B,w_C\ge0\) mit Summe 1 und \(w_A(2,0)+w_B(0,2)+w_C(0,0)=(1;\,0{,}5)\). Komponentenweise: \(2w_A=1\), \(2w_B=0{,}5\), also \(w_A=0{,}5\), \(w_B=0{,}25\) und \(w_C=1-0{,}5-0{,}25=0{,}25\). Alle drei sind <em>echt positiv</em>; nach Satz 6.2 (b) ist \(o\) damit ein innerer Punkt und exakt erreichbar.<br>
<b>(b) Scores.</b> Aus \(w_j=e^{s_j}/Z\) folgt \(w_j/w_l=e^{s_j-s_l}\) (der gemeinsame Nenner \(Z\) kürzt sich), also \(s_j-s_l=\ln(w_j/w_l)\). Mit \(s_C=0\): \(s_A=\ln(0{,}5/0{,}25)=\ln2\approx0{,}6931\) und \(s_B=\ln(0{,}25/0{,}25)=0\). Probe: \(e^{s}=(2;\,1;\,1)\), Summe 4, Gewichte \((0{,}5;\,0{,}25;\,0{,}25)\). Die Scores sind nur bis auf eine gemeinsame Konstante bestimmt (Satz 6.1 a) – deshalb die Festlegung \(s_C=0\).<br>
<b>(c) Query.</b> \(s_j=q^\top k_j/\sqrt2\). Mit \(k_C=0\) ist \(s_C=0\) für jedes \(q\) – passend zur Festlegung. \(s_A=q_1/\sqrt2=\ln2\) ⇒ \(q_1=\sqrt2\ln2\approx0{,}9803\); \(s_B=q_2/\sqrt2=0\) ⇒ \(q_2=0\).<br>
<b>(d) Halbe Temperatur.</b> Alle \(s_j/T\) verdoppeln sich: \((2\ln2;\,0;\,0)\), also Zähler \(e^{2\ln2}=4\), 1, 1; Summe 6; Gewichte \((2/3;\,1/6;\,1/6)\). Ausgabe \(o=\tfrac23(2,0)+\tfrac16(0,2)=(4/3;\,1/3)\), also \(o_1=4/3\approx1{,}3333\). Die Ausgabe rückt zur Ecke \(v_A\): kleinere Temperatur schärft die Verteilung.<br>
<b>(e) Ausgleich über die Länge.</b> Nach Satz 6.1 (b) wirkt \(\lambda q\) bei \(T\) wie \(q\) bei \(T/\lambda\). Wir wollen bei \(T=0{,}5\) dieselben Gewichte wie bei \(T=1\), also \(\lambda=0{,}5\): \(q=(\ln2/\sqrt2;\,0)\), \(q_1\approx0{,}4901\).<br>
<b>Kontrolle und Grenze.</b> Ein Ziel wie \((2,0)\) (Ecke) wäre nur im Grenzwert erreichbar; \((2,2)\) (außerhalb) nie. Und bei Keys, deren Projektionen nicht frei wählbar sind (z. B. zwei gleiche Keys), wären manche Gewichtsverhältnisse unerreichbar – dann scheitert Schritt (c), nicht (b).''',
    rubric=['(a) Gewichte aus Komponentengleichungen, Positivität geprüft (2 P.)', '(b) Logarithmus der Gewichtsverhältnisse mit Begründung (2 P.)',
            '(c) Skalierung √2 berücksichtigt (1 P.)', '(d) Gewichte und Ausgabe bei T = 0,5 (2 P.)', '(e) Satz 6.1 b angewendet (1 P.)', 'Grenzbetrachtung (1 P.)'])

A19 = dict(id='A19', kc='attention', transfer=True,
           prompt=r'Values \(v_1=(4,0)\), \(v_2=(0,4)\), \(v_3=(0,0)\), Softmax mit \(T=1\). Gesucht sind Scores mit \(s_3=0\), sodass die Ausgabe genau \(o=(1,1)\) ist. Bestimmen Sie \(s_1\).',
           answers=[dict(label=r'\(s_1\)', type='num', check='ln:1/2')],
           solution=r'\(w=(0{,}25;\,0{,}25;\,0{,}5)\), \(s_1=s_2=\ln(0{,}25/0{,}5)=-\ln2\approx-0{,}6931\).',
           worked=r'Komponentenweise \(4w_1=1\), \(4w_2=1\) ⇒ \(w_1=w_2=0{,}25\), \(w_3=0{,}5\) (alle positiv: innerer Punkt, Satz 6.2 b). Aus \(w_j/w_3=e^{s_j-s_3}\) und \(s_3=0\): \(s_1=s_2=\ln(1/2)=-\ln2\approx-0{,}6931\). Negative Scores sind zulässig – die Softmax macht daraus trotzdem positive Gewichte. Probe: \(e^{s}=(0{,}5;\,0{,}5;\,1)\), Summe 2, Gewichte \((0{,}25;\,0{,}25;\,0{,}5)\).',
           rubric=['Gewichte aus o bestimmt (1 P.)', 'Logarithmus des Verhältnisses mit Vorzeichen (1 P.)'])

B19 = dict(id='B-19', kc='attention', transfer=True,
           prompt=r'Values \(v_1=(3,0)\), \(v_2=(0,3)\), \(v_3=(0,0)\), Softmax mit \(T=1\). Für welche Scores mit \(s_3=0\) ist die Ausgabe \(o=(2;\,0{,}5)\)? Bestimmen Sie \(s_1\).',
           answers=[dict(label=r'\(s_1\)', type='num', check='ln:4')],
           solution=r'\(w=(2/3;\,1/6;\,1/6)\), \(s_1=\ln4\approx1{,}3863\), \(s_2=0\).',
           worked=r'\(3w_1=2\), \(3w_2=0{,}5\) ⇒ \(w_1=2/3\), \(w_2=1/6\), \(w_3=1-2/3-1/6=1/6\). Alle positiv ⇒ erreichbar. \(s_1=\ln\frac{2/3}{1/6}=\ln4\approx1{,}3863\), \(s_2=\ln1=0\). Probe: \(e^{s}=(4;\,1;\,1)\), Summe 6, Gewichte \((2/3;\,1/6;\,1/6)\).',
           rubric=['Gewichte (1 P.)', 'Score über Logarithmus (1 P.)'])

# ---- Anki: Referenzsequenz (atomar, kein Beweis auf Karten; Grafik nur, wo sie beim Abruf hilft) ----
CARD_UPDATES = {
 'attention/formel': dict(
     prompt=r'Wie werden aus Scores \(s_1,\dots,s_N\) bei Temperatur \(T\) die Attention-Gewichte \(w_j\) berechnet?',
     answer=r'\(w_j=\dfrac{e^{s_j/T}}{\sum_{l}e^{s_l/T}}\) (Softmax); dann \(o=\sum_j w_jv_j\).',
     why=r'\(e^x\) macht jeden Score positiv und erhält die Reihenfolge; die Division normiert auf Summe 1. Gewichte hängen nur von Score-Differenzen ab.',
     example=r'Bank: \(s=(0{,}8485;\,-0{,}891;\,0{,}1909)\) → \(w=(0{,}5904;\,0{,}1037;\,0{,}3059)\).',
     source='Lehrbuch 6.3, Definition 6.2, Abb. 6.2; SLP3 §7.1.1, S. 180', diagram='att_pipeline.svg', prereq='Exponentialfunktion; Skalarprodukt (6.2)'),
 'attention/sharpening': dict(source='Lehrbuch 6.3, Abb. 6.3 (Temperatur); Satz 6.1 b'),
 'attention/skalierung': dict(source='Lehrbuch 6.8, Satz 3 mit Beweis; Abb. 6.6; Vaswani et al. 2017, §3.2.1'),
 'attention/convex': dict(prompt=r'Wo liegt die Attention-Ausgabe \(o=\sum_j w_jv_j\) relativ zu den Values \(v_j\)?', answer=r'In der konvexen Hülle der \(v_j\); innere Punkte exakt, Randpunkte nur im Grenzwert, äußere nie.',
     why=r'Softmax-Gewichte sind positiv und summieren zu 1: \(o\) ist eine Konvexkombination (Satz 6.2).',
     diagram='att_hull_bank.svg', source='Lehrbuch 6.5, Satz 6.2, Abb. 6.5'),
}
NEW_CARDS = [
 dict(key='attention/softmax-why-exp', kc='attention', type='concept',
      prompt=r'Warum normiert man Scores nicht einfach als \(s_j/\sum_l s_l\), sondern über \(e^{s_j}\)?',
      answer=r'Scores können negativ sein: Der einfache Quotient liefert negative oder riesige Gewichte. \(e^{s_j}\) ist positiv, ordnungserhaltend und macht nur Differenzen relevant.',
      why=r'Die vier Forderungen: positiv, Summe 1, Ordnung erhalten, Verschiebung egal – \(e^x\) erfüllt alle (Lehrbuch 6.3).',
      example=r'\(s=(1;\,-1;\,0{,}5)\): Quotient gibt \((2;\,-2;\,1)\).', mistake='Gewichte = normierte Scores.',
      source='Lehrbuch 6.3, Forderungen W1–W4', prereq='Exponentialfunktion'),
 dict(key='attention/simplex', kc='attention', type='case',
      prompt=r'Drei Wörter. Welche Gewichtsvektoren \((w_1,w_2,w_3)\) kann die Softmax überhaupt ausgeben?',
      answer=r'Genau die inneren Punkte des Simplex: alle \(w_j&gt;0\), Summe 1. Ecken wie \((1,0,0)\) nur im Grenzwert.',
      why=r'\(e^{s}&gt;0\) für jedes \(s\) – kein Gewicht wird 0. Temperatur bewegt den Punkt zwischen Ecke (\(T\to0\)) und Mitte (\(T\to\infty\)).',
      source='Lehrbuch 6.4, Abb. 6.4', diagram='att_simplex.svg', prereq='Softmax (6.3)', mistake=r'„Bei kleiner Temperatur ist die Ausgabe exakt one-hot.“'),
]
