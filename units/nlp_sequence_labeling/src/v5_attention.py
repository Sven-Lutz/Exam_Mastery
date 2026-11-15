"""v5 (Issue #8): Self-Attention-Mikrosequenz – Lab-Experiment → Lehrbuch → Aufgabe → ausführliche Lösung → Anki.

Alle Dezimalzahlen stammen aus BANK (Startzustand des Labors) bzw. den `attn`-Daten der Aufgaben und werden von
reference_unit.verify über attn_full nachgerechnet.
"""
BANK = {'q': [0.9, -0.6], 'K': [[1.6, 0.4], [-0.4, 1.5], [0.1, -0.3]], 'V': [[1.8, 0.2], [0.1, 1.9], [0.2, 0.2]], 'T': 1, 'scale': True, 'lambdas': [2, 3]}
AT8 = {'q': [1, 1], 'K': [[2, 0], [0, 1]], 'V': [[1, 0], [0, 1]], 'T': 1, 'scale': True}

LAB = {  # KC -> Experimente im Labor (Stationen/Challenges); Labor verlinkt zurück ins Lehrbuch
    'attention': {'lab': 'attention', 'items': [['a1', 'Station 1: Wonach sucht „Bank“?'], ['a2', 'Station 2: Länge ist Schärfe'], ['a3', 'Station 3: Nur Unterschiede zählen'],
                  ['a4', 'Station 4: Gleichgültigkeit erzeugen'], ['a5', 'Station 5: Was die Ausgabe nie kann'], ['a6', 'Station 6: Warum durch √d_k teilen?'], ['c-impossible', 'Challenge: Unerreichbar?']]},
    'position': {'lab': 'attention', 'items': [['a7', 'Station 7: Self-Attention sieht keine Reihenfolge'], ['c-order', 'Challenge: Gegenbeispiel bauen']]},
    'decoding': {'lab': 'crf', 'items': [['r1', 'Station 1: Jedes Wort für sich'], ['r2', 'Station 2: Verbotene Übergänge'], ['r4', 'Station 4: Summe statt Maximum'], ['k-mm', 'Challenge: Die Randverteilungs-Falle']]},
    'birnn': {'lab': 'birnn', 'items': [['b1', 'Station 1: Vorwärts sieht nur die Vergangenheit'], ['b2', 'Station 2: Rückwärts bringt die Zukunft'], ['n-sat', 'Challenge: Gesättigt']]},
    'spans': {'lab': 'spans', 'items': [['s5', 'Station 5: IO verliert Grenzen']]},
    'prf': {'lab': 'spans', 'items': [['s1', 'Station 1: Fast richtig ist falsch'], ['f-prec', 'Challenge: Präzise, aber blind']]},
    'prf-edge': {'lab': 'spans', 'items': [['s3', 'Station 3: Wenn nichts da ist']]},
    'prf-level': {'lab': 'spans', 'items': [['s2', 'Station 2: Token-Zählung ist großzügiger'], ['f-half', 'Challenge: Halbe Treffer']]},
    'micro-macro': {'lab': 'spans', 'items': [['s4', 'Station 4: Micro gegen Macro'], ['f-macro', 'Challenge: Seltenes zählt']]},
}

