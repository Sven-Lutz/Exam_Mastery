# Lösungsschlüssel Neuronale Sequenzmarkierung

Nur hochladen, wenn der Tutor Antworten prüfen soll. Der Tutor gibt Lösungen erst nach eigenem Versuch preis.

## S1
**Kurzschlüssel.** (a) \(4\cdot5+1=21\). (b) \(w_1\) ist O. \(w_2\) ist <code>I-LOC</code> ohne Vorgänger desselben Typs und eröffnet daher eine Spanne, die \(w_3\) fortsetzt. \(w_4\) ist <code>B-LOC</code> und beginnt eine neue: \([w_2\,w_3]\)LOC und \([w_4]\)LOC.

**Ausführliche Lösung.** (a) \(4\cdot5+1=21\). (b) \(w_1\) ist O. \(w_2\) ist <code>I-LOC</code> ohne Vorgänger desselben Typs und eröffnet daher eine Spanne, die \(w_3\) fortsetzt. \(w_4\) ist <code>B-LOC</code> und beginnt eine neue: \([w_2\,w_3]\)LOC und \([w_4]\)LOC.

**Bewertung.** 4K+1 (1 P.) · I ohne Vorgänger eröffnet Spanne (1 P.) · B beginnt neue Spanne (1 P.)

## G1
**Kurzschlüssel.** \(0{,}5\,h^{\rightarrow}_1+e_2=(0{,}3808;\,-1)\), also \(h^{\rightarrow}_2=(\tanh 0{,}3808;\ \tanh(-1))=(0{,}3634;\,-0{,}7616)\). Mit „signed“: \((0{,}3634;\,+0{,}7616)\). Ab Position 2 unterscheiden sich die Sätze – dort hat der Vorwärtszustand das unterschiedliche Wort gelesen.

**Ausführliche Lösung.** \(0{,}5\,h^{\rightarrow}_1+e_2=(0{,}3808;\,-1)\), also \(h^{\rightarrow}_2=(\tanh 0{,}3808;\ \tanh(-1))=(0{,}3634;\,-0{,}7616)\). Mit „signed“: \((0{,}3634;\,+0{,}7616)\). Ab Position 2 unterscheiden sich die Sätze – dort hat der Vorwärtszustand das unterschiedliche Wort gelesen.

**Bewertung.** Dämpfung 0,5 auf den alten Zustand · Komponentenweise tanh · Deutung: Unterschied erst ab Position 2

## W1
**Kurzschlüssel.** \(|\mathcal L|=2\cdot4+1=9\). Je Richtung \(128^2+128\cdot100+128=29\,312\), beide Richtungen \(58\,624\). Ausgabe \(W_o\in\mathbb R^{9\times256}\) plus Bias: \(9\cdot256+9=2\,313\). Summe \(60\,937\). Selbsterklärung: \(W_o\) hat 256 Spalten, weil der Klassifikator \(h^{\mathrm{bi}}_t\in\mathbb R^{2d_h}\) liest.

**Ausführliche Lösung.** \(|\mathcal L|=2\cdot4+1=9\). Je Richtung \(128^2+128\cdot100+128=29\,312\), beide Richtungen \(58\,624\). Ausgabe \(W_o\in\mathbb R^{9\times256}\) plus Bias: \(9\cdot256+9=2\,313\). Summe \(60\,937\). Selbsterklärung: \(W_o\) hat 256 Spalten, weil der Klassifikator \(h^{\mathrm{bi}}_t\in\mathbb R^{2d_h}\) liest.

**Bewertung.** Labelzahl 2K+1 · zwei Richtungen ohne geteilte Parameter · W_o mit 2d_h Spalten · Summe

## B1
**Kurzschlüssel.** \(|\mathcal L|=2\cdot3+1=7\). Je Richtung \(64^2+64\cdot50+64=4\,096+3\,200+64=7\,360\); beide \(14\,720\). Ausgabe \(7\cdot128+7=903\). Summe \(15\,623\).

**Ausführliche Lösung.** \(|\mathcal L|=2\cdot3+1=7\). Je Richtung \(64^2+64\cdot50+64=4\,096+3\,200+64=7\,360\); beide \(14\,720\). Ausgabe \(7\cdot128+7=903\). Summe \(15\,623\).

**Bewertung.** Labelzahl (1 P.) · zwei Richtungen (1 P.) · W_o mit 2d_h Spalten (1 P.) · Summe (1 P.)

## B2
**Kurzschlüssel.** \(\tanh(-0{,}6093)\approx-0{,}5436\), also \(h^{\leftarrow}_1=(0{,}7616;\,-0{,}5436)\). Das Minuszeichen stammt von „state“ an Position 2 und erreicht Position 1 nur über die Rückwärtsrekursion.

**Ausführliche Lösung.** \(\tanh(-0{,}6093)\approx-0{,}5436\), also \(h^{\leftarrow}_1=(0{,}7616;\,-0{,}5436)\). Das Minuszeichen stammt von „state“ an Position 2 und erreicht Position 1 nur über die Rückwärtsrekursion.

**Bewertung.** Rekursion von rechts · Wert ±0,0005 · Herkunft des Vorzeichens

## AT1
**Kurzschlüssel.** \(\alpha_{3\cdot}=(2{,}0281;\,2{,}0281;\,4{,}1133)/8{,}1695=(0{,}2483;\,0{,}2483;\,0{,}5035)\). \(o_3=0{,}2483\,(1,0)+0{,}2483\,(0,1)+0{,}5035\,(1,1)=(0{,}7517;\,0{,}7517)\). Token 3 achtet am stärksten auf sich selbst, weil \(q_3\) mit \(k_3\) das größte Skalarprodukt hat.

