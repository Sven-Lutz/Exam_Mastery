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
           prompt=r"""Drei Wörter mit Keys \(k_1=(1,0)\), \(k_2=(1,0)\), \(k_3=(0,1)\), Values \(v_1=(2,0)\), \(v_2=(0,2)\), \(v_3=(0,0)\); \(d_k=2\), \(T=1\).<br>
(a) Welche Aussage über die Gewichte gilt für <em>jede</em> Query \(q\)?<br>
(b) Kann die Ausgabe \(o=(1;\,0{,}5)\) erreicht werden? (Hinweis: Sie liegt im Inneren des Dreiecks der Values.)<br>
(c) Für welchen Wert von \(q_1-q_2\) ist \(o=(0{,}5;\,0{,}5)\)?""",
           answers=[dict(label='(a)', type='choice', options=[r'\(w_1=w_2\), weil \(q^\top k_1=q^\top k_2\)', r'\(w_3=0\)', r'\(w_1+w_2=w_3\)'], correct=0),
                    dict(label='(b)', type='choice', options=[r'Nein: Mit \(w_1=w_2\) liegt \(o=(2w_1,2w_1)\) immer auf der Diagonale.', r'Ja, nach Satz 6.2 (b), weil der Punkt im Inneren liegt.', r'Ja, aber nur für \(T\to0\).'], correct=0,
                         diagnoses=[dict(value='1', msg=r'Satz 6.2 (b) gilt für frei wählbare Scores. Hier sind die Scores an \(s=Kq/\sqrt2\) gebunden, und gleiche Keys erzwingen gleiche Scores.')]),
                    dict(label=r'(c) \(q_1-q_2\)', type='num', check='sqrt2ln:1/2:1')],
           solution=r'(a) \(w_1=w_2\); (b) nein; (c) \(q_1-q_2=-\sqrt2\ln2\approx-0{,}9803\).',
           worked=r"""<b>(a)</b> \(s_j=q^\top k_j/\sqrt2\). Wegen \(k_1=k_2\) ist \(s_1=s_2\) für jedes \(q\), und gleiche Scores geben gleiche Gewichte (gemeinsamer Nenner der Softmax): \(w_1=w_2=:a\), \(w_3=1-2a\).<br>
<b>(b)</b> Dann ist \(o=a(2,0)+a(0,2)+(1-2a)(0,0)=(2a,\,2a)\): Jede erreichbare Ausgabe liegt auf der Diagonale. \((1;\,0{,}5)\) liegt nicht darauf – <em>unerreichbar</em>, obwohl der Punkt im Inneren der Hülle liegt (für frei wählbare Scores wäre er mit \(w=(0{,}5;\,0{,}25;\,0{,}25)\) erreichbar, Satz 6.2 b). Grund: Die Scores liegen im Bild von \(K\) (plus Vielfache von \(\mathbf 1\)), und dieses Bild erzwingt \(s_1=s_2\).<br>
<b>(c)</b> \(o=(0{,}5;\,0{,}5)\) ⇒ \(2a=0{,}5\), \(a=0{,}25\), \(w_3=0{,}5\). Aus \(w_1/w_3=e^{s_1-s_3}\): \(s_1-s_3=\ln(0{,}25/0{,}5)=-\ln2\). Mit \(s_1=q_1/\sqrt2\), \(s_3=q_2/\sqrt2\): \(q_1-q_2=-\sqrt2\ln2\approx-0{,}9803\). Nur die Differenz ist bestimmt (Satz 6.1 a).<br>
<b>Erreichbare Menge insgesamt:</b> \(a=e^{s_1}/(2e^{s_1}+e^{s_3})\) nimmt jeden Wert in \((0;\,\tfrac12)\) an, also ist genau die offene Strecke von \((0,0)\) bis \((1,1)\) erreichbar.""",
           rubric=['(a) gleiche Keys ⇒ gleiche Scores ⇒ gleiche Gewichte (2 P.)', '(b) Diagonale als erreichbare Menge, Abgrenzung zu Satz 6.2 b (3 P.)', '(c) Gewichte, Logarithmus, Skalierung (2 P.)', 'erreichbare Menge benannt (1 P.)'])