TEXT = r'''
<h3 id="attention-geometrie">Geometrie der Attention: ein Wort sucht seinen Kontext</h3>
<p><span class="layer" data-layer="core">Klausurkern</span></p>
<p><b>Problem.</b> Im Satz „Wir sitzen auf der <b>Bank</b> am <b>Fluss</b>“ muss der Vektor von „Bank“ zur Ufer-Bedeutung verschoben werden, im Satz „Ich hebe Geld von der Bank ab“ zur Finanz-Bedeutung. Dieselbe Rechenvorschrift muss beides leisten – nur aus dem Kontext. Wir verfolgen die Rechnung in zwei Dimensionen, in denen jede Zwischengröße sichtbar ist; im Labor ist genau dieser Zustand der Startpunkt.</p>
<div class="lab-ref" data-kc="attention"></div>
<p><b>Notation und Dimensionen.</b> Eine Query \(q\in\mathbb R^{d_k}\) (das suchende Wort), Keys \(k_1,\dots,k_N\in\mathbb R^{d_k}\), Values \(v_1,\dots,v_N\in\mathbb R^{d_v}\), Temperatur \(T&gt;0\) (Standard \(T=1\)). Scores, Gewichte und Ausgabe:</p>
\[s_j=\frac{q^\top k_j}{\sqrt{d_k}},\qquad w_j=\frac{e^{s_j/T}}{\sum_{l=1}^Ne^{s_l/T}},\qquad o=\sum_{j=1}^Nw_jv_j\in\mathbb R^{d_v}.\]
<p>Geometrisch ist \(q^\top k_j=\lVert q\rVert\,\lVert k_j\rVert\cos\theta_j=\lVert q\rVert\cdot\pi_j\) mit der vorzeichenbehafteten Projektionslänge \(\pi_j\) von \(k_j\) auf die Richtung von \(q\): <em>Wer weit in Richtung der Query ragt, bekommt Gewicht.</em></p>
<p><b>Durchgerechnetes Beispiel.</b> \(q=(0{,}9;\,-0{,}6)\); Keys Fluss \((1{,}6;\,0{,}4)\), Geld \((-0{,}4;\,1{,}5)\), der \((0{,}1;\,-0{,}3)\); Values (Achsen: Ufer-, Finanz-Bedeutung) Fluss \((1{,}8;\,0{,}2)\), Geld \((0{,}1;\,1{,}9)\), der \((0{,}2;\,0{,}2)\); \(d_k=2\).</p>
\[\begin{aligned}
q^\top k&amp;=\big(0{,}9\cdot1{,}6+(-0{,}6)\cdot0{,}4;\ \ 0{,}9\cdot(-0{,}4)+(-0{,}6)\cdot1{,}5;\ \ 0{,}9\cdot0{,}1+(-0{,}6)(-0{,}3)\big)=(1{,}2;\ -1{,}26;\ 0{,}27) &amp;&amp;\text{(Fluss; Geld; der)}\\
s&amp;=(0{,}8485;\ -0{,}891;\ 0{,}1909) &amp;&amp;\text{(Division durch }\sqrt2)\\
e^{s}&amp;=(2{,}3362;\ 0{,}4103;\ 1{,}2104),\ \textstyle\sum=3{,}9568 &amp;&amp;\\
w&amp;=(0{,}5904;\ 0{,}1037;\ 0{,}3059) &amp;&amp;\text{(Summe 1)}\\
o&amp;=0{,}5904\,v_{\text{Fluss}}+0{,}1037\,v_{\text{Geld}}+0{,}3059\,v_{\text{der}}=(1{,}1343;\ 0{,}3763)
\end{aligned}\]
<p>Die Ausgabe liegt deutlich auf der Ufer-Achse. Entropie der Gewichte: \(H=1{,}3106\) Bit von höchstens \(\log_23=1{,}585\) Bit – die Aufmerksamkeit ist verteilt, nicht scharf.</p>
<div class="thm"><b>Satz 6.1 (Verschiebung und Länge).</b> (a) Für jedes \(c\in\mathbb R\) gilt \(\operatorname{softmax}(s+c\mathbf 1)=\operatorname{softmax}(s)\). Insbesondere ändert die gemeinsame Verschiebung aller Keys um denselben Vektor \(u\) keine Gewichte. (b) Für \(\lambda&gt;0\) liefert die Query \(\lambda q\) bei Temperatur \(T\) dieselben Gewichte wie \(q\) bei Temperatur \(T/\lambda\).</div>
<div class="proof">\[\begin{aligned}
\frac{e^{(s_j+c)/T}}{\sum_le^{(s_l+c)/T}}&amp;=\frac{e^{c/T}\,e^{s_j/T}}{e^{c/T}\sum_le^{s_l/T}}=\frac{e^{s_j/T}}{\sum_le^{s_l/T}} &amp;&amp;\text{(a): Faktor kürzt sich}\\
\frac{q^\top(k_j+u)}{\sqrt{d_k}}&amp;=s_j+\frac{q^\top u}{\sqrt{d_k}} &amp;&amp;\text{gleiches }c\text{ für alle }j\\
\frac{(\lambda q)^\top k_j}{\sqrt{d_k}\,T}&amp;=\frac{s_j}{T/\lambda} &amp;&amp;\text{(b)}\quad\square
\end{aligned}\]</div>
<p><b>Rechenbeispiel zu (b).</b> Verdoppelt bzw. verdreifacht man \(q\) im Bank-Beispiel, werden die Gewichte \((0{,}7697;\,0{,}0237;\,0{,}2066)\) bzw. \((0{,}8738;\,0{,}0047;\,0{,}1215)\); die Entropie fällt von \(1{,}3106\) auf \(0{,}8888\) bzw. \(0{,}5762\) Bit. Ein Netz steuert die Schärfe seiner Auswahl also schon über die Länge der Query. <b>Gegenbeispiel zu (a):</b> Verschiebt man nur <em>einen</em> Key, ändert sich nur ein Score – die Gewichte ändern sich. <b>Praxis:</b> (a) ist der Grund, warum Implementierungen vor dem Exponenzieren \(\max_ls_l\) abziehen (keine Überläufe, identisches Ergebnis).</p>
<div class="thm"><b>Satz 6.2 (Konvexe Hülle).</b> Die Ausgabe \(o\) liegt in der konvexen Hülle \(\operatorname{conv}\{v_1,\dots,v_N\}\). Jeder Punkt im <em>Inneren</em> der Hülle ist für geeignete Scores exakt erreichbar; Punkte außerhalb nie.</div>
<div class="proof">Aus \(w_j=e^{s_j/T}/\sum_le^{s_l/T}&gt;0\) und \(\sum_jw_j=1\) ist \(o\) eine Konvexkombination – das ist die Definition der konvexen Hülle. Umgekehrt: Für einen inneren Punkt \(z=\sum_j\mu_jv_j\) mit allen \(\mu_j&gt;0\), \(\sum_j\mu_j=1\) wähle \(s_j=T\ln\mu_j\); dann ist \(w_j=\mu_j\). Randpunkte brauchen \(\mu_j=0\), also \(s_j\to-\infty\): nur im Grenzwert. \(\square\)</div>
<p>Konsequenz: Self-Attention allein kann Information nur <em>mischen</em>, nicht verstärken oder umkehren. Darum folgen im Transformer eine lineare Abbildung \(W_O\) und eine Residualverbindung (Abschnitt 8). Ob ein Score-Vektor \(s\) mit diesen Werten auch durch eine Query \(q\) realisierbar ist, hängt zusätzlich von den Keys ab – im Labor (Challenge „Punktlandung“) sieht man, dass dafür Richtung <em>und</em> Länge von \(q\) gebraucht werden.</p>
<div class="thm"><b>Satz 6.3 (Gleichverteilung).</b> \(w_1=\dots=w_N=1/N\) genau dann, wenn \(q^\top(k_i-k_j)=0\) für alle \(i,j\) – also wenn \(q\) auf allen Differenzen der Keys senkrecht steht.</div>
<div class="proof">Gleiche Gewichte \(\Leftrightarrow\) \(e^{s_i/T}=e^{s_j/T}\) \(\Leftrightarrow\) \(s_i=s_j\) (exp ist injektiv) \(\Leftrightarrow\) \(q^\top k_i=q^\top k_j\) \(\Leftrightarrow\) \(q^\top(k_i-k_j)=0\). \(\square\)</div>
<p><b>Grenzfälle.</b> \(q=0\) erfüllt Satz 6.3 trivial. Mit \(q\ne0\) geht es in \(\mathbb R^2\) nur, wenn alle Keys auf einer Geraden senkrecht zu \(q\) liegen; in \(\mathbb R^{d_k}\) mit \(d_k\ge N\) dagegen fast immer (die \(N-1\) Differenzen spannen höchstens einen \((N-1)\)-dimensionalen Raum auf). \(T\to0\): Gewicht gleichmäßig auf alle Maxima (bei Gleichstand nicht one-hot!). \(T\to\infty\): Gleichverteilung. Alle Positionen maskiert: Softmax undefiniert.</p>
<p><span class="layer" data-layer="deep">Vertiefung</span> <b>Warum Sättigung das Lernen bremst.</b></p>
<div class="thm"><b>Lemma 6.4 (Jacobi-Matrix der Softmax mit Temperatur).</b> Für \(w=\operatorname{softmax}(s/T)\) gilt \(\dfrac{\partial w_i}{\partial s_j}=\dfrac{1}{T}\big(w_i[i=j]-w_iw_j\big)\), also \(J=\frac1T\big(\operatorname{diag}(w)-ww^\top\big)\). Sei \(m\) ein Index mit maximalem Score und \(\Delta=s_m-\max_{j\ne m}s_j\) der Vorsprung. Dann gilt
\[\lVert J\rVert_F\;\le\;\frac{4\,(1-w_m)}{T}\;\le\;\frac{4\,(N-1)\,e^{-\Delta/T}}{T}.\]
(a) Bei <b>fester</b> Temperatur \(T&gt;0\) und \(\Delta\to\infty\) folgt \(J\to0\) (Sättigung). (b) Für \(T\to0\) bei <b>eindeutigem</b> Maximum (\(\Delta&gt;0\) fest) folgt ebenfalls \(J\to0\), weil \(e^{-\Delta/T}/T\to0\). (c) Für \(T\to0\) bei \(k\ge2\) <b>gleich großen</b> Maxima gilt \(w\to\) Gleichverteilung auf diesen \(k\) Indizes und \(J_{mm}\to\infty\): Die Jacobi-Matrix divergiert.</div>
<div class="proof">\[\begin{aligned}
\frac{\partial w_i}{\partial s_j}&amp;=\frac{\tfrac1T e^{s_i/T}[i=j]\,Z-e^{s_i/T}\,\tfrac1Te^{s_j/T}}{Z^2}=\tfrac1T\big(w_i[i=j]-w_iw_j\big) &amp;&amp;\text{Quotientenregel},\ Z=\textstyle\sum_le^{s_l/T}\\
\lVert J\rVert_F\le\textstyle\sum_{i,j}|J_{ij}|&amp;=\tfrac1T\Big(\textstyle\sum_iw_i(1-w_i)+\sum_{i\ne j}w_iw_j\Big)=\tfrac2T\textstyle\sum_iw_i(1-w_i) &amp;&amp;\textstyle\sum_{j\ne i}w_j=1-w_i\\
\textstyle\sum_iw_i(1-w_i)&amp;\le(1-w_m)+\textstyle\sum_{i\ne m}w_i=2(1-w_m) &amp;&amp;w_m\le1,\ 1-w_i\le1\\
1-w_m=\frac{\sum_{j\ne m}e^{(s_j-s_m)/T}}{\sum_le^{(s_l-s_m)/T}}&amp;\le(N-1)\,e^{-\Delta/T} &amp;&amp;\text{Nenner}\ge1\\
\text{(c)}:\ w_i\to\tfrac1k\ (i\text{ unter den Maxima}),\quad J_{ii}&amp;=\tfrac1Tw_i(1-w_i)\to\tfrac1T\cdot\tfrac1k\big(1-\tfrac1k\big)\to\infty &amp;&amp;\square
\end{aligned}\]</div>
<p><b>Lehre aus (c).</b> „Kleine Temperatur macht Gradienten klein“ ist <em>falsch</em> formuliert. Klein werden sie nur, wenn ein Score eindeutig vorn liegt. Bei Gleichstand wird die Softmax für \(T\to0\) zum unstetigen \(\arg\max\), und an dieser Stelle explodiert die Ableitung. Im Labor: Preset „Zwei gleich gute Schlüssel“ und \(T\) verkleinern; \(\lVert J\rVert\) steigt.</p>
<p>Im Bank-Beispiel ist \(\lVert J\rVert_F=0{,}4324\) (bezogen auf \(s\)). Satz 3 sagt, dass ohne Skalierung die Scores mit Standardabweichung \(\sqrt{d_k}\) streuen; dann ist \(w\) fast immer nahezu one-hot, und nach Lemma 6.4 kommt kaum Gradient bei den Scores an. Das Labor misst das reproduzierbar (Ansicht „Skalierung“). Das ist die präzise Fassung des Arguments „die Softmax gerät in Bereiche mit sehr kleinen Gradienten“ der Originalarbeit.</p>
<aside class="research"><h4>Forschungsfenster: Sind Attention-Gewichte Erklärungen?</h4><p><b>Frage.</b> Darf man aus großen Gewichten \(w_j\) schließen, dass Wort \(j\) die Entscheidung verursacht hat?</p><p><b>Methode und Befund.</b> Jain &amp; Wallace (2019) vergleichen Attention-Gewichte mit gradientenbasierten Wichtigkeitsmaßen und konstruieren stark abweichende („adversariale“) Gewichtsverteilungen, die dennoch dieselbe Vorhersage liefern; sie folgern, dass Standard-Attention keine verlässlichen Erklärungen liefert. Wiegreffe &amp; Pinter (2019) halten dagegen: Ob Attention erklärt, hängt von der Definition von „Erklärung“ ab; ihre Diagnosen zeigen, dass die gefundenen adversarialen Verteilungen in einem einfachen Test schlecht abschneiden – die frühere Arbeit widerlege die Nützlichkeit nicht.</p><p><b>Grenzen dieser Darstellung.</b> Gelesen wurden die Zusammenfassungen beider Arbeiten (ACL Anthology), nicht die Experimente im Detail; Zahlen werden daher nicht wiedergegeben. Beide Arbeiten untersuchen Klassifikationsmodelle mit RNN-Encodern, nicht Transformer-NER.</p><p><b>Bedeutung für dieses Kapitel.</b> Satz 6.1 und 6.2 zeigen mathematisch, warum Vorsicht geboten ist: Viele verschiedene Gewichtsvektoren ergeben dieselbe Ausgabe, sobald Values zusammenfallen oder kollinear sind, und die Gewichte sagen nichts über \(W_O\) und die Residualverbindung. Prüfungstauglich: „Attention-Gewichte zeigen, <em>wie gemischt</em> wird, nicht zwingend, <em>was entscheidet</em>.“</p><p class="mute small">Belegstellen: <a class="cite" href="#ref-jain">Jain &amp; Wallace 2019</a>; <a class="cite" href="#ref-wiegreffe">Wiegreffe &amp; Pinter 2019</a></p></aside>
<aside class="media"><h4>Zum Anschauen (optional, Vertiefung)</h4><p><a href="https://www.youtube.com/watch?v=eMlx5fFNoYc">3Blue1Brown: „Attention in transformers, step-by-step“ (Deep Learning, Kapitel 6, 7. April 2024)</a>, Begleitseite <a href="https://www.3blue1brown.com/lessons/attention">3blue1brown.com/lessons/attention</a>. <b>Rolle:</b> visuelle Intuition für Query, Key und Value in hohen Dimensionen vor bzw. nach dem Labor. <b>Hinweis:</b> Das Video verwendet eine andere Notation (Spaltenvektoren, Beispiele aus der Textgenerierung mit kausaler Maske); für die Klausur gilt die Notation dieses Lehrbuchs. Inhalt hier nicht im Detail ausgewertet, daher keine Zeitmarken.</p></aside>
<div class="task-ref" data-task="AT5"></div>
'''