**Ausführliche Lösung.** \(\alpha_{3\cdot}=(2{,}0281;\,2{,}0281;\,4{,}1133)/8{,}1695=(0{,}2483;\,0{,}2483;\,0{,}5035)\). \(o_3=0{,}2483\,(1,0)+0{,}2483\,(0,1)+0{,}5035\,(1,1)=(0{,}7517;\,0{,}7517)\). Token 3 achtet am stärksten auf sich selbst, weil \(q_3\) mit \(k_3\) das größte Skalarprodukt hat.

**Bewertung.** Energien mit Skalierung · Softmax korrekt normiert · gewichtete Summe

## PO1
**Kurzschlüssel.** (a) Identisch: \(\operatorname{Att}(PX)=P\operatorname{Att}(X)\), der Vektor wandert nur mit dem Token. (b) \(q^\top R((5-2)\cdot0{,}5)k=\cos(1{,}5)\approx0{,}0707\). Gleicher Wert für \(m=4,n=7\): nur der Abstand zählt.

**Ausführliche Lösung.** (a) Identisch: \(\operatorname{Att}(PX)=P\operatorname{Att}(X)\), der Vektor wandert nur mit dem Token. (b) \(q^\top R((5-2)\cdot0{,}5)k=\cos(1{,}5)\approx0{,}0707\). Gleicher Wert für \(m=4,n=7\): nur der Abstand zählt.

**Bewertung.** Satz 4 angewandt · Drehungen zusammengefasst · Wert

## C1
**Kurzschlüssel.** (a) Je Wort das Maximum: O (2), I-LOC (1,2), I-LOC (1,5) – Score 4,7, aber O→I-LOC ist verboten. (b) Gültige Kandidaten: O B-LOC I-LOC mit \(2+1{,}0+1{,}5=4{,}5\); O B-LOC B-LOC mit 3,2; O O I-LOC verboten; O O O mit 2,3. Viterbi wählt O B-LOC I-LOC, Score 4,5.

**Ausführliche Lösung.** (a) Je Wort das Maximum: O (2), I-LOC (1,2), I-LOC (1,5) – Score 4,7, aber O→I-LOC ist verboten. (b) Gültige Kandidaten: O B-LOC I-LOC mit \(2+1{,}0+1{,}5=4{,}5\); O B-LOC B-LOC mit 3,2; O O I-LOC verboten; O O O mit 2,3. Viterbi wählt O B-LOC I-LOC, Score 4,5.

**Bewertung.** gierige Folge · Übergangsregel angewandt · bester Score

## B3
**Kurzschlüssel.** TP = FP = 0, FN = 3. \(P=0/0\) nicht definiert, \(R=0/3=0\), Zählform \(F_1=0/(0+0+3)=0\). \(2PR/(P+R)\) ist hier nicht anwendbar.

**Ausführliche Lösung.** TP = FP = 0, FN = 3. \(P=0/0\) nicht definiert, \(R=0/3=0\), Zählform \(F_1=0/(0+0+3)=0\). \(2PR/(P+R)\) ist hier nicht anwendbar.

**Bewertung.** Zählungen · P undefiniert begründet · F1 = 0 über Zählform

## B4
**Kurzschlüssel.** Phrasen: Gold {[Angela Merkel]PER, [Siemens AG]ORG, [München]LOC}, System {[Angela Merkel]PER, [Siemens]ORG, [München]ORG}: TP = 1, FP = 2, FN = 2, \(F_1=2/6=1/3\). Token: TP = 3 (Angela, Merkel, Siemens), FP = 1 (München als ORG), FN = 2 (AG; München als LOC): \(F_1=6/9=2/3\).

**Ausführliche Lösung.** Phrasen: Gold {[Angela Merkel]PER, [Siemens AG]ORG, [München]LOC}, System {[Angela Merkel]PER, [Siemens]ORG, [München]ORG}: TP = 1, FP = 2, FN = 2, \(F_1=2/6=1/3\). Token: TP = 3 (Angela, Merkel, Siemens), FP = 1 (München als ORG), FN = 2 (AG; München als LOC): \(F_1=6/9=2/3\).

**Bewertung.** Spannenmengen (1 P.) · Doppelzählung (2 P.) · Token-Zählung (1 P.) · beide Werte (1 P.)

## B5
**Kurzschlüssel.** Jede System-Spanne muss genau einmal als TP oder FP erscheinen. Das System gibt drei Spannen aus; in ihren Listen stehen zwei ([Angela Merkel] als TP, [Siemens] als FP). [München]ORG fehlt als FP. Richtig: FP = 2, \(P=\tfrac13\). Die FN-Liste ist korrekt.

**Ausführliche Lösung.** Jede System-Spanne muss genau einmal als TP oder FP erscheinen. Das System gibt drei Spannen aus; in ihren Listen stehen zwei ([Angela Merkel] als TP, [Siemens] als FP). [München]ORG fehlt als FP. Richtig: FP = 2, \(P=\tfrac13\). Die FN-Liste ist korrekt.

**Bewertung.** Prüfprinzip: jede System-Spanne genau einmal · fehlende FP-Zählung benannt · korrigiertes P

## B6
**Kurzschlüssel.** \(D=(190,\ 130,\ 10)\), \(\sum D=330\). Typ-\(F_1\): PER \(160/190\approx0{,}8421\), LOC \(100/130\approx0{,}7692\), MISC \(0/10=0\). (a) Micro \(=(160+100+0)/330=26/33\approx0{,}7879\). (b) Macro \(\approx0{,}5371\). (c) \(w_{\mathrm{MISC}}=10/330=1/33\approx0{,}0303\) – nicht der Gold-Anteil \(7/162\approx0{,}0432\). Macro zeigt den Ausfall, weil MISC dort ein Drittel Gewicht hat.

