"""v5 (Issue #8): ausführliche Musterlösungen der Probeklausur, getrennt vom knappen Bewertungsschlüssel (`solution`).

Jede Zahl mit Nachkommastellen wird von reference_unit.verify nachgerechnet (Prosa-Prüfung schließt `worked` ein).
"""
W = {}
R = {}

W['A1'] = r'''<b>Ansatz.</b> BIO braucht je Typ ein Label für den Spannenanfang (B-) und eines für die Fortsetzung (I-), dazu ein gemeinsames O.<br><b>Rechnung.</b> \(|\mathcal L|=2K+1=2\cdot7+1=15\).<br><b>Kontrolle.</b> Für \(K=1\): B-X, I-X, O – drei Labels, Formel liefert \(3\). <b>Typischer Fehler:</b> \(2K=14\) (O vergessen).'''
R['A1'] = ['Formel 2K+1 mit Begründung (1 P.)', 'Ergebnis 15 (1 P.)']
W['A2'] = r'''<b>Lesart von <code>conlleval</code>.</b> Eine Spanne beginnt bei B-X oder bei I-X, das keine Spanne desselben Typs fortsetzt.<br>\(w_1\): <code>B-PER</code> eröffnet \([w_1]\)PER. \(w_2\): <code>I-LOC</code> kann die PER-Spanne nicht fortsetzen (anderer Typ), also schließt \([w_1]\)PER und \(w_2\) eröffnet \([w_2]\)LOC.<br><b>Antwort (a).</b> Option (c) ist falsch, weil <code>conlleval</code> ungültige Folgen nicht verwirft, sondern nach dieser Regel liest; (b) ignoriert den Typwechsel.'''
R['A2'] = ['Typwechsel beendet Spanne (1 P.)', 'I-X ohne Vorgänger eröffnet neue Spanne (1 P.)']
W['A3'] = r'''<b>Labels.</b> \(|\mathcal L|=2\cdot4+1=9\).<br><b>Eine Richtung.</b> \(W\in\mathbb R^{200\times200}\): \(40\,000\); \(U\in\mathbb R^{200\times300}\): \(60\,000\); \(b\): \(200\). Zusammen \(100\,200\).<br><b>Beide Richtungen</b> (getrennte Parameter): \(200\,400\).<br><b>Ausgabe.</b> \(W_o\in\mathbb R^{9\times400}\) liest den verketteten Zustand \([\overrightarrow h_t;\overleftarrow h_t]\in\mathbb R^{400}\), dazu 9 Bias-Werte: \(9\cdot401=3\,609\).<br><b>Summe.</b> \(200\,400+3\,609=204\,009\).'''
R['A3'] = ['Labelzahl 9 (1 P.)', 'je Richtung d_h²+d_h·d+d_h (1 P.)', 'zwei Richtungen (1 P.)', 'W_o mit 2d_h Spalten + Bias (1 P.)']
W['A4'] = r'''<b>Bedingung.</b> Das Label von Wort \(t\) darf nur von \(x_1,\dots,x_t\) abhängen.<br><b>Vorwärts-RNN.</b> \(\overrightarrow h_t=f(x_1,\dots,x_t)\) (Satz 1) – erfüllt.<br><b>BiRNN</b> (mit oder ohne CRF): \(\overleftarrow h_t\) hängt von \(x_t,\dots,x_T\) ab (Satz 2), also auch von Wort \(t+1\) – erst nach Satzende verfügbar. Ein CRF verschärft das: Viterbi legt Labels erst nach dem letzten Wort fest.<br><b>Antwort (b).</b>'''
R['A4'] = ['Abhängigkeitsbereich Vorwärts (1 P.)', 'BiRNN/CRF brauchen Satzende (1 P.)']
W['A5'] = r'''<b>Annahmen</b> (Satz 3): \(q_i,k_i\) unabhängig, Erwartungswert 0, Varianz 1.<br>\(\operatorname{Var}(q_ik_i)=\mathbb E[q_i^2]\,\mathbb E[k_i^2]=1\); die 64 Summanden sind unkorreliert, Varianzen addieren sich: \(\operatorname{Var}(q^\top k)=64\).<br><b>Einordnung.</b> Standardabweichung \(8\); nach Division durch \(\sqrt{64}=8\) Varianz 1. Ohne Skalierung lägen typische Score-Abstände bei mehreren Einheiten – die Softmax sättigt (Labor: Ansicht „Skalierung“).'''
R['A5'] = ['Varianz je Summand 1 mit Annahme (1 P.)', 'Additivität → 64 (1 P.)']
W['A6'] = r'''<b>Skalarprodukte.</b> \(q^\top k_1=2\cdot1+0\cdot0=2\), \(q^\top k_2=2\cdot0+0\cdot1=0\).<br><b>Skalierung.</b> \(e_1=2/\sqrt2=1{,}4142\), \(e_2=0\).<br><b>Softmax.</b> \(e^{1{,}4142}=4{,}1133\), \(e^0=1\): \(\alpha_1=4{,}1133/(4{,}1133+1)=0{,}8044\), \(\alpha_2=1-\alpha_1\).<br><b>Probe.</b> \(\alpha_1/\alpha_2=e^{e_1-e_2}=4{,}1133\). Ohne Skalierung wäre \(\alpha_1=e^2/(e^2+1)\) größer – Skalierung macht die Verteilung flacher.'''
R['A6'] = ['Skalarprodukte (1 P.)', 'Division durch √2 (1 P.)', 'Softmax korrekt (2 P.)']
W['A7'] = r'''<b>Satz 4.</b> Sei \(P\) die Permutationsmatrix. Dann \(Q'=PQ\), \(K'=PK\), \(V'=PV\) und \(Q'K'^\top=P\,QK^\top P^\top\). Die zeilenweise Softmax vertauscht nur Zeilen und Spalten mit: \(\operatorname{softmax}(PSP^\top)=P\operatorname{softmax}(S)P^\top\). Also \(\operatorname{Att}(PX)=P\operatorname{softmax}(S)P^\top PV=P\operatorname{Att}(X)\) wegen \(P^\top P=I\).<br><b>Deutung.</b> Jedes Token erhält exakt denselben Ausgabevektor, nur in anderer Zeile (Antwort a). Gegenbeispiel-Bedingung: Mit Positionsvektoren oder kausaler Maske gilt das nicht mehr (Labor, Ansicht „Ganzer Satz“).'''
R['A7'] = ['Äquivarianz statt Invarianz erkannt (1 P.)', 'Begründung über PSPᵀ (1 P.)']
W['A8'] = r'''<b>RoPE.</b> \(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R\big((n-m)\theta\big)k\), weil \(R(a)^\top R(b)=R(b-a)\).<br>Mit \(q=k=(1,0)\): \(q^\top R(\phi)k=\cos\phi\). Hier \(\phi=(5-1)\cdot0{,}25=1\): Ähnlichkeit \(\cos 1=0{,}5403\).<br><b>Kontrolle.</b> Gleiche Positionen ergäben \(\cos0=1\); nur der Abstand 4 zählt.'''
R['A8'] = ['Abstandsformel (1 P.)', 'Winkel 1 und cos 1 (1 P.)']
W['A9'] = r'''<b>Gierig.</b> nach→O (1,5), New→I-LOC (1,1), York→I-LOC (1,4): Folge O I-LOC I-LOC ist ungültig (O→I-LOC verboten).<br><b>Gültige Kandidaten</b> (Summe der Emissionen, Übergänge sonst 0): O B-LOC I-LOC: \(1{,}5+0{,}9+1{,}4=3{,}8\); O B-LOC O: \(1{,}5+0{,}9+0{,}1=2{,}5\); O O O: \(1{,}5+0{,}4+0{,}1=2{,}0\); B-LOC I-LOC I-LOC: \(0{,}2+1{,}1+1{,}4=2{,}7\).<br><b>Viterbi.</b> Bester gültiger Pfad O B-LOC I-LOC mit Score \(3{,}8\). Er unterscheidet sich vom gierigen Ergebnis nur an „New“: Das Verbot erzwingt dort B statt I.'''
R['A9'] = ['Gierige Folge als ungültig erkannt (1 P.)', 'Kandidatenvergleich oder Viterbi-Rekursion (2 P.)', 'Score 3,8 (1 P.)']
W['A10'] = r'''Ein CRF mit \(-\infty\) für verbotene Übergänge gibt jedem ungültigen Pfad Wahrscheinlichkeit 0; Viterbi wählt daher immer einen gültigen Pfad (Antwort a). <b>Nicht garantiert:</b> richtige Grenzen oder Typen – die hängen von den Emissionen ab. <b>Beleg:</b> Ratinov &amp; Roth (2009) fanden gierige Dekodierung mit BILOU vergleichbar gut. Gegenbeispiel im Labor: verbotene Übergänge reparieren die Gültigkeit, nicht die Spannengrenze.'''
R['A10'] = ['nur Gültigkeit (1 P.)', 'Abgrenzung zu Grenz-/Typfehlern (1 P.)']
W['A11'] = r'''\(F_1=\dfrac{2\,\mathrm{TP}}{2\,\mathrm{TP}+\mathrm{FP}+\mathrm{FN}}=\dfrac{24}{24+4+8}=\dfrac{24}{36}=\dfrac23\).<br><b>Kontrolle über P und R.</b> \(P=12/16\), \(R=12/20\); \(2PR/(P+R)\) ergibt denselben Wert \(2/3\).'''
R['A11'] = ['Zählform (1 P.)', 'Ergebnis 2/3 (1 P.)']
W['A12'] = r'''Das arithmetische Mittel \((0{,}2+1)/2=0{,}6\) ist falsch: \(F_1\) ist das <em>harmonische</em> Mittel. \(F_1=\dfrac{2\cdot0{,}2\cdot1}{0{,}2+1}=\dfrac{0{,}4}{1{,}2}=\dfrac13\approx0{,}3333\).<br><b>Schranke.</b> \(F_1\le 2\min(P,R)=0{,}4\): Ein schlechter Wert lässt sich nicht durch einen guten ausgleichen.'''
R['A12'] = ['harmonisches Mittel (1 P.)', 'Ergebnis 1/3 (1 P.)']
W['A13'] = r'''TP = 0, FP = 0, FN = 3. \(P=0/0\) ist undefiniert (keine Ausgabe), \(R=0/3=0\). Zählform: \(F_1=0/(0+0+3)=0\) – definiert, weil der Nenner \(2\mathrm{TP}+\mathrm{FP}+\mathrm{FN}=3\ne0\).'''
R['A13'] = ['P undefiniert erkannt (1 P.)', 'F1 = 0 aus Zählform (1 P.)']
W['A14'] = r'''TP = FP = FN = 0: Auch die Zählform ergibt \(0/0\). Weder 1 („kein Fehler“) noch 0 („kein Treffer“) folgt aus der Definition; Werkzeuge setzen per Konvention einen Wert (z. B. <code>zero_division</code> in scikit-learn). Antwort (c).'''
R['A14'] = ['0/0 erkannt (1 P.)', 'Konvention benannt (1 P.)']
W['A15'] = r'''<b>Gold-Spannen</b> (3): [FC Bayern München]ORG, [Dortmund]LOC, [Borussia Dortmund]ORG.<br><b>System-Spannen</b> (4): [FC Bayern]ORG, [München]LOC, [Dortmund]LOC, [Borussia Dortmund]PER.<br><b>Exakter Vergleich.</b> Nur [Dortmund]LOC stimmt: TP = 1. FP = 4 − 1 = 3, FN = 3 − 1 = 2.<br>\(F_1=\dfrac{2}{2+3+2}=\dfrac27\). Der Grenzfehler bei „FC Bayern München“ kostet einen FN und zwei FP.'''
R['A15'] = ['Spannen beider Seiten (1 P.)', 'TP/FP/FN (2 P.)', 'F1 = 2/7 (1 P.)']
W['A16'] = r'''<b>Token mit Entitätstyp</b> (Gold): FC, Bayern, München (ORG), Dortmund (LOC), Borussia, Dortmund (ORG).<br>Vergleich je Token: FC ✓, Bayern ✓, München ORG→LOC (FP und FN), Dortmund LOC ✓, Borussia ORG→PER (FP+FN), Dortmund ORG→PER (FP+FN).<br>TP = 3, FP = 3, FN = 3: \(F_1=6/12=1/2\) – höher als Phrasen-\(F_1=2/7\), weil Teiltreffer zählen.'''
R['A16'] = ['tokenweiser Vergleich (2 P.)', 'F1 = 1/2 (1 P.)', 'Vergleich zu A15 (1 P.)']
W['A17'] = r'''<b>Micro:</b> Zählwerte summieren: TP = 60 + 40 + 70 = 170, FP = 15 + 20 + 5 = 40, FN = 10 + 30 + 5 = 45.<br>\(F_1=\dfrac{340}{340+40+45}=\dfrac{340}{425}=0{,}8\).'''
R['A17'] = ['Summieren der Zählwerte (1 P.)', 'Ergebnis 0,8 (1 P.)']
W['A18'] = r'''<b>Je Typ</b> (Zählform): PER \(120/145=0{,}8276\), ORG \(80/130=0{,}6154\), LOC \(140/150=0{,}9333\).<br><b>Macro</b> = ungewichtetes Mittel: \((0{,}8276+0{,}6154+0{,}9333)/3=0{,}7921\).<br><b>Vergleich.</b> Macro &lt; Micro (0,8), weil der schwache Typ ORG mit Gewicht \(1/3\) eingeht, in Micro aber nur mit \(130/425\).'''
R['A18'] = ['F1 je Typ (2 P.)', 'Mittelwert (1 P.)', 'Deutung (1 P.)']
W['B-1'] = r'''BILOU: je Typ B (Anfang), I (innen), L (letztes), U (Einzel-Token), dazu O: \(4K+1=4\cdot3+1=13\). <b>Kontrolle</b> \(K=1\): B, I, L, U, O.'''
R['B-1'] = ['4K+1 (1 P.)', '13 (1 P.)']
W['B-2'] = r'''IO: beide Lesarten ergeben <code>DAY DAY</code> – nicht unterscheidbar (Antwort a). BIO: <code>B-DAY B-DAY</code> vs. <code>B-DAY I-DAY</code>. BILOU: <code>U-DAY U-DAY</code> vs. <code>B-DAY L-DAY</code>. Satz A: BIO ist auf gültigen Folgen umkehrbar, IO nicht.'''
R['B-2'] = ['IO (1 P.)', 'Begründung mit Kodierungen (1 P.)']
W['B-3'] = r'''\(|\mathcal L|=2\cdot2+1=5\). Je Richtung \(32^2+32\cdot64+32=1\,024+2\,048+32=3\,104\); beide \(6\,208\). Ausgabe \(W_o\in\mathbb R^{5\times64}\) plus Bias: \(5\cdot65=325\). Summe \(6\,533\).'''
R['B-3'] = ['Labelzahl (1 P.)', 'Richtungen (1 P.)', 'Ausgabe 2d_h+1 (1 P.)', 'Summe (1 P.)']
W['B-4'] = r'''\(\overrightarrow h_t\) hängt nur von \(x_1,\dots,x_t\) ab (Satz 1). Die Sätze stimmen in \(x_1..x_4\) überein, also gilt \(\overrightarrow h_t\) gleich für \(t=1,2,3,4\). Ab \(t=5\) hat der Zustand das abweichende Wort gelesen; ob er sich tatsächlich unterscheidet, hängt von den Gewichten ab – garantiert ist nur 1–4.'''
R['B-4'] = ['1,2,3,4 (1 P.)', 'Begründung „garantiert“ vs. „möglicherweise“ (1 P.)']
W['B-5'] = r'''Je Kopf \(W_Q^{(i)}\in\mathbb R^{512\times64}\) (\(d/h=64\)): \(32\,768\) Einträge. Acht Köpfe: \(8\cdot32\,768=262\,144=512^2\). Gleich viele wie eine einzelne \(512\times512\)-Projektion: Die Aufteilung schneidet die Matrix nur in Spaltenblöcke.'''
R['B-5'] = ['Kopfdimension d/h (1 P.)', 'Summe 262 144 (1 P.)']
W['B-6'] = r'''Antwort (a). Unter den Annahmen von Satz 3 ist \(\operatorname{Var}(q^\top k)=d_k\); Division durch \(\sqrt{d_k}\) bringt die Varianz auf 1. Ohne sie werden Score-Abstände groß, die Softmax nahezu one-hot und ihre Jacobi-Matrix \(\operatorname{diag}(w)-ww^\top\) fast 0 – kleine Gradienten. (b) ist falsch: Normierung auf Summe 1 leistet die Softmax immer. (c) ist falsch: Die Werte gehen nicht in die Gewichte ein.'''
R['B-6'] = ['Varianzargument (1 P.)', 'Abgrenzung zu (b)/(c) (1 P.)']
W['B-7'] = r'''Formel (Vaswani et al. 2017, §3.5): gerade Dimension \(i=2k\): \(\sin\big(t/10000^{2k/d}\big)\). Hier \(t=3\), \(i=2\Rightarrow k=1\), \(d=4\): \(10000^{2/4}=100\), also \(\sin(3/100)=\sin(0{,}03)\approx0{,}0300\).'''
R['B-7'] = ['richtiger Exponent 2k/d (1 P.)', 'Wert (1 P.)']
W['B-8'] = r'''\(R(a)^\top R(b)=R(b-a)\), daher \(\big(R(3\theta)q\big)^\top R((3+\Delta)\theta)k=q^\top R(\Delta\theta)k\): nur \(q\), \(k\) und der Abstand \(\Delta\) (Antwort a). Die absolute Position 3 kürzt sich heraus.'''
R['B-8'] = ['Rotationsregel (1 P.)', 'Antwort (1 P.)']
W['B-9'] = r'''<b>Gierig.</b> Wort 1→B-LOC (1,0), Wort 2→I-LOC (0,9), Wort 3→O (1,2): B-LOC I-LOC O ist gültig. Da die Übergänge nur verbieten, aber nichts belohnen, ist die gierige Folge bereits optimal: Viterbi ändert nichts. Score \(1{,}0+0{,}9+1{,}2=3{,}1\). <b>Lehre:</b> Ein CRF mit harten Regeln greift nur bei ungültigen Folgen ein.'''
R['B-9'] = ['Gültigkeit geprüft (1 P.)', 'Score 3,1 (1 P.)']
W['B-10'] = r'''Exposure Bias (a): Im Training sieht das Modell Gold-Vorgänger, im Test eigene (möglicherweise falsche) Vorhersagen – Fehler pflanzen sich fort. Label Bias (b) ist ein anderes Problem lokal normierter Modelle (MEMM): Zustände mit wenigen Nachfolgern ignorieren die Beobachtung; CRFs normieren global.'''
R['B-10'] = ['Begriff (1 P.)', 'Abgrenzung Label Bias (1 P.)']
W['B-11'] = r'''\(F_1=\dfrac{36}{36+2+12}=\dfrac{36}{50}=0{,}72\). Kontrolle: \(P=18/20\), \(R=18/30\).'''
R['B-11'] = ['Zählform (1 P.)', '0,72 (1 P.)']
W['B-12'] = r'''\(F_1=\dfrac{2PR}{P+R}=\dfrac{2\cdot0{,}27}{1{,}2}=0{,}45\) mit \(PR=0{,}9\cdot0{,}3=0{,}27\) und \(P+R=1{,}2\). Liegt nahe am kleineren Wert: harmonisches Mittel.'''
R['B-12'] = ['Produkt und Summe (1 P.)', '0,45 (1 P.)']
W['B-13'] = r'''TP = 0, FP = 4, FN = 0: \(P=0/4=0\); \(R=0/0\) undefiniert (kein Gold); Zählform \(F_1=0/(0+4+0)=0\). Antwort (b) – Fall (iv) der Tabelle im Lehrbuch.'''
R['B-13'] = ['P und R (1 P.)', 'F1 = 0 aus Zählform (1 P.)']
W['B-14'] = r'''\(P=0/2=0\), \(R=0/5=0\). \(2PR/(P+R)=0/0\): kein Wert (Antwort b). Die Zählform liefert dagegen \(0/(0+2+5)=0\) – deshalb definiert man \(F_1\) über die Zählform.'''
R['B-14'] = ['0/0 erkannt (1 P.)', 'Zählform als Ausweg (1 P.)']
W['B-15'] = r'''Gold: [Barack Obama]PER, [Angela Merkel]PER, [Berlin]LOC. System: [Barack Obama]PER, [Angela Merkel]LOC, [Berlin]LOC. TP = 2, FP = 1 ([Angela Merkel]LOC), FN = 1 ([Angela Merkel]PER): \(F_1=4/6=2/3\).'''
R['B-15'] = ['Zählung (1 P.)', '2/3 (1 P.)']
W['B-16'] = r'''Token: Barack ✓, Obama ✓, Angela PER→LOC, Merkel PER→LOC, Berlin ✓. TP = 3, FP = 2, FN = 2: \(F_1=6/10=3/5\). Hier ist die Token-Ebene <em>strenger</em> als die Phrasen-Ebene (2/3), weil der Typfehler eine zweiwortige Spanne betrifft – die Rangfolge der Zählweisen ist nicht festgelegt.'''
R['B-16'] = ['Token-Zählung (1 P.)', 'Deutung (1 P.)']
W['B-17'] = r'''TP = 150, FP = 50, FN = 30: \(F_1=300/(300+50+30)=300/380=15/19\approx0{,}7895\).'''
R['B-17'] = ['Summen (1 P.)', 'Ergebnis (1 P.)']
W['B-18'] = r'''Micro-\(F_1\) ist ein gewichtetes Mittel der Typ-\(F_1\) mit Gewichten \(D_k=2\mathrm{TP}_k+\mathrm{FP}_k+\mathrm{FN}_k\): PER \(120\), ORG \(60\), LOC \(200\), Summe \(380\). Beweisidee: \(F_1^{(k)}D_k=2\mathrm{TP}_k\), also \(\sum_kF_1^{(k)}D_k/\sum_kD_k=2\mathrm{TP}/D\). Gewicht ORG \(=60/380\approx0{,}1579\), größer als sein Gold-Anteil \(20/180\approx0{,}1111\), weil die 30 Fehlalarme in \(D\) zählen.'''
R['B-18'] = ['Gewichtsformel (1 P.)', 'Wert (1 P.)']