TASKS = [
 dict(id='AT5', stage='worked', kc='attention', title='Durchgerechnet: „Bank“ am Fluss',
      prompt=r'Query \(q=(0{,}9;\,-0{,}6)\), Keys \(k_{\text{Fluss}}=(1{,}6;\,0{,}4)\), \(k_{\text{Geld}}=(-0{,}4;\,1{,}5)\), \(k_{\text{der}}=(0{,}1;\,-0{,}3)\), Values \(v_{\text{Fluss}}=(1{,}8;\,0{,}2)\), \(v_{\text{Geld}}=(0{,}1;\,1{,}9)\), \(v_{\text{der}}=(0{,}2;\,0{,}2)\), \(d_k=2\), \(T=1\). Berechnen Sie Gewichte und Ausgabe.',
      data={'attn': BANK},
      steps=[dict(s=r'Skalarprodukte \(1{,}2;\ -1{,}26;\ 0{,}27\)', why=r'Komponentenweise: \(0{,}9\cdot1{,}6+(-0{,}6)\cdot0{,}4=1{,}2\) usw.'),
             dict(s=r'Scores \(s=(0{,}8485;\ -0{,}891;\ 0{,}1909)\)', why=r'Division durch \(\sqrt{d_k}=\sqrt2\).'),
             dict(s=r'\(e^{s}=(2{,}3362;\ 0{,}4103;\ 1{,}2104)\), Summe \(3{,}9568\)', why='Exponentieren; die Summe ist der Normierer.'),
             dict(s=r'\(w=(0{,}5904;\ 0{,}1037;\ 0{,}3059)\)', why='Jeden Exponentialwert durch die Summe teilen; Probe: Summe 1.'),
             dict(s=r'\(o=(1{,}1343;\ 0{,}3763)\)', why=r'\(o=\sum_jw_jv_j\), komponentenweise.')],
      answers=[dict(label=r'Selbsterklärung: Warum bekommt „der“ mehr Gewicht als „Geld“, obwohl \(k_{\text{Geld}}\) viel länger ist?', type='choice',
                    options=[r'Es zählt die Projektion auf \(q\): \(k_{\text{Geld}}\) zeigt von \(q\) weg (negatives Skalarprodukt), \(k_{\text{der}}\) leicht in Richtung \(q\).', r'Kurze Keys werden von der Softmax bevorzugt.', r'Weil \(v_{\text{der}}\) klein ist.'], correct=0)],
      lab={'lab': 'attention', 'item': 'a1', 'label': 'Labor, Station 1 (gleicher Startzustand)'},
      solution=r'\(w=(0{,}5904;\ 0{,}1037;\ 0{,}3059)\), \(o=(1{,}1343;\ 0{,}3763)\).',
      worked=r'Skalarprodukte \(1{,}2\), \(-1{,}26\), \(0{,}27\); nach Division durch \(\sqrt2\): \(0{,}8485\), \(-0{,}891\), \(0{,}1909\). Exponentialwerte \(2{,}3362\), \(0{,}4103\), \(1{,}2104\), Summe \(3{,}9568\). Gewichte \(0{,}5904\), \(0{,}1037\), \(0{,}3059\). Ausgabe \(o=(1{,}1343;\ 0{,}3763)\) – nahe der Ufer-Achse. <b>Geometrie:</b> \(q^\top k_j=\lVert q\rVert\pi_j\); \(k_{\text{Geld}}\) hat trotz großer Länge eine negative Projektion. <b>Kontrolle:</b> \(o\) liegt im Dreieck der Values (Satz 6.2).',
      rubric=['Skalarprodukte (1 P.)', 'Skalierung (1 P.)', 'Softmax mit Probe (1 P.)', 'gewichtete Summe (1 P.)', 'Deutung über Projektion (1 P.)']),
 dict(id='AT6', stage='proof', kc='attention', title='Beweis: Verschiebung und Länge',
      prompt=r'Beweisen Sie Satz 6.1: (a) Eine gemeinsame Verschiebung aller Keys um \(u\) ändert die Gewichte nicht. (b) \(\lambda q\) bei Temperatur \(T\) wirkt wie \(q\) bei \(T/\lambda\). Welcher Rechenschritt trägt (a)?',
      answers=[dict(label='Tragender Schritt in (a)', type='choice', options=[r'\(e^{(s_j+c)/T}=e^{c/T}e^{s_j/T}\) – der Faktor \(e^{c/T}\) kürzt sich zwischen Zähler und Nenner', r'Die Softmax ist monoton', r'\(q^\top u=0\) für jede Verschiebung'], correct=0,
                    diagnoses=[dict(value='2', msg=r'Falsch: \(q^\top u\) ist im Allgemeinen nicht 0 – die Scores ändern sich ja (im Labor sichtbar). Entscheidend ist, dass sich alle um <em>denselben</em> Betrag ändern.')])],
      hints=[r'Schreiben Sie den neuen Score als \(s_j+c\) mit \(c=q^\top u/\sqrt{d_k}\).', r'Für (b): Ziehen Sie \(\lambda\) aus dem Skalarprodukt.'],
      lab={'lab': 'attention', 'item': 'a3', 'label': 'Labor, Station 3 und 2'},
      solution=r'(a) Score \(s_j+c\) mit gleichem \(c=q^\top u/\sqrt{d_k}\); \(e^{c/T}\) kürzt sich. (b) \((\lambda q)^\top k_j/(\sqrt{d_k}T)=s_j/(T/\lambda)\).',
      worked=r'<b>(a)</b> Neue Keys \(k_j+u\). Score: \(q^\top(k_j+u)/\sqrt{d_k}=s_j+c\) mit \(c=q^\top u/\sqrt{d_k}\), <em>unabhängig von</em> \(j\). Softmax: \(e^{(s_j+c)/T}/\sum_le^{(s_l+c)/T}=e^{c/T}e^{s_j/T}/(e^{c/T}\sum_le^{s_l/T})=w_j\). <b>(b)</b> \((\lambda q)^\top k_j/(\sqrt{d_k}\,T)=\lambda s_j/T=s_j/(T/\lambda)\): exakt die Gewichte bei Temperatur \(T/\lambda\). <b>Gegenbeispiel</b> (Grenze der Aussage): Verschiebt man nur \(k_1\), ändert sich nur \(s_1\), und \(w_1\) steigt oder fällt mit \(q^\top u\). \(\square\)',
      rubric=['c unabhängig von j erkannt (2 P.)', 'Kürzen korrekt (1 P.)', '(b) mit Temperatur (1 P.)', 'Gegenbeispiel (1 P.)']),
 dict(id='AT7', stage='transfer', kc='attention', title='Transfer: Was Attention nicht kann',
      prompt=r'Values \(v_1=(1,0)\), \(v_2=(0,1)\), \(v_3=(0,0)\). Ein Kollege möchte mit einer einzigen Attention-Schicht (ohne \(W_O\), ohne Residualverbindung) die Ausgabe \(o=(1,1)\) erzeugen und sucht dafür Query und Temperatur. Was ist richtig?',
      answers=[dict(label='Aussage', type='choice', options=[r'Unmöglich: \(o\) liegt im Dreieck \(\operatorname{conv}\{v_1,v_2,v_3\}\), dort gilt \(o_1+o_2\le1\).', r'Möglich mit \(T\to0\) und \(q\) zwischen \(k_1\) und \(k_2\).', r'Möglich, wenn die Keys lang genug sind.'], correct=0,
                    diagnoses=[dict(value='1', msg=r'\(T\to0\) konzentriert das Gewicht auf das Maximum (bei Gleichstand gleichmäßig auf die Maxima) – \(o\) wird dann \(v_1\), \(v_2\) oder \((0{,}5;\,0{,}5)\), nie \((1,1)\).'), dict(value='2', msg='Keys ändern nur die Gewichte, nicht deren Eigenschaften \\(w_j\\ge0,\\ \\sum w_j=1\\).')])],
      hints=[r'Welche Werte kann \(w_1+w_2\) höchstens annehmen?'],
      lab={'lab': 'attention', 'item': 'c-impossible', 'label': 'Labor, Challenge „Unerreichbar?“'},
      solution=r'Unmöglich (Satz 6.2): \(o_1+o_2=w_1+w_2\le1\).',
      worked=r'Für jede Wahl von \(q\), Keys und \(T\) ist \(o=w_1(1,0)+w_2(0,1)+w_3(0,0)=(w_1,w_2)\) mit \(w_j&gt;0\) und \(w_1+w_2+w_3=1\). Also \(o_1+o_2=1-w_3&lt;1\). \((1,1)\) hat Koordinatensumme 2 – unerreichbar. Erreichbar wären nur Punkte im Inneren des Dreiecks (Satz 6.2), Randpunkte nur im Grenzwert. <b>Abhilfe in echten Modellen:</b> \(W_O\) (lineare Abbildung kann skalieren) und die Residualverbindung \(x+\operatorname{Att}(x)\).',
      rubric=['Konvexkombination (2 P.)', 'konkrete Ungleichung (1 P.)', 'Abhilfe W_O/Residual (1 P.)']),
 dict(id='AT8', stage='independent', kc='attention', title='Sättigung und Gradient',
      prompt=r'\(q=(1,1)\), Keys \(k_1=(2,0)\), \(k_2=(0,1)\), \(d_k=2\), \(T=1\). Berechnen Sie \(w_1\) und die Ableitung \(\partial w_1/\partial s_1=w_1(1-w_1)\) (Lemma 6.4). Wie ändert sich diese Ableitung, wenn man die Skalierung weglässt – größer oder kleiner?',
      data={'attn': AT8},
      answers=[dict(label=r'\(w_1\)', type='num', check='attnd:AT8:w:0', diagnoses=[dict(value='0.7311', msg=r'Sie haben nicht durch \(\sqrt2\) geteilt (Scores 2 und 1).')]),
               dict(label=r'\(\partial w_1/\partial s_1\)', type='num', check='attnd:AT8:jac:0', diagnoses=[dict(value='0.25', msg=r'Das wäre der Wert bei \(w_1=0{,}5\). Setzen Sie Ihr \(w_1\) ein.')]),
               dict(label='Ohne Skalierung wird die Ableitung …', type='choice', options=['kleiner', 'größer', 'gleich'], correct=0, diagnoses=[dict(value='1', msg=r'Ohne Skalierung wächst der Score-Abstand, \(w_1\) rückt näher an 1, und \(w_1(1-w_1)\) fällt.')])],
      hints=[r'Scores \(2/\sqrt2\) und \(1/\sqrt2\); nur der Abstand zählt (Satz 6.1).', r'\(w_1=1/(1+e^{-(s_1-s_2)})\).'],
      lab={'lab': 'attention', 'item': 'a6', 'label': 'Labor, Station 6 (Gradientenstärke ‖J‖)'},
      solution=r'\(w_1\approx0{,}6698\), \(\partial w_1/\partial s_1\approx0{,}2212\); ohne Skalierung kleiner.',
      worked=r'Skalarprodukte \(q^\top k_1=2\), \(q^\top k_2=1\); Scores \(1{,}4142\) und \(0{,}7071\), Abstand \(0{,}7071\). \(w_1=e^{1{,}4142}/(e^{1{,}4142}+e^{0{,}7071})=0{,}6698\). Ableitung \(w_1(1-w_1)=0{,}6698\cdot0{,}3302=0{,}2212\). Ohne Skalierung ist der Abstand \(1\): \(w_1\) wächst, \(w_1(1-w_1)\) sinkt. Allgemein ist \(w(1-w)\) bei \(w=0{,}5\) maximal (\(0{,}25\)) und geht gegen 0, wenn \(w\to1\): Sättigung bremst das Lernen (Lemma 6.4).',
      rubric=['Scores mit Skalierung (1 P.)', 'w₁ (1 P.)', 'Ableitung (1 P.)', 'Richtung mit Begründung (1 P.)']),
 dict(id='AT9', stage='error', kc='attention', title='Fehleranalyse: „Gleichverteilung nur bei q = 0“',
      prompt=r'Eine Kommilitonin behauptet: „Die Gewichte sind genau dann gleichverteilt, wenn \(q=0\).“ Welches Gegenbeispiel widerlegt das?',
      answers=[dict(label='Gegenbeispiel', type='choice', options=[r'\(q=(2,0)\), Keys \((1,1)\), \((1,-1)\), \((1;\,0{,}5)\): alle Skalarprodukte 2, also gleichverteilt bei \(q\ne0\).', r'\(q=(0,0)\) mit beliebigen Keys.', r'\(q=(1,0)\), Keys \((1,0)\), \((0,1)\).'], correct=0,
                    diagnoses=[dict(value='1', msg='Das bestätigt die Richtung „q = 0 ⇒ gleichverteilt“, widerlegt aber das „genau dann“ nicht.'), dict(value='2', msg='Skalarprodukte 1 und 0 – nicht gleichverteilt.')])],
      hints=[r'Satz 6.3: Es kommt auf \(q^\top(k_i-k_j)\) an.'],
      lab={'lab': 'attention', 'item': 'c-uniform', 'label': 'Labor, Challenge „Gleichgültig, aber nicht leer“'},
      solution=r'Gegenbeispiel (a); richtig ist Satz 6.3: \(q\perp(k_i-k_j)\) für alle Paare.',
      worked=r'Die Aussage verwechselt eine hinreichende mit einer notwendigen Bedingung. \(q=0\) reicht, ist aber nicht nötig: Bei \(q=(2,0)\) und Keys mit gleicher erster Komponente 1 sind alle Skalarprodukte \(2\) (die zweite Komponente wird mit 0 multipliziert), also alle Gewichte \(1/3\). Korrekt (Satz 6.3): gleichverteilt \(\Leftrightarrow\) \(q^\top(k_i-k_j)=0\) für alle \(i,j\). Geometrisch: alle Keys liegen in einer Hyperebene senkrecht zu \(q\).',
      rubric=['hinreichend vs. notwendig (1 P.)', 'Gegenbeispiel geprüft (1 P.)', 'korrekte Bedingung (1 P.)']),
]