**Ausführliche Lösung.** \(D=(190,\ 130,\ 10)\), \(\sum D=330\). Typ-\(F_1\): PER \(160/190\approx0{,}8421\), LOC \(100/130\approx0{,}7692\), MISC \(0/10=0\). (a) Micro \(=(160+100+0)/330=26/33\approx0{,}7879\). (b) Macro \(\approx0{,}5371\). (c) \(w_{\mathrm{MISC}}=10/330=1/33\approx0{,}0303\) – nicht der Gold-Anteil \(7/162\approx0{,}0432\). Macro zeigt den Ausfall, weil MISC dort ein Drittel Gewicht hat.

**Bewertung.** Micro (1 P.) · Macro (1 P.) · Gewicht über D_k statt Support (2 P.)

## F1
**Kurzschlüssel.** (a) Nach Viterbi: TP = 5, FP = 3, FN = 3, \(F_1=10/16=5/8\) (gierig: TP = 4, FP = 5, FN = 4, \(8/17\)). (b) 2 Grenzfehler: [Barack]PER statt [Barack Obama]PER und [Berlin .]LOC statt [Berlin]LOC. (c) Harte Übergangsregeln schließen nur ungültige Folgen aus; <code>B-LOC I-LOC</code> ist gültig. Nur bessere Emissionen (oder gelernte Übergangswerte, die „. “ als Fortsetzung bestrafen) ändern das.

**Ausführliche Lösung.** (a) Nach Viterbi: TP = 5, FP = 3, FN = 3, \(F_1=10/16=5/8\) (gierig: TP = 4, FP = 5, FN = 4, \(8/17\)). (b) 2 Grenzfehler: [Barack]PER statt [Barack Obama]PER und [Berlin .]LOC statt [Berlin]LOC. (c) Harte Übergangsregeln schließen nur ungültige Folgen aus; <code>B-LOC I-LOC</code> ist gültig. Nur bessere Emissionen (oder gelernte Übergangswerte, die „. “ als Fortsetzung bestrafen) ändern das.

**Bewertung.** F1 nach Viterbi · Grenzfehler gezählt · Begründung gültig/ungültig

## B7
**Kurzschlüssel.** Sei \(P\le R\) (Symmetrie). \(\tfrac{2PR}{P+R}\le 2P\iff 2PR\le 2P(P+R)\iff 0\le 2P^2\) – wahr. Markiert ein System alles, ist \(R\) nahe 1, \(P\) gleich dem Anteil der Entitätstoken; \(F_1\) bleibt unter dem Doppelten davon.

**Ausführliche Lösung.** Sei \(P\le R\) (Symmetrie). \(\tfrac{2PR}{P+R}\le 2P\iff 2PR\le 2P(P+R)\iff 0\le 2P^2\) – wahr. Markiert ein System alles, ist \(R\) nahe 1, \(P\) gleich dem Anteil der Entitätstoken; \(F_1\) bleibt unter dem Doppelten davon.

**Bewertung.** WLOG begründet · Äquivalenzumformung mit positivem Faktor · Interpretation

## S0
**Kurzschlüssel.** BILOU markiert das letzte Wort einer Mehrwortspanne (L-) und Einwortspannen (U-) explizit. Darstellbar sind dieselben Spannenmengen wie mit BIO; der Unterschied liegt im Lernsignal: Der Klassifikator muss Spannenenden direkt vorhersagen, statt sie implizit aus dem folgenden Label zu erschließen.

**Ausführliche Lösung.** BILOU markiert das letzte Wort einer Mehrwortspanne (L-) und Einwortspannen (U-) explizit. Darstellbar sind dieselben Spannenmengen wie mit BIO; der Unterschied liegt im Lernsignal: Der Klassifikator muss Spannenenden direkt vorhersagen, statt sie implizit aus dem folgenden Label zu erschließen.

**Bewertung.** richtige Option (1 P.) · Begründung: gleiche Ausdruckskraft, anderes Lernsignal (1 P.)

## S2
**Kurzschlüssel.** <code>O O B-CITY I-CITY O B-CITY</code>. „Boston“ bekommt B-CITY, weil es eine neue Spanne beginnt; I-CITY wäre gültig nur direkt nach einem CITY-Label.

**Ausführliche Lösung.** <code>O O B-CITY I-CITY O B-CITY</code>. „Boston“ bekommt B-CITY, weil es eine neue Spanne beginnt; I-CITY wäre gültig nur direkt nach einem CITY-Label.

**Bewertung.** Spannenanfänge mit B- (1 P.) · Fortsetzung mit I- (1 P.) · Rest O (1 P.)

## S3
**Kurzschlüssel.** <code>O O B-CITY L-CITY O U-CITY</code>. „New York“ ist eine Zweiwortspanne (B-, L-), „Boston“ eine Einwortspanne (U-).

**Ausführliche Lösung.** <code>O O B-CITY L-CITY O U-CITY</code>. „New York“ ist eine Zweiwortspanne (B-, L-), „Boston“ eine Einwortspanne (U-).

**Bewertung.** B/L für Mehrwortspanne (1 P.) · U für Einwortspanne (1 P.)

## S4
**Kurzschlüssel.** <code>start</code> wird nur bei <code>B-</code> gesetzt. Bei <code>O I-LOC I-LOC</code> bleibt <code>start=None</code>, die Ausgabe ist <code>[]</code>. <code>conlleval</code> liest dagegen ein <code>I-LOC</code> ohne Vorgänger als neue Spanne: [w₂ w₃]LOC. Dieselben Vorhersagen ergeben mit beiden Decodern verschiedene Recall-Werte – eine typische, schwer zu entdeckende Quelle nicht vergleichbarer Ergebnisse. Der Typ wird von diesem Code übrigens gar nicht ausgegeben.