B19 = dict(id='B-19', kc='attention', transfer=True, data={'attn': {'q': [1, 0], 'K': [[1, 0], [0, 0]], 'V': [[2, 0], [0, 2]], 'T': 1, 'scale': True}},
           prompt=r"""Kausale Self-Attention (jedes Wort sieht nur sich und frühere Wörter), zwei Wörter in der Reihenfolge A, B. Keys \(k_A=(1,0)\), \(k_B=(0,0)\); Values \(v_A=(2,0)\), \(v_B=(0,2)\); Queries \(q_A=(0,1)\), \(q_B=(1,0)\); \(d_k=2\), \(T=1\).<br>
(a) Welche Ausgabe hat A – und hängt sie von \(q_A\) ab?<br>
(b) Welches Gewicht \(w_{B\to A}\) gibt B dem Wort A?<br>
(c) Jetzt wird die Reihenfolge vertauscht (B, A), alle Vektoren bleiben gleich. Was passiert mit der Ausgabe von B, und was zeigt das?""",
           answers=[dict(label='(a)', type='choice', options=[r'\(o_A=v_A=(2,0)\), unabhängig von \(q_A\)', r'\(o_A=(1,1)\)', r'\(o_A\) hängt von \(q_A\) ab'], correct=0),
                    dict(label=r'(b) \(w_{B\to A}\)', type='num', check='attnq:1,0|1,0;0,0:0'),
                    dict(label='(c)', type='choice', options=[r'\(o_B=v_B=(0,2)\) statt vorher \(\approx(1{,}3395;\,0{,}6605)\): Mit Maske gilt Satz 4 nicht – die Reihenfolge ändert die Ausgabe desselben Wortes.', r'\(o_B\) bleibt gleich (Satz 4).', r'Nur die Zeilen der Ausgabe werden vertauscht.'], correct=0,
                         diagnoses=[dict(value='1', msg='Satz 4 setzt voraus, dass jede Zeile über alle Positionen normiert. Die kausale Maske hängt von der Position ab.')])],
           solution=r'(a) \(o_A=(2,0)\), unabhängig von \(q_A\); (b) \(w_{B\to A}\approx0{,}6698\); (c) \(o_B\) ändert sich zu \((0,2)\) – Gegenbeispiel zu Satz 4 unter Maske.',
           worked=r"""<b>(a)</b> A steht vorn und sieht nur sich selbst: Die Softmax über <em>einen</em> Score ist 1, also \(o_A=v_A=(2,0)\) für jede Query – \(q_A\) ist wirkungslos.<br>
<b>(b)</b> B sieht A und sich: \(s_A=q_B^\top k_A/\sqrt2=1/\sqrt2\approx0{,}7071\), \(s_B=q_B^\top k_B/\sqrt2=0\). \(w_{B\to A}=e^{0{,}7071}/(e^{0{,}7071}+1)=2{,}0281/3{,}0281\approx0{,}6698\), also \(o_B=0{,}6698\,(2,0)+0{,}3302\,(0,2)\approx(1{,}3395;\,0{,}6605)\).<br>
<b>(c)</b> Bei Reihenfolge (B, A) steht B vorn und sieht nur sich: \(o_B=v_B=(0,2)\). Dasselbe Wort mit denselben Vektoren erhält eine andere Ausgabe. Satz 4 (\(\operatorname{Att}(PX)=P\operatorname{Att}(X)\)) gilt also nicht mehr: Sein Beweis benutzt, dass \(\operatorname{softmax}(PSP^\top)=P\operatorname{softmax}(S)P^\top\) – mit Maske hängt die Menge der zugelassenen Spalten aber von der Position ab. Die Maske allein macht Reihenfolge sichtbar, ganz ohne Positionsvektoren.""",
           rubric=['(a) eine sichtbare Position ⇒ Gewicht 1 (2 P.)', '(b) Scores mit Skalierung, Softmax (2 P.)', '(c) neue Ausgabe berechnet (1 P.)', '(c) Begründung, welche Voraussetzung von Satz 4 verletzt ist (3 P.)'])

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
      why=r'\(e^{s}&gt;0\) – kein Gewicht wird 0. Für \(T\to\infty\): Mitte. Für \(T\to0\): Ecke nur bei eindeutigem Maximum; bei Gleichstand der Mittelpunkt der Kante bzw. Fläche der Maxima; sind alle Scores gleich, bleibt w für jedes T in der Mitte.',
      source='Lehrbuch 6.4, Abb. 6.4', diagram='att_simplex.svg', prereq='Softmax (6.3)', mistake=r'„Bei kleiner Temperatur ist die Ausgabe exakt one-hot.“'),
]