CARDS = [
 dict(key='attention/shift-invariance', kc='attention', type='math', prompt=r'Alle Keys werden um denselben Vektor \(u\) verschoben: \(k_j\mapsto k_j+u\). Was passiert mit Scores und Gewichten?',
      answer=r'Jeder Score ändert sich um dasselbe \(c=q^\top u/\sqrt{d_k}\); die Gewichte bleiben gleich.', why=r'\(e^{(s_j+c)/T}\) enthält den Faktor \(e^{c/T}\), der sich in der Softmax kürzt (Satz 6.1a).',
      source='Lehrbuch §6, Satz 6.1; Labor Station 3', example=r'Bank-Beispiel: Scores ändern sich, \(w=(0{,}5904;\,0{,}1037;\,0{,}3059)\) bleibt.', mistake='Nur einen Key verschieben – dann ändern sich die Gewichte sehr wohl.', diagram='softmax_shift.svg', prereq='Softmax; Skalarprodukt'),
 dict(key='attention/length-temperature', kc='attention', type='concept', prompt=r'Die Query wird auf das Dreifache verlängert, ihre Richtung bleibt. Welche andere Stellschraube hat exakt dieselbe Wirkung?',
      answer=r'Die Temperatur auf \(T/3\) senken.', why=r'\((\lambda q)^\top k_j=\lambda\,q^\top k_j\): alle Scores werden mit \(\lambda\) multipliziert – wie Division durch \(T/\lambda\) (Satz 6.1b).',
      source='Lehrbuch §6, Satz 6.1; Labor Station 2', example=r'Bank: Entropie \(1{,}3106\to0{,}5762\) Bit bei \(\lambda=3\).', mistake='„Nur die Richtung von q zählt“ – die Länge bestimmt die Schärfe.', prereq='Temperatur der Softmax'),
 dict(key='attention/uniform-condition', kc='attention', type='concept', prompt=r'Unter welcher genauen Bedingung an \(q\) und die Keys sind alle Attention-Gewichte gleich?',
      answer=r'\(q^\top(k_i-k_j)=0\) für alle Paare \(i,j\): \(q\) steht senkrecht auf allen Key-Differenzen.', why='Gleiche Gewichte ⇔ gleiche Scores, weil exp injektiv ist (Satz 6.3).',
      source='Lehrbuch §6, Satz 6.3; Labor Station 4', example=r'\(q=(2,0)\), Keys \((1,1)\), \((1,-1)\), \((1;\,0{,}5)\): alle Gewichte \(1/3\).', mistake=r'„Nur bei \(q=0\)“ – das ist hinreichend, nicht notwendig.', prereq='Skalarprodukt, Orthogonalität'),
 dict(key='attention/jacobian', kc='attention', type='math', prompt=r'Wie lautet \(\partial w_i/\partial s_j\) für \(w=\operatorname{softmax}(s/T)\), und was folgt bei fast one-hot \(w\)?',
      answer=r'\(\tfrac1T(w_i[i=j]-w_iw_j)\). Bei fester \(T\) und \(w\to e_m\) gilt \(J\to0\); bei \(T\to0\) nur mit eindeutigem Maximum, bei Gleichstand divergiert \(J\).', why=r'\(\lVert J\rVert_F\le4(1-w_m)/T\) (Lemma 6.4). Gesättigte Softmax leitet kaum Gradient – Grund für \(1/\sqrt{d_k}\).',
      source='Lehrbuch §6, Lemma 6.4; Labor Station 6', example=r'Zwei Scores: \(\partial w_1/\partial s_1=w_1(1-w_1)\), maximal \(0{,}25\) bei \(w_1=0{,}5\).', mistake='„Kleines T ⇒ kleiner Gradient“ – falsch bei gleich großen Maxima.', prereq='Softmax, Kettenregel; Satz 3'),
 dict(key='attention/hull-impossible', kc='attention', type='case', prompt=r'Values \(v_1=(1,0)\), \(v_2=(0,1)\), \(v_3=(0,0)\). Kann eine Attention-Schicht allein \(o=(1,1)\) ausgeben?',
      answer=r'Nein: \(o=(w_1,w_2)\) mit \(w_1+w_2&lt;1\); \((1,1)\) liegt außerhalb der konvexen Hülle.', why='Softmax-Gewichte sind positiv und summieren zu 1 – Konvexkombination (Satz 6.2). Abhilfe: W_O und Residualverbindung.',
      source='Lehrbuch §6, Satz 6.2; Aufgabe AT7; Labor Challenge „Unerreichbar?“', mistake='Mit T → 0 „erzwingen“: Das ergibt einen Value (eindeutiges Maximum) oder den Mittelwert gleichauf liegender Values – beides in der Hülle.', diagram='attention_hull.svg', prereq='Konvexkombination'),
]