**Ausführliche Lösung.** <code>start</code> wird nur bei <code>B-</code> gesetzt. Bei <code>O I-LOC I-LOC</code> bleibt <code>start=None</code>, die Ausgabe ist <code>[]</code>. <code>conlleval</code> liest dagegen ein <code>I-LOC</code> ohne Vorgänger als neue Spanne: [w₂ w₃]LOC. Dieselben Vorhersagen ergeben mit beiden Decodern verschiedene Recall-Werte – eine typische, schwer zu entdeckende Quelle nicht vergleichbarer Ergebnisse. Der Typ wird von diesem Code übrigens gar nicht ausgegeben.

**Bewertung.** Ausgabe [] (1 P.) · Unterschied zu conlleval (1 P.) · Folge für Vergleichbarkeit (1 P.)

## W1F
**Kurzschlüssel.** Ausgabe \(5\cdot(2\cdot100+1)=1\,005\). Summe \(60\,200+1\,005=61\,205\).

**Ausführliche Lösung.** Ausgabe \(5\cdot(2\cdot100+1)=1\,005\). Summe \(60\,200+1\,005=61\,205\).

**Bewertung.** Ausgabeschicht mit 2d_h Spalten (1 P.) · Summe (1 P.)

## R1
**Kurzschlüssel.** Anfang \(s=T\): \(h^{\leftarrow}_T=\tanh(W\prime\cdot0+U\prime e_T+b\prime)\) hängt nur von \(x_T\) ab. Schritt \(s+1\to s\): Nach Annahme ist \(h^{\leftarrow}_{s+1}=G_{s+1}(x_{s+1},\dots,x_T)\). Einsetzen: \(h^{\leftarrow}_s=\tanh\big(W\prime G_{s+1}(x_{s+1},\dots,x_T)+U\prime e_s+b\prime\big)=:G_s(x_s,\dots,x_T)\); kein \(x_r\) mit \(r&lt;s\) kommt vor. \(\square\)

**Ausführliche Lösung.** Anfang \(s=T\): \(h^{\leftarrow}_T=\tanh(W\prime\cdot0+U\prime e_T+b\prime)\) hängt nur von \(x_T\) ab. Schritt \(s+1\to s\): Nach Annahme ist \(h^{\leftarrow}_{s+1}=G_{s+1}(x_{s+1},\dots,x_T)\). Einsetzen: \(h^{\leftarrow}_s=\tanh\big(W\prime G_{s+1}(x_{s+1},\dots,x_T)+U\prime e_s+b\prime\big)=:G_s(x_s,\dots,x_T)\); kein \(x_r\) mit \(r&lt;s\) kommt vor. \(\square\)

**Bewertung.** Induktionsanfang mit Startzustand (1 P.) · Induktionsschritt sauber eingesetzt (2 P.) · Schlussfolgerung über fehlende linke Wörter (1 P.)

## T1
**Kurzschlüssel.** Das System liest \(h^{\rightarrow}_{6}\); nach Satz 1 hängt es von \(x_1,\dots,x_6\) ab, also Indizes 1, 2, 3, 4, 5, 6. Gegenüber einem reinen Vorwärts-Tagger gewinnt es zwei Wörter rechten Kontext, um den Preis von zwei Wörtern Latenz – der Kompromiss aus Abschnitt 5(a).

**Ausführliche Lösung.** Das System liest \(h^{\rightarrow}_{6}\); nach Satz 1 hängt es von \(x_1,\dots,x_6\) ab, also Indizes 1, 2, 3, 4, 5, 6. Gegenüber einem reinen Vorwärts-Tagger gewinnt es zwei Wörter rechten Kontext, um den Preis von zwei Wörtern Latenz – der Kompromiss aus Abschnitt 5(a).

**Bewertung.** Satz 1 auf t+k angewandt (1 P.) · Menge korrekt (1 P.) · Latenz-Kontext-Abwägung benannt (1 P.)

## AT0
**Kurzschlüssel.** Energien \(0{,}7071\) und \(0\); Gewichte \(0{,}6698\) und \(0{,}3302\); Ausgabe \((1{,}3395;\ 1{,}3210)\). Die Werte bestimmen, <em>was</em> gemischt wird, die Schlüssel, <em>wie stark</em>: \(q\) ist parallel zu \(k_1\), daher \(\alpha_1&gt;\alpha_2\), unabhängig von der Norm der Werte.

**Ausführliche Lösung.** Energien \(0{,}7071\) und \(0\); Gewichte \(0{,}6698\) und \(0{,}3302\); Ausgabe \((1{,}3395;\ 1{,}3210)\). Die Werte bestimmen, <em>was</em> gemischt wird, die Schlüssel, <em>wie stark</em>: \(q\) ist parallel zu \(k_1\), daher \(\alpha_1&gt;\alpha_2\), unabhängig von der Norm der Werte.

**Bewertung.** Energien · Softmax · gewichtete Summe · Rolle von Schlüssel vs. Wert

## AT2
**Kurzschlüssel.** \(q^\top k_1=2\cdot1+1\cdot0=2\), \(q^\top k_2=2\cdot0+1\cdot2=2\); nach Skalierung beide \(1{,}4142\). Gleiche Energien ergeben gleiche Gewichte: \(\alpha_1=\alpha_2=0{,}5\). \(o=0{,}5\,(1,0)+0{,}5\,(0,2)=(0{,}5;\ 1)\), erste Komponente \(0{,}5\). Gleich lange Projektionen bedeuten gleiche Aufmerksamkeit – auch wenn \(q\) nicht genau in eine der beiden Richtungen zeigt.

**Ausführliche Lösung.** \(q^\top k_1=2\cdot1+1\cdot0=2\), \(q^\top k_2=2\cdot0+1\cdot2=2\); nach Skalierung beide \(1{,}4142\). Gleiche Energien ergeben gleiche Gewichte: \(\alpha_1=\alpha_2=0{,}5\). \(o=0{,}5\,(1,0)+0{,}5\,(0,2)=(0{,}5;\ 1)\), erste Komponente \(0{,}5\). Gleich lange Projektionen bedeuten gleiche Aufmerksamkeit – auch wenn \(q\) nicht genau in eine der beiden Richtungen zeigt.

**Bewertung.** Skalarprodukte · Gewichte · Ausgabe · Deutung

## AT3
**Kurzschlüssel.** Für jedes \(i\): \(\mathbb E[q_ik_i]=\mathbb E[q_i]\mathbb E[k_i]=0\) (Unabhängigkeit). \(\operatorname{Var}(q_ik_i)=\mathbb E[q_i^2k_i^2]-0=\mathbb E[q_i^2]\mathbb E[k_i^2]=1\) (Unabhängigkeit, \(\mathbb E[q_i^2]=\operatorname{Var}q_i=1\) wegen Mittelwert 0). Die Summanden sind paarweise unkorreliert (verschiedene unabhängige Variablen), also addieren sich die Varianzen: \(\operatorname{Var}(q^\top k)=d\). \(\square\)

**Ausführliche Lösung.** Für jedes \(i\): \(\mathbb E[q_ik_i]=\mathbb E[q_i]\mathbb E[k_i]=0\) (Unabhängigkeit). \(\operatorname{Var}(q_ik_i)=\mathbb E[q_i^2k_i^2]-0=\mathbb E[q_i^2]\mathbb E[k_i^2]=1\) (Unabhängigkeit, \(\mathbb E[q_i^2]=\operatorname{Var}q_i=1\) wegen Mittelwert 0). Die Summanden sind paarweise unkorreliert (verschiedene unabhängige Variablen), also addieren sich die Varianzen: \(\operatorname{Var}(q^\top k)=d\). \(\square\)

**Bewertung.** Erwartungswert 0 (1 P.) · Varianz je Summand mit benannter Annahme (2 P.) · Additivität mit Begründung (1 P.)

## AT4
**Kurzschlüssel.** Je Projektionsart \(4\cdot128\cdot32=16\,384=128^2\), drei Arten: \(49\,152\). Dazu \(W_O\): \(16\,384\). Summe \(65\,536\). Die Aufteilung in Köpfe ändert die Zahl nicht; erst \(W_O\) kommt hinzu (Abschnitt 6).

**Ausführliche Lösung.** Je Projektionsart \(4\cdot128\cdot32=16\,384=128^2\), drei Arten: \(49\,152\). Dazu \(W_O\): \(16\,384\). Summe \(65\,536\). Die Aufteilung in Köpfe ändert die Zahl nicht; erst \(W_O\) kommt hinzu (Abschnitt 6).

**Bewertung.** Köpfe ändern Anzahl nicht (1 P.) · W_O gezählt (1 P.) · Summe (1 P.)

## PO2
**Kurzschlüssel.** \(\mathrm{POS}(5,0)=\sin(5)\approx-0{,}9589\), \(\mathrm{POS}(5,1)=\cos(5)\approx0{,}2837\). Beide Komponenten gehören zur schnellsten Frequenz \(\omega=1\); das Paar liegt auf dem Einheitskreis: \(0{,}9589^2+0{,}2837^2\approx1\).

**Ausführliche Lösung.** \(\mathrm{POS}(5,0)=\sin(5)\approx-0{,}9589\), \(\mathrm{POS}(5,1)=\cos(5)\approx0{,}2837\). Beide Komponenten gehören zur schnellsten Frequenz \(\omega=1\); das Paar liegt auf dem Einheitskreis: \(0{,}9589^2+0{,}2837^2\approx1\).

**Bewertung.** Exponent 0 bei d=0 und d=1 (1 P.) · Werte (1 P.) · Einheitskreis-Deutung (1 P.)

## PO3
**Kurzschlüssel.** \(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R(m\theta)^\top R(n\theta)k\). Drehmatrizen sind orthogonal mit \(R(\varphi)^\top=R(-\varphi)\), und Drehungen addieren sich: \(R(a)R(b)=R(a+b)\). Also \(q^\top R(-m\theta)R(n\theta)k=q^\top R((n-m)\theta)k\). \(\square\) Folge: Verschiebt man beide Positionen um denselben Betrag, bleibt die Ähnlichkeit gleich.

**Ausführliche Lösung.** \(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R(m\theta)^\top R(n\theta)k\). Drehmatrizen sind orthogonal mit \(R(\varphi)^\top=R(-\varphi)\), und Drehungen addieren sich: \(R(a)R(b)=R(a+b)\). Also \(q^\top R(-m\theta)R(n\theta)k=q^\top R((n-m)\theta)k\). \(\square\) Folge: Verschiebt man beide Positionen um denselben Betrag, bleibt die Ähnlichkeit gleich.

**Bewertung.** Transposition (1 P.) · Orthogonalität (1 P.) · Gruppeneigenschaft (1 P.) · Folgerung (1 P.)

## PO4
**Kurzschlüssel.** Gelernte Positionsvektoren sind eine Tabelle mit fester Länge: Für Positionen über 512 gibt es keinen Eintrag (Vorlesung: „limited length“). Sinus-Kodierungen sind für jede Position definiert, RoPE kodiert relative Abstände; ob ein Modell auf längere Folgen tatsächlich verallgemeinert, ist damit noch nicht garantiert.

**Ausführliche Lösung.** Gelernte Positionsvektoren sind eine Tabelle mit fester Länge: Für Positionen über 512 gibt es keinen Eintrag (Vorlesung: „limited length“). Sinus-Kodierungen sind für jede Position definiert, RoPE kodiert relative Abstände; ob ein Modell auf längere Folgen tatsächlich verallgemeinert, ist damit noch nicht garantiert.