CARD_EXTRAS = {  # bestehende Karten: Voraussetzungen (bisher 0 belegt), Beispiele, Fehlvorstellungen, fokussierte Grafiken
 'spans/io-not-injective': dict(prereq='Spanne, Entitätstyp'), 'spans/label-count': dict(prereq='Kodierungsschemata IO, BIO, BILOU'),
 'spans/conlleval-i': dict(prereq='BIO-Kodierung', example=r'<code>O I-LOC I-LOC B-LOC</code> → [w₂ w₃]LOC, [w₄]LOC'), 'spans/encode-mini': dict(prereq='BIO-Kodierung'), 'spans/bilou-evidence': dict(prereq='BIO, BILOU'),
 'birnn/abhaengigkeit-vorwaerts': dict(prereq='RNN-Rekursion'), 'birnn/washington': dict(prereq='Vorwärts-RNN; BiRNN', mistake='„Das Vorwärts-RNN sieht das nächste Wort“ – erst ab Position 2.'),
 'birnn/definition': dict(prereq='RNN-Rekursion'), 'birnn/latenz': dict(prereq='BiRNN-Definition'), 'birnn/softmax-unabhaengig': dict(prereq='Softmax je Position'),
 'birnn/params': dict(prereq='Matrixdimensionen eines RNN'), 'birnn/error-wo': dict(prereq='Verkettung [h→; h←]'),
 'attention/formel': dict(prereq='Skalarprodukt, Softmax', example=r'Bank-Beispiel: \(w=(0{,}5904;\,0{,}1037;\,0{,}3059)\), \(o=(1{,}1343;\,0{,}3763)\)', mistake='Values in die Gewichte einrechnen – sie werden nur gemischt.'),
 'attention/gelernt': dict(prereq='Self-Attention-Formel'), 'attention/skalierung': dict(prereq='Varianz, Unabhängigkeit', mistake='„Skalierung normiert die Gewichte auf Summe 1“ – das tut die Softmax.'),
 'attention/sharpening': dict(prereq='Softmax, Temperatur'), 'attention/convex': dict(prereq='Konvexkombination', diagram='attention_hull.svg', mistake='Mit kleiner Temperatur Punkte außerhalb erreichen wollen.'),
 'attention/burger': dict(prereq='gewichtete Summe'), 'attention/multihead': dict(prereq='Projektionsmatrizen'),
 'position/permutation': dict(prereq='Self-Attention-Formel; Permutationsmatrix', mistake='„Invarianz“ statt Äquivarianz: Die Ausgaben wandern mit.'), 'position/sinus-linear': dict(prereq='Additionstheoreme'),
 'position/rope': dict(prereq='Rotationsmatrix'), 'position/learned-nachteil': dict(prereq='Positionskodierung'),
 'decoding/crf-score': dict(prereq='Emission, Übergang'), 'decoding/crf-prob': dict(prereq='CRF-Score; Softmax über Folgen'), 'decoding/forward-vs-viterbi': dict(prereq='Viterbi-Rekursion', example=r'max ↔ log Σ exp: \(\delta\) vs. \(\alpha\)'),
 'decoding/prob-mini': dict(prereq='Partitionsfunktion Z'), 'decoding/garantie': dict(prereq='BIO-Gültigkeit; Viterbi'), 'decoding/label-vs-exposure': dict(prereq='lokale vs. globale Normierung'), 'decoding/greedy-evidence': dict(prereq='gierige Dekodierung'),
 'prf/zaehlform': dict(prereq='TP, FP, FN'), 'prf/schranke': dict(prereq='harmonisches Mittel'), 'prf/keine-tn': dict(prereq='Konfusionsmatrix'), 'prf/fbeta': dict(prereq='F1-Formel'),
 'prf-edge/nichts-ausgegeben': dict(prereq='Zählform von F1'), 'prf-edge/tp-null': dict(prereq='Zählform von F1'), 'prf-edge/beide-leer': dict(prereq='Zählform von F1'),
 'prf-level/doppelt': dict(prereq='exakter Spannenvergleich', example='[Angela Merkel]PER vs. [Angela]PER: 1 FP + 1 FN'), 'prf-level/rangfolge': dict(prereq='Token- vs. Spannen-Zählung'),
 'micro-macro/gewicht': dict(prereq='Micro-F1'), 'micro-macro/error-support': dict(prereq='Micro-F1 als gewichtetes Mittel'), 'micro-macro/unterschied': dict(prereq='F1 je Typ'), 'micro-macro/accuracy': dict(prereq='Micro-F1, Accuracy'),
}

SOURCES = [
 {'id': 'jain', 'kind': 'FORSCHUNG', 'ref': 'Jain, S.; Wallace, B. C. (2019): Attention is not Explanation. Proc. NAACL-HLT 2019, 3543–3556. Gelesen: Zusammenfassung.', 'url': 'https://aclanthology.org/N19-1357/'},
 {'id': 'wiegreffe', 'kind': 'FORSCHUNG', 'ref': 'Wiegreffe, S.; Pinter, Y. (2019): Attention is not not Explanation. Proc. EMNLP-IJCNLP 2019, 11–20. Gelesen: Zusammenfassung.', 'url': 'https://aclanthology.org/D19-1002/'},
 {'id': '3b1b-attention', 'kind': 'VERTIEFUNG', 'ref': '3Blue1Brown (G. Sanderson): Attention in transformers, step-by-step. Deep Learning, Kapitel 6, Video, 7. April 2024. Rolle: visuelle Intuition; nicht im Detail ausgewertet.', 'url': 'https://www.3blue1brown.com/lessons/attention'},
]