**Bewertung.** fehlender Tabelleneintrag (1 P.) · Alternative benannt mit Einschränkung (1 P.)

## C0
**Kurzschlüssel.** \(\delta_1=(2;0;-\infty)\), \(\delta_2=(2{,}3;\ 3{,}0;\ 1{,}2)\), \(\delta_3=(3{,}0;\ 3{,}2;\ 4{,}5)\). Bester Pfad O B-LOC I-LOC mit Score 4,5. \(\delta_2(\text{I-LOC})\) kann nur aus B-LOC kommen: \(0+1{,}2=1{,}2\).

**Ausführliche Lösung.** \(\delta_1=(2;0;-\infty)\), \(\delta_2=(2{,}3;\ 3{,}0;\ 1{,}2)\), \(\delta_3=(3{,}0;\ 3{,}2;\ 4{,}5)\). Bester Pfad O B-LOC I-LOC mit Score 4,5. \(\delta_2(\text{I-LOC})\) kann nur aus B-LOC kommen: \(0+1{,}2=1{,}2\).

**Bewertung.** Startbedingung · Übergangsregel in Zeile 2 · Maximum je Zelle · Rückverfolgung

## C2
**Kurzschlüssel.** Forward: \(\alpha_1=(7{,}3891;\ 1;\ 0)\), \(\alpha_2=(11{,}324;\ 22{,}8038;\ 3{,}3201)\), \(\alpha_3=(37{,}448;\ 45{,}7391;\ 117{,}0794)\); \(Z=\sum\alpha_3\approx200{,}2664\) (13 gültige Pfade). \(p=e^{4{,}5}/200{,}2664\approx0{,}4495\). Der beste Pfad ist also der wahrscheinlichste, aber das Modell ist sich alles andere als sicher.

**Ausführliche Lösung.** Forward: \(\alpha_1=(7{,}3891;\ 1;\ 0)\), \(\alpha_2=(11{,}324;\ 22{,}8038;\ 3{,}3201)\), \(\alpha_3=(37{,}448;\ 45{,}7391;\ 117{,}0794)\); \(Z=\sum\alpha_3\approx200{,}2664\) (13 gültige Pfade). \(p=e^{4{,}5}/200{,}2664\approx0{,}4495\). Der beste Pfad ist also der wahrscheinlichste, aber das Modell ist sich alles andere als sicher.

**Bewertung.** Forward-Rekursion (2 P.) · Z (1 P.) · p (1 P.) · Deutung Score vs. Wahrscheinlichkeit (1 P.)

## C3
**Kurzschlüssel.** \(\log p=S-\log Z=4{,}5-\log 200{,}2664\approx4{,}5-5{,}2996=-0{,}7996\). Der Fehler: „global normiert“ bezieht sich auf die Wahrscheinlichkeit (9.2); der Score (9.1) ist eine unnormierte Summe. Ein Score kann beliebig groß sein, ein Log-Wahrscheinlichkeitswert ist immer \(\le0\).

**Ausführliche Lösung.** \(\log p=S-\log Z=4{,}5-\log 200{,}2664\approx4{,}5-5{,}2996=-0{,}7996\). Der Fehler: „global normiert“ bezieht sich auf die Wahrscheinlichkeit (9.2); der Score (9.1) ist eine unnormierte Summe. Ein Score kann beliebig groß sein, ein Log-Wahrscheinlichkeitswert ist immer \(\le0\).

**Bewertung.** Formel log p = S − log Z (2 P.) · Wert (1 P.) · Fehler benannt (1 P.)

## C4
**Kurzschlüssel.** <code>B-DRUG → I-DOSE</code> ist verboten. Viterbi wählt die beste <em>gültige</em> Folge; welche das ist (z. B. <code>B-DRUG B-DOSE I-DOSE</code> oder <code>B-DRUG I-DRUG I-DRUG</code>), entscheiden die Emissionswerte. Garantiert ist nur die Gültigkeit – wie in der Fallstudie.

**Ausführliche Lösung.** <code>B-DRUG → I-DOSE</code> ist verboten. Viterbi wählt die beste <em>gültige</em> Folge; welche das ist (z. B. <code>B-DRUG B-DOSE I-DOSE</code> oder <code>B-DRUG I-DRUG I-DRUG</code>), entscheiden die Emissionswerte. Garantiert ist nur die Gültigkeit – wie in der Fallstudie.

**Bewertung.** verbotener Übergang erkannt (1 P.) · nur Gültigkeit garantiert (1 P.)

## P0
**Kurzschlüssel.** \(1/P=4/3\), \(1/R=5/3\), Mittel \(3/2\), \(F_1=2/3\); Probe mit der Zählform \(12/18=2/3\). TN tritt nicht auf, weil beide Aufwände nur Ausgaben und Gold-Entitäten zählen.

**Ausführliche Lösung.** \(1/P=4/3\), \(1/R=5/3\), Mittel \(3/2\), \(F_1=2/3\); Probe mit der Zählform \(12/18=2/3\). TN tritt nicht auf, weil beide Aufwände nur Ausgaben und Gold-Entitäten zählen.

**Bewertung.** beide Aufwände · Mittel und Kehrwert · Probe

## P1
**Kurzschlüssel.** \(P=7/10=0{,}7\), \(R=7/14=0{,}5\), \(F_1=14/(14+3+7)=14/24=7/12\approx0{,}5833\) – unter dem arithmetischen Mittel \(0{,}6\).

**Ausführliche Lösung.** \(P=7/10=0{,}7\), \(R=7/14=0{,}5\), \(F_1=14/(14+3+7)=14/24=7/12\approx0{,}5833\) – unter dem arithmetischen Mittel \(0{,}6\).

**Bewertung.** P und R · F1 · Vergleich mit Mittel

## P2
**Kurzschlüssel.** \(F_2=\frac{5\cdot0{,}8\cdot0{,}5}{4\cdot0{,}8+0{,}5}=\frac{2}{3{,}7}\approx0{,}5405\). Kleiner als \(F_1\approx0{,}6154\), weil das schwache \(R\) stärker zählt – passend zur Anforderung „alle Namen finden“.

**Ausführliche Lösung.** \(F_2=\frac{5\cdot0{,}8\cdot0{,}5}{4\cdot0{,}8+0{,}5}=\frac{2}{3{,}7}\approx0{,}5405\). Kleiner als \(F_1\approx0{,}6154\), weil das schwache \(R\) stärker zählt – passend zur Anforderung „alle Namen finden“.

**Bewertung.** Formel mit β²=4 · Wert · Deutung

## P3
**Kurzschlüssel.** Sei \(P\le R\). \(\frac{2PR}{P+R}\ge P\iff 2PR\ge P(P+R)\) (Multiplikation mit \(P+R&gt;0\)) \(\iff PR\ge P^2\iff R\ge P\) (Division durch \(P&gt;0\)) – wahr. \(\square\)

**Ausführliche Lösung.** Sei \(P\le R\). \(\frac{2PR}{P+R}\ge P\iff 2PR\ge P(P+R)\) (Multiplikation mit \(P+R&gt;0\)) \(\iff PR\ge P^2\iff R\ge P\) (Division durch \(P&gt;0\)) – wahr. \(\square\)

**Bewertung.** WLOG (1 P.) · beide Umformungen mit Vorzeichenbegründung (2 P.)

## E1
**Kurzschlüssel.** (a) \((1+0{,}5+0)/3=1/2\). (b) \((1+0{,}5)/2=3/4\). Dieselben Vorhersagen ergeben je nach Konvention 0,5 oder 0,75. Deshalb gehört die Konvention in jeden Bericht; die Zählform über das ganze Korpus vermeidet das Problem.

**Ausführliche Lösung.** (a) \((1+0{,}5+0)/3=1/2\). (b) \((1+0{,}5)/2=3/4\). Dieselben Vorhersagen ergeben je nach Konvention 0,5 oder 0,75. Deshalb gehört die Konvention in jeden Bericht; die Zählform über das ganze Korpus vermeidet das Problem.

**Bewertung.** (a) · (b) · Folgerung

## L1
**Kurzschlüssel.** Phrasen: TP = 1 (Deutsche Bank), FP = 1 ([Frankfurt]LOC), FN = 1 ([Frankfurt am Main]LOC): \(2/4=1/2\). Token: TP = 3 (Deutsche, Bank, Frankfurt), FP = 0, FN = 2 (am, Main): \(6/8=3/4\).

**Ausführliche Lösung.** Phrasen: TP = 1 (Deutsche Bank), FP = 1 ([Frankfurt]LOC), FN = 1 ([Frankfurt am Main]LOC): \(2/4=1/2\). Token: TP = 3 (Deutsche, Bank, Frankfurt), FP = 0, FN = 2 (am, Main): \(6/8=3/4\).

**Bewertung.** Phrasen · Token · Grenzfehler doppelt gezählt

## M0
**Kurzschlüssel.** \(D=(100;80;70;15)\), Gewichte \(D_k/265\); \(D_kF_{1,k}=2\mathrm{TP}_k\) ergibt \(192/265\approx0{,}7245\) – identisch mit der gepoolten Zählform. MISC hat Gewicht \(15/265\approx0{,}0566\).

**Ausführliche Lösung.** \(D=(100;80;70;15)\), Gewichte \(D_k/265\); \(D_kF_{1,k}=2\mathrm{TP}_k\) ergibt \(192/265\approx0{,}7245\) – identisch mit der gepoolten Zählform. MISC hat Gewicht \(15/265\approx0{,}0566\).

**Bewertung.** D_k · Typ-F1 · Identität

## M1
**Kurzschlüssel.** Support \(100,\ 55,\ 7\) (Summe 162). \((100\cdot0{,}8421+55\cdot0{,}7692+7\cdot0)/162\approx0{,}7810\). Drei verschiedene Mittel derselben Zählungen: Micro \(0{,}7879\), support-gewichtet \(0{,}7810\), Macro \(0{,}5371\).

**Ausführliche Lösung.** Support \(100,\ 55,\ 7\) (Summe 162). \((100\cdot0{,}8421+55\cdot0{,}7692+7\cdot0)/162\approx0{,}7810\). Drei verschiedene Mittel derselben Zählungen: Micro \(0{,}7879\), support-gewichtet \(0{,}7810\), Macro \(0{,}5371\).

**Bewertung.** Support je Typ · Wert · Vergleich der drei Mittel

## M2
**Kurzschlüssel.** Macro-\(F_1\) gibt jedem Typ gleiches Gewicht, ein Ausfall der seltenen Klasse wird sichtbar; zusätzlich \(F_1\) je Typ. Micro wird von den 90 % häufigen Entitäten dominiert; Accuracy mit O ist durch die vielen O-Token fast immer hoch (Satz 7).

**Ausführliche Lösung.** Macro-\(F_1\) gibt jedem Typ gleiches Gewicht, ein Ausfall der seltenen Klasse wird sichtbar; zusätzlich \(F_1\) je Typ. Micro wird von den 90 % häufigen Entitäten dominiert; Accuracy mit O ist durch die vielen O-Token fast immer hoch (Satz 7).

**Bewertung.** Macro mit Begründung · warum nicht Micro/Accuracy

## AT5
**Kurzschlüssel.** \(w=(0{,}5904;\ 0{,}1037;\ 0{,}3059)\), \(o=(1{,}1343;\ 0{,}3763)\).

**Ausführliche Lösung.** Skalarprodukte \(1{,}2\), \(-1{,}26\), \(0{,}27\); nach Division durch \(\sqrt2\): \(0{,}8485\), \(-0{,}891\), \(0{,}1909\). Exponentialwerte \(2{,}3362\), \(0{,}4103\), \(1{,}2104\), Summe \(3{,}9568\). Gewichte \(0{,}5904\), \(0{,}1037\), \(0{,}3059\). Ausgabe \(o=(1{,}1343;\ 0{,}3763)\) – nahe der Ufer-Achse. <b>Geometrie:</b> \(q^\top k_j=\lVert q\rVert\pi_j\); \(k_{\text{Geld}}\) hat trotz großer Länge eine negative Projektion. <b>Kontrolle:</b> \(o\) liegt im Dreieck der Values (Satz 6.2).

**Bewertung.** Skalarprodukte (1 P.) · Skalierung (1 P.) · Softmax mit Probe (1 P.) · gewichtete Summe (1 P.) · Deutung über Projektion (1 P.)

## AT6
**Kurzschlüssel.** (a) Score \(s_j+c\) mit gleichem \(c=q^\top u/\sqrt{d_k}\); \(e^{c/T}\) kürzt sich. (b) \((\lambda q)^\top k_j/(\sqrt{d_k}T)=s_j/(T/\lambda)\).

**Ausführliche Lösung.** <b>(a)</b> Neue Keys \(k_j+u\). Score: \(q^\top(k_j+u)/\sqrt{d_k}=s_j+c\) mit \(c=q^\top u/\sqrt{d_k}\), <em>unabhängig von</em> \(j\). Softmax: \(e^{(s_j+c)/T}/\sum_le^{(s_l+c)/T}=e^{c/T}e^{s_j/T}/(e^{c/T}\sum_le^{s_l/T})=w_j\). <b>(b)</b> \((\lambda q)^\top k_j/(\sqrt{d_k}\,T)=\lambda s_j/T=s_j/(T/\lambda)\): exakt die Gewichte bei Temperatur \(T/\lambda\). <b>Gegenbeispiel</b> (Grenze der Aussage): Verschiebt man nur \(k_1\), ändert sich nur \(s_1\), und \(w_1\) steigt oder fällt mit \(q^\top u\). \(\square\)

**Bewertung.** c unabhängig von j erkannt (2 P.) · Kürzen korrekt (1 P.) · (b) mit Temperatur (1 P.) · Gegenbeispiel (1 P.)

## AT7
**Kurzschlüssel.** Unmöglich (Satz 6.2): \(o_1+o_2=w_1+w_2\le1\).

**Ausführliche Lösung.** Für jede Wahl von \(q\), Keys und \(T\) ist \(o=w_1(1,0)+w_2(0,1)+w_3(0,0)=(w_1,w_2)\) mit \(w_j&gt;0\) und \(w_1+w_2+w_3=1\). Also \(o_1+o_2=1-w_3&lt;1\). \((1,1)\) hat Koordinatensumme 2 – unerreichbar. Erreichbar wären nur Punkte im Inneren des Dreiecks (Satz 6.2), Randpunkte nur im Grenzwert. <b>Abhilfe in echten Modellen:</b> \(W_O\) (lineare Abbildung kann skalieren) und die Residualverbindung \(x+\operatorname{Att}(x)\).

**Bewertung.** Konvexkombination (2 P.) · konkrete Ungleichung (1 P.) · Abhilfe W_O/Residual (1 P.)

## AT8
**Kurzschlüssel.** \(w_1\approx0{,}6698\), \(\partial w_1/\partial s_1\approx0{,}2212\); ohne Skalierung kleiner.

**Ausführliche Lösung.** Skalarprodukte \(q^\top k_1=2\), \(q^\top k_2=1\); Scores \(1{,}4142\) und \(0{,}7071\), Abstand \(0{,}7071\). \(w_1=e^{1{,}4142}/(e^{1{,}4142}+e^{0{,}7071})=0{,}6698\). Ableitung \(w_1(1-w_1)=0{,}6698\cdot0{,}3302=0{,}2212\). Ohne Skalierung ist der Abstand \(1\): \(w_1\) wächst, \(w_1(1-w_1)\) sinkt. Allgemein ist \(w(1-w)\) bei \(w=0{,}5\) maximal (\(0{,}25\)) und geht gegen 0, wenn \(w\to1\): Sättigung bremst das Lernen (Lemma 6.4).

**Bewertung.** Scores mit Skalierung (1 P.) · w₁ (1 P.) · Ableitung (1 P.) · Richtung mit Begründung (1 P.)

## AT9
**Kurzschlüssel.** Gegenbeispiel (a); richtig ist Satz 6.3: \(q\perp(k_i-k_j)\) für alle Paare.

**Ausführliche Lösung.** Die Aussage verwechselt eine hinreichende mit einer notwendigen Bedingung. \(q=0\) reicht, ist aber nicht nötig: Bei \(q=(2,0)\) und Keys mit gleicher erster Komponente 1 sind alle Skalarprodukte \(2\) (die zweite Komponente wird mit 0 multipliziert), also alle Gewichte \(1/3\). Korrekt (Satz 6.3): gleichverteilt \(\Leftrightarrow\) \(q^\top(k_i-k_j)=0\) für alle \(i,j\). Geometrisch: alle Keys liegen in einer Hyperebene senkrecht zu \(q\).

**Bewertung.** hinreichend vs. notwendig (1 P.) · Gegenbeispiel geprüft (1 P.) · korrekte Bedingung (1 P.)
