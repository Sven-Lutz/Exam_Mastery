# Tutor-Kontext: Neuronale Sequenzmarkierung

Modul `nlp-sequence-labeling` · Fach: nlp · erzeugt 2026-11-15

## Offizieller Rahmen
NER und Spannen · RNN, BiRNN, Self-Attention, Positionen · CRF und Viterbi · Precision, Recall, F1 · Fallstudie

Offizielle Kursquellen (definieren den Prüfungsstoff): Vorlesungsfolien NLP Kap. 09 (privat)

## Prüfung
Zwei Probeklausurformen A/B; offizielle Angaben zu Dauer und Hilfsmitteln liegen nicht vor.

## Notation
- Q, K, V: Zeilen = Token; Q = XW_Q usw.
- BIO: B-X Anfang, I-X innen, O außerhalb
- TP, FP, FN: Zählwerte auf Spannenebene (conlleval)

## Kompetenzen
### spans · Spannenkodierung (IO, BIO, BILOU) (Klausurkern)
Voraussetzungen: ext:BIO, BILOU, ext:BIO-Kodierung, ext:Kodierungsschemata IO, BIO, BILOU, ext:Spanne, Entitätstyp
- Ziel: Vorlesung PDF-S. 4–18; Lehrbuch SLP3 §9.5.2 S. 239; §18.3 S. 405
- Typische Fehlvorstellung: „Ungültige Labels werden von allen Decodern ignoriert.“
Lernprodukte: {"book": ["spannen", "ner"], "tasks": ["S1", "S0", "S2", "S3", "S4"], "cards": ["spans/io-not-injective", "spans/label-count", "spans/conlleval-i", "spans/encode-mini", "spans/bilou-evidence"], "lab": [{"lab": "spans", "item": "s5"}]}
Quellen: kurs, ratinov, lample, conll

### birnn · Abhängigkeitsbereich und BiRNN (Klausurkern)
Voraussetzungen: ext:BiRNN-Definition, ext:Matrixdimensionen eines RNN, ext:RNN-Rekursion, ext:Softmax je Position, ext:Verkettung [h→; h←], ext:Vorwärts-RNN; BiRNN
- Ziel: Vorlesung PDF-S. 24–29, 77–80; Lehrbuch SLP3 §14.4–14.4.2 S. 312–314
- Typische Fehlvorstellung: „Das Vorwärts-RNN sieht das nächste Wort“ – erst ab Position 2.
- Typische Fehlvorstellung: „Ein RNN hat globalen Kontext, also sieht jeder Zustand den ganzen Satz.“
Lernprodukte: {"book": ["tagger", "rnn", "birnn"], "tasks": ["G1", "W1", "B1", "B2", "W1F", "R1", "T1"], "cards": ["birnn/abhaengigkeit-vorwaerts", "birnn/washington", "birnn/definition", "birnn/latenz", "birnn/softmax-unabhaengig", "birnn/params", "birnn/error-wo"], "lab": [{"lab": "birnn", "item": "b1"}, {"lab": "birnn", "item": "b2"}, {"lab": "birnn", "item": "n-sat"}]}
Quellen: kurs, schuster

### attention · Self-Attention (Klausurkern)
Voraussetzungen: ext:Konvexkombination, ext:Projektionsmatrizen, ext:Self-Attention-Formel, ext:Skalarprodukt, Orthogonalität, ext:Skalarprodukt, Softmax, ext:Softmax, Kettenregel; Satz 3, ext:Softmax, Temperatur, ext:Softmax; Skalarprodukt, ext:Temperatur der Softmax, ext:Varianz, Unabhängigkeit, ext:gewichtete Summe
- Ziel: Vorlesung PDF-S. 31–58, 72–76; Lehrbuch SLP3 §7.1–7.3 S. 179–188
- Typische Fehlvorstellung: Mit T → 0 „erzwingen“: Das ergibt einen Value (eindeutiges Maximum) oder den Mittelwert gleichauf liegender Values – beides in der Hülle.
- Typische Fehlvorstellung: Mit kleiner Temperatur Punkte außerhalb erreichen wollen.
- Typische Fehlvorstellung: Nur einen Key verschieben – dann ändern sich die Gewichte sehr wohl.
- Typische Fehlvorstellung: Values in die Gewichte einrechnen – sie werden nur gemischt.
- Typische Fehlvorstellung: „Die Attention-Gewichte sind trainierte Parameter.“
- Typische Fehlvorstellung: „Kleines T ⇒ kleiner Gradient“ – falsch bei gleich großen Maxima.
- Typische Fehlvorstellung: „Nur bei \(q=0\)“ – das ist hinreichend, nicht notwendig.
- Typische Fehlvorstellung: „Nur die Richtung von q zählt“ – die Länge bestimmt die Schärfe.
- Typische Fehlvorstellung: „Skalierung normiert die Gewichte auf Summe 1“ – das tut die Softmax.
Lernprodukte: {"book": ["attention", "architektur"], "tasks": ["AT1", "AT0", "AT2", "AT3", "AT4", "AT5", "AT6", "AT7", "AT8", "AT9"], "cards": ["attention/formel", "attention/gelernt", "attention/skalierung", "attention/sharpening", "attention/convex", "attention/burger", "attention/multihead", "attention/shift-invariance", "attention/length-temperature", "attention/uniform-condition", "attention/jacobian", "attention/hull-impossible"], "lab": [{"lab": "attention", "item": "a1"}, {"lab": "attention", "item": "a2"}, {"lab": "attention", "item": "a3"}, {"lab": "attention", "item": "a4"}, {"lab": "attention", "item": "a5"}, {"lab": "attention", "item": "a6"}, {"lab": "attention", "item": "c-impossible"}]}
Quellen: kurs, vaswani, jain, wiegreffe

### position · Positionsinformation (Klausurkern)
Voraussetzungen: ext:Additionstheoreme, ext:Positionskodierung, ext:Rotationsmatrix, ext:Self-Attention-Formel; Permutationsmatrix
- Ziel: Vorlesung PDF-S. 60–70; Lehrbuch SLP3 §7.4 S. 191–193
- Typische Fehlvorstellung: „Invarianz“ statt Äquivarianz: Die Ausgaben wandern mit.
Lernprodukte: {"book": ["position"], "tasks": ["PO1", "PO2", "PO3", "PO4"], "cards": ["position/permutation", "position/sinus-linear", "position/rope", "position/learned-nachteil"], "lab": [{"lab": "attention", "item": "a7"}, {"lab": "attention", "item": "c-order"}]}
Quellen: kurs, vaswani, su

### decoding · Labelabhängigkeiten und Viterbi (Klausurkern)
Voraussetzungen: ext:BIO-Gültigkeit; Viterbi, ext:CRF-Score; Softmax über Folgen, ext:Emission, Übergang, ext:Partitionsfunktion Z, ext:Viterbi-Rekursion, ext:gierige Dekodierung, ext:lokale vs. globale Normierung
- Ziel: Vorlesung PDF-S. 82–85; Lehrbuch SLP3 §18.4.5–18.5 S. 411–419; §9.5.3 S. 239–241
- Typische Fehlvorstellung: „Der CRF-Score ist global normiert.“
Lernprodukte: {"book": ["struktur", "fallstudie"], "tasks": ["C1", "F1", "C0", "C2", "C3", "C4"], "cards": ["decoding/crf-score", "decoding/crf-prob", "decoding/forward-vs-viterbi", "decoding/prob-mini", "decoding/garantie", "decoding/label-vs-exposure", "decoding/greedy-evidence"], "lab": [{"lab": "crf", "item": "r1"}, {"lab": "crf", "item": "r2"}, {"lab": "crf", "item": "r4"}, {"lab": "crf", "item": "k-mm"}]}
Quellen: kurs, lafferty, andor, ratinov, huang, lample

### prf · Precision, Recall, F1 (Klausurkern)
Voraussetzungen: ext:F1-Formel, ext:Konfusionsmatrix, ext:TP, FP, FN, ext:harmonisches Mittel
- Ziel: Vorlesung PDF-S. 20–21; Lehrbuch SLP3 §4.9 S. 112–114
Lernprodukte: {"book": ["prf"], "tasks": ["B7", "P0", "P1", "P2", "P3"], "cards": ["prf/zaehlform", "prf/schranke", "prf/keine-tn", "prf/fbeta"], "lab": [{"lab": "spans", "item": "s1"}, {"lab": "spans", "item": "f-prec"}]}
Quellen: kurs

### prf-edge · Grenzfälle mit Nenner 0 (Vertiefung)
Voraussetzungen: ext:Zählform von F1
- Ziel: Vorlesung – (Vertiefung); Lehrbuch SLP3 §4.9; scikit-learn zero_division
Lernprodukte: {"book": ["prf"], "tasks": ["B3", "E1"], "cards": ["prf-edge/nichts-ausgegeben", "prf-edge/tp-null", "prf-edge/beide-leer"], "lab": [{"lab": "spans", "item": "s3"}]}
Quellen: kurs, sklearn

### prf-level · Phrasen- vs. Token-Zählung (Klausurkern)
Voraussetzungen: ext:Token- vs. Spannen-Zählung, ext:exakter Spannenvergleich
- Ziel: Vorlesung PDF-S. 21–22; Lehrbuch SLP3 §9.5.4 S. 241
Lernprodukte: {"book": ["einheit"], "tasks": ["B4", "B5", "L1"], "cards": ["prf-level/doppelt", "prf-level/rangfolge"], "lab": [{"lab": "spans", "item": "s2"}, {"lab": "spans", "item": "f-half"}]}
Quellen: kurs, conll, manning

### micro-macro · Micro- und Macro-Mittelung (Vertiefung)
Voraussetzungen: ext:F1 je Typ, ext:Micro-F1, ext:Micro-F1 als gewichtetes Mittel, ext:Micro-F1, Accuracy
- Ziel: Vorlesung – (Vertiefung); Lehrbuch SLP3 §4.9.1 S. 114–115
Lernprodukte: {"book": ["mittelung"], "tasks": ["B6", "M0", "M1", "M2"], "cards": ["micro-macro/gewicht", "micro-macro/error-support", "micro-macro/unterschied", "micro-macro/accuracy"], "lab": [{"lab": "spans", "item": "s4"}, {"lab": "spans", "item": "f-macro"}]}
Quellen: kurs, opitz

## Übungsaufgaben (ohne Lösungen; Schlüssel separat in answer_key.md)
- **S1** (spans, independent): (a) Wie viele Labels braucht BILOU für \(K=5\) Entitätstypen? (b) Welche Spannen liest <code>conlleval</code> aus der Folge <code>O I-LOC I-LOC B-LOC</code> über den Wörtern \(w_1\dots w_4\)?
- **G1** (birnn, guided): Berechnen Sie im Experiment für „Washington <b>state</b>“ den Vorwärtszustand \(h^{\rightarrow}_2=\tanh(0{,}5\,h^{\rightarrow}_1+e_2)\) mit \(h^{\rightarrow}_1=(0{,}7616;\,0)\) und \(e_2=(0,-1)\). Vier Nachkommastellen.
- **W1** (birnn, worked): BiRNN-Tagger für CoNLL-2003 (vier Typen PER, ORG, LOC, MISC; Vorlesung PDF-S. 11) in BIO-Kodierung, Einbettung \(d=100\), Zustand \(d_h=128\) je Richtung. Wie viele Parameter hat er ohne Einbettungsmatrix?
- **B1** (birnn, independent): BiRNN-Tagger mit drei Entitätstypen in BIO, Einbettung \(d=50\), Zustand \(d_h=64\) je Richtung. Wie viele Parameter ohne Einbettungsmatrix?
- **B2** (birnn, faded): Rückwärts-RNN des Experiments, \(h^{\leftarrow}_t=\tanh(0{,}8\,h^{\leftarrow}_{t+1}+e_t)\), \(h^{\leftarrow}_3=0\), Satz „Washington state“. Bestimmen Sie die zweite Komponente von \(h^{\leftarrow}_1\).
- **AT1** (attention, faded): Drei Token mit \(x_1=(1,0)\), \(x_2=(0,1)\), \(x_3=(1,1)\); \(W_Q=W_K=W_V=I\), \(d_k=2\). Berechnen Sie das Gewicht \(\alpha_{33}\), mit dem Token 3 auf sich selbst achtet, und die erste Komponente von \(o_3\).
- **PO1** (position, independent): (a) Ein Self-Attention-Modell ohne Positionskodierung verarbeitet „Marry kills John“ und „John kills Marry“. Was gilt für den Ausgabevektor von „John“? (b) RoPE mit \(\theta=0{,}5\), \(q=k=(1,0)\): Berechnen Sie die Ähnlichkeit \(\big(R(m\theta)q\big)^\top R(n\theta)k\) für \(m=2\), \(n=5\).
- **C1** (decoding, independent): Emissionswerte \(s_t(\ell)\) für „in New York“ mit Labels O, B-LOC, I-LOC: in (2; 0; 0,5), New (0,3; 1,0; 1,2), York (0; 0,2; 1,5). Übergänge: verboten sind Start→I-LOC und O→I-LOC, alle anderen 0. (a) Welche Folge wählt die gierige Dekodierung? (b) Welchen Score hat die beste gültige Folge?
- **B3** (prf-edge, independent): Ein Satz enthält 3 Gold-Entitäten; das System gibt keine aus. Bestimmen Sie \(F_1\) mit der Zählform und entscheiden Sie, ob \(P\) definiert ist.
- **B4** (prf-level, independent): Gold: <code>[Angela Merkel]PER besuchte gestern die [Siemens AG]ORG in [München]LOC .</code><br>System: <code>[Angela Merkel]PER besuchte gestern die [Siemens]ORG AG in [München]ORG .</code><br>Berechnen Sie \(F_1\) auf Phrasen- und auf Token-Ebene.
- **B5** (prf-level, error): Eine Kommilitonin wertet B4 auf Phrasen-Ebene so aus:<br>TP: <code>[Angela Merkel]PER</code> · FP: <code>[Siemens]ORG</code> · FN: <code>[Siemens AG]ORG</code>, <code>[München]LOC</code><br>und erhält \(P=\tfrac12\), \(R=\tfrac13\). Welche Aussage beschreibt ihren Fehler genau?
- **B6** (micro-macro, transfer): PER: TP 80, FP 10, FN 20; LOC: TP 50, FP 25, FN 5; MISC: TP 0, FP 3, FN 7. (a) Micro-\(F_1\), (b) Macro-\(F_1\), (c) das exakte Gewicht \(w_{\mathrm{MISC}}\) von MISC in Micro-\(F_1\) als gewichtetem Mittel der Typ-\(F_1\)-Werte.
- **F1** (decoding, transfer): Nutzen Sie die Fallstudie in Abschnitt 13 (gierige gegen Viterbi-Dekodierung). (a) Phrasen-\(F_1\) nach Viterbi. (b) Wie viele Grenzfehler bleiben nach Viterbi? (c) Warum repariert Viterbi den Fehler bei „Berlin .“ nicht?
- **B7** (prf, transfer): Zeigen Sie für \(P,R\in(0,1]\): \(F_1\le 2\min(P,R)\). Was folgt für ein System, das jedes Wort als Entität markiert?
- **S0** (spans, independent): BIO kann jede Spannenmenge eindeutig darstellen (Satz A). Welche zusätzliche Information liefert BILOU dem Klassifikator?
- **S2** (spans, independent): Satz: <code>Tickets nach New York und Boston</code> mit den Gold-Spannen [New York]CITY und [Boston]CITY. Geben Sie die BIO-Folge an (Labels durch Leerzeichen getrennt).
- **S3** (spans, independent): Gleicher Satz wie S2. Geben Sie die BILOU-Folge an.
- **S4** (spans, error): Ein Team dekodiert BIO so:<pre><code>def spans(tags):\n    out, start = [], None\n    for i, t in enumerate(tags + ["O"]):\n        if start is not None and not t.startswith("I-"):\n            out.append((start, i)); start = None\n        if t.startswith("B-"):\n            start = i\n    return out</code></pre>Was liefert der Code für <code>O I-LOC I-LOC</code>, und wie unterscheidet sich das von <code>conlleval</code>?
- **W1F** (birnn, faded): BiRNN-Tagger mit zwei Entitätstypen in BIO, \(d=200\), \(d_h=100\) je Richtung. Ergänzen Sie den fehlenden Schritt und die Summe.
- **R1** (birnn, proof): Beweisen Sie ohne Rückgriff auf Satz 1 per Induktion über \(s=T,T-1,\dots,1\): \(h^{\leftarrow}_s\) ist eine Funktion von \(x_s,\dots,x_T\).
- **T1** (birnn, transfer): Ein Diktiersystem darf das Label von Wort \(t\) erst ausgeben, wenn zwei weitere Wörter gesprochen sind (Vorausschau \(k=2\)). Es nutzt ein Vorwärts-RNN, das zum Zeitpunkt der Ausgabe \(h^{\rightarrow}_{t+2}\) liest. Von welchen Eingaben kann das Label für \(t=4\) in einem Satz mit \(T=10\) Wörtern abhängen?
- **AT0** (attention, worked): Anfrage \(q=(1,0)\), Schlüssel \(k_1=(1,0)\), \(k_2=(0,1)\), Werte \(v_1=(2,0)\), \(v_2=(0,4)\), \(d_k=2\). Berechnen Sie die Ausgabe.
- **AT2** (attention, independent): Anfrage \(q=(2,1)\), Schlüssel und Werte \(k_1=v_1=(1,0)\), \(k_2=v_2=(0,2)\), \(d_k=2\). Bestimmen Sie \(\alpha_1\) und die erste Komponente der Ausgabe \(o\).
- **AT3** (attention, proof): Zeigen Sie: Sind \(q_1,\dots,q_d,k_1,\dots,k_d\) unabhängig mit Erwartungswert 0 und Varianz 1, so hat \(q^\top k\) die Varianz \(d\). Welche Annahme benutzen Sie an welcher Stelle?
- **AT4** (attention, transfer): Ein Transformer-Attention-Block mit \(n=d=128\) und \(h=4\) Köpfen hat Projektionen \(W_Q,W_K,W_V\) (je Kopf \(128\times32\)) und eine Ausgabematrix \(W_O\in\mathbb R^{128\times128}\). Wie viele Gewichte (ohne Bias) hat er?
- **PO2** (position, independent): Mit \(d_{\text{model}}=4\): Berechnen Sie \(\mathrm{POS}(5,0)\) und \(\mathrm{POS}(5,1)\) (Bogenmaß, vier Nachkommastellen).
- **PO3** (position, proof): Zeigen Sie für 2D-Vektoren \(q,k\) und Drehmatrizen \(R(\varphi)\): \(\big(R(m\theta)q\big)^\top R(n\theta)k=q^\top R((n-m)\theta)k\). Welche zwei Eigenschaften von Drehungen benutzen Sie?
- **PO4** (position, transfer): Ein Tagger mit <em>gelernten</em> absoluten Positionsvektoren für Positionen 1–512 soll Dokumente mit 600 Wörtern markieren. Was ist das unmittelbare Problem?
- **C0** (decoding, worked): Emissionen wie in Abb. 9.1 („in New York“, Labels O, B-LOC, I-LOC; erlaubte Übergänge 0, verbotene \(-\infty\)). Füllen Sie die Viterbi-Tabelle \(\delta_t(\ell)\) und lesen Sie den besten Pfad ab.
- **C2** (decoding, independent): Gleiche Emissionen wie C1/Abb. 9.1. Berechnen Sie die Zustandssumme \(Z\) über alle gültigen Folgen und die Wahrscheinlichkeit \(p(y^\ast\mid x)\) des besten Pfades (vier Nachkommastellen).
- **C3** (decoding, error): Jemand schreibt: „Das CRF normiert global, also ist \(S(x,y^\ast)=4{,}5\) direkt \(\log p(y^\ast\mid x)\).“ Berechnen Sie das korrekte \(\log p(y^\ast\mid x)\) für C1/C2.
- **C4** (decoding, transfer): Ein Tagger für Arztbriefe hat die Typen DRUG und DOSE in BIO. Ein BiRNN gibt für „Ibuprofen 400 mg“ gierig <code>B-DRUG I-DOSE I-DOSE</code> aus. Was liefert Viterbi mit harten BIO-Regeln mindestens?
- **P0** (prf, worked): Ein System hat 6 Treffer, 2 falsche Alarme, 4 verpasste Entitäten. Leiten Sie \(F_1\) über den mittleren Aufwand her.
- **P1** (prf, independent): TP = 7, FP = 3, FN = 7. Berechnen Sie \(P\), \(R\) und \(F_1\) (Bruch oder vier Nachkommastellen).
- **P2** (prf, independent): Ein Anonymisierungssystem muss möglichst alle Personennamen finden. \(P=0{,}8\), \(R=0{,}5\). Berechnen Sie \(F_2\).
- **P3** (prf, proof): Zeigen Sie für \(P,R\in(0,1]\): \(F_1\ge\min(P,R)\). Wo nutzen Sie \(P,R&gt;0\)?
- **E1** (prf-edge, transfer): Drei Testsätze: Satz 1 hat \(F_1=1\), Satz 2 \(F_1=\tfrac12\), Satz 3 hat weder Gold noch Ausgaben. Berechnen Sie den Mittelwert über Sätze (a) mit <code>zero_division=0</code> und (b) mit <code>np.nan</code> (Satz fällt heraus).
- **L1** (prf-level, independent): Gold: <code>Die [Deutsche Bank]ORG sitzt in [Frankfurt am Main]LOC .</code><br>System: <code>Die [Deutsche Bank]ORG sitzt in [Frankfurt]LOC am Main .</code><br>Phrasen- und Token-\(F_1\)?
- **M0** (micro-macro, worked): PER: TP 45, FP 5, FN 5 · LOC: 30, 10, 10 · ORG: 20, 15, 15 · MISC: 1, 4, 9. Zeigen Sie, dass Micro-\(F_1\) das mit \(D_k\) gewichtete Mittel der Typ-\(F_1\) ist.
- **M1** (micro-macro, independent): Zählungen wie in B6 (PER 80/10/20, LOC 50/25/5, MISC 0/3/7). Berechnen Sie das support-gewichtete Macro-\(F_1\) (Gewicht \(\mathrm{TP}_k+\mathrm{FN}_k\)).
- **M2** (micro-macro, transfer): Ein Krankenhaus will überwachen, ob ein NER-System <em>seltene</em> Medikamentennamen zuverlässig erkennt. Häufige Typen (Datum, Person) machen 90 % der Entitäten aus. Welche Kennzahl berichten Sie zuerst?
- **AT5** (attention, worked): Query \(q=(0{,}9;\,-0{,}6)\), Keys \(k_{\text{Fluss}}=(1{,}6;\,0{,}4)\), \(k_{\text{Geld}}=(-0{,}4;\,1{,}5)\), \(k_{\text{der}}=(0{,}1;\,-0{,}3)\), Values \(v_{\text{Fluss}}=(1{,}8;\,0{,}2)\), \(v_{\text{Geld}}=(0{,}1;\,1{,}9)\), \(v_{\text{der}}=(0{,}2;\,0{,}2)\), \(d_k=2\), \(T=1\). Berechnen Sie Gewichte und Ausgabe.
- **AT6** (attention, proof): Beweisen Sie Satz 6.1: (a) Eine gemeinsame Verschiebung aller Keys um \(u\) ändert die Gewichte nicht. (b) \(\lambda q\) bei Temperatur \(T\) wirkt wie \(q\) bei \(T/\lambda\). Welcher Rechenschritt trägt (a)?
- **AT7** (attention, transfer): Values \(v_1=(1,0)\), \(v_2=(0,1)\), \(v_3=(0,0)\). Ein Kollege möchte mit einer einzigen Attention-Schicht (ohne \(W_O\), ohne Residualverbindung) die Ausgabe \(o=(1,1)\) erzeugen und sucht dafür Query und Temperatur. Was ist richtig?
- **AT8** (attention, independent): \(q=(1,1)\), Keys \(k_1=(2,0)\), \(k_2=(0,1)\), \(d_k=2\), \(T=1\). Berechnen Sie \(w_1\) und die Ableitung \(\partial w_1/\partial s_1=w_1(1-w_1)\) (Lemma 6.4). Wie ändert sich diese Ableitung, wenn man die Skalierung weglässt – größer oder kleiner?
- **AT9** (attention, error): Eine Kommilitonin behauptet: „Die Gewichte sind genau dann gleichverteilt, wenn \(q=0\).“ Welches Gegenbeispiel widerlegt das?

## Eigene, geprüfte Beispiele
- **N1** (attention): „Bank“ am Fluss (Startzustand des Labors) – w = (0,5904; 0,1037; 0,3059), o = (1,1343; 0,3763); gemeinsame Key-Verschiebung ändert nichts, einzelne schon.
- **N2** (attention): Softmax-Jacobi bei T → 0: eindeutig vs. Gleichstand – Mit eindeutigem Maximum geht J gegen 0, bei gleich großen Maxima divergiert J (Lemma 6.4).

## Geprüfte Quellen (nur diese zitieren)
- **kurs** [official, lecture, Zugriff: private_course_material] Vorlesungsfolien Natural Language Processing, Kap. 09 „Neural Sequence Labeling“, WS 2025/26 (private Kursunterlagen, nicht veröffentlicht). Seitenangaben „PDF-S.“ = Seite im PDF; die Fußzeile der Folie zeigt diese Zahl minus 1. 
  - siehe Zitat: Vorlesungsfolien Natural Language Processing, Kap. 09 „Neural Sequence Labeling“, WS 2025/26 (private Kursunterlagen, nicht veröffentlicht). Seitenangaben „PDF-S.“ = Seite im PDF; die Fußzeile der Folie zeigt diese Zahl minus 1.
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **slp3** [extension, textbook, Zugriff: section] Jurafsky, D.; Martin, J. H.: Speech and Language Processing, 3. Aufl., Entwurf Aug. 2026 (lokale Kopie des Nutzers). Gelesen und verwendet (gedruckte Seiten): §4.9–4.9.1 S. 112–115; §7.1–7.4 S. 179–193; §9.5.1–9.5.4 S. 238–241; §14.4–14.4.2 S. 312–314; §18.3 S. 405; §18.4.5–18.5 S. 411–419. https://web.stanford.edu/~jurafsky/slp3/
  - siehe Zitat: Jurafsky, D.; Martin, J. H.: Speech and Language Processing, 3. Aufl., Entwurf Aug. 2026 (lokale Kopie des Nutzers). Gelesen und verwendet (gedruckte Seiten): §4.9–4.9.1 S. 112–115; §7.1–7.4 S. 179–193; §9.5.1–9.5.4 S. 238–241; §14.4–14.4.2 S. 312–314; §18.3 S. 405; §18.4.5–18.5 S. 411–419.
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **andor** [extension, paper, Zugriff: abstract] Andor, D. et al. (2016): Globally Normalized Transition-Based Neural Networks. Proc. ACL 2016, 2442–2452. Verwendet: Abstract (S. 2442). 
  - siehe Zitat: Andor, D. et al. (2016): Globally Normalized Transition-Based Neural Networks. Proc. ACL 2016, 2442–2452. Verwendet: Abstract (S. 2442).
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **lample** [extension, paper, Zugriff: abstract] Lample, G. et al. (2016): Neural Architectures for Named Entity Recognition. Proc. NAACL-HLT 2016, 260–270. Verwendet: Abstract (S. 260), Tagging-Schema IOBES (S. 263). 
  - siehe Zitat: Lample, G. et al. (2016): Neural Architectures for Named Entity Recognition. Proc. NAACL-HLT 2016, 260–270. Verwendet: Abstract (S. 260), Tagging-Schema IOBES (S. 263).
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **ratinov** [extension, paper, Zugriff: section] Ratinov, L.; Roth, D. (2009): Design Challenges and Misconceptions in Named Entity Recognition. Proc. CoNLL-2009, 147–155. Verwendet: S. 148 (BILOU vs. BIO; gierige Dekodierung vergleichbar mit Viterbi), S. 150 (Tabelle 2, Schemavergleich). https://aclanthology.org/W09-1119/
  - siehe Zitat: Ratinov, L.; Roth, D. (2009): Design Challenges and Misconceptions in Named Entity Recognition. Proc. CoNLL-2009, 147–155. Verwendet: S. 148 (BILOU vs. BIO; gierige Dekodierung vergleichbar mit Viterbi), S. 150 (Tabelle 2, Schemavergleich).
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **vaswani** [extension, paper, Zugriff: section] Vaswani, A. et al. (2017): Attention Is All You Need. arXiv:1706.03762 (NeurIPS 2017). Verwendet: §3.2.1 mit Fußnote 1 (Skalierung, Varianz d_k), §3.5 (Positionskodierung, lineare Verschiebung). https://arxiv.org/abs/1706.03762
  - siehe Zitat: Vaswani, A. et al. (2017): Attention Is All You Need. arXiv:1706.03762 (NeurIPS 2017). Verwendet: §3.2.1 mit Fußnote 1 (Skalierung, Varianz d_k), §3.5 (Positionskodierung, lineare Verschiebung).
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **su** [extension, paper, Zugriff: section] Su, J. et al. (2024): RoFormer: Enhanced Transformer with Rotary Position Embedding. Neurocomputing 568 (in der Vorlesung PDF-S. 69 zitiert; Volltext nicht gelesen, nur die Rotationseigenschaft wird verwendet und hier selbst bewiesen). 
  - siehe Zitat: Su, J. et al. (2024): RoFormer: Enhanced Transformer with Rotary Position Embedding. Neurocomputing 568 (in der Vorlesung PDF-S. 69 zitiert; Volltext nicht gelesen, nur die Rotationseigenschaft wird verwendet und hier selbst bewiesen).
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **jain** [extension, paper, Zugriff: abstract] Jain, S.; Wallace, B. C. (2019): Attention is not Explanation. Proc. NAACL-HLT 2019, 3543–3556. Gelesen: Zusammenfassung. https://aclanthology.org/N19-1357/
  - siehe Zitat: Jain, S.; Wallace, B. C. (2019): Attention is not Explanation. Proc. NAACL-HLT 2019, 3543–3556. Gelesen: Zusammenfassung.
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit
- **wiegreffe** [extension, paper, Zugriff: abstract] Wiegreffe, S.; Pinter, Y. (2019): Attention is not not Explanation. Proc. EMNLP-IJCNLP 2019, 11–20. Gelesen: Zusammenfassung. https://aclanthology.org/D19-1002/
  - siehe Zitat: Wiegreffe, S.; Pinter, Y. (2019): Attention is not not Explanation. Proc. EMNLP-IJCNLP 2019, 11–20. Gelesen: Zusammenfassung.
  - Grenzen: Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md
  - Funktion: Beleg im Lehrbuch der NLP-Einheit

## Labore
- attention: Self-Attention, CRF/Viterbi, BiRNN, Spannen & F1 – Experimente zu Attention-Geometrie, Viterbi vs. Vorwärts, Abhängigkeitsbereich, Zählweisen

## Lernstand
Kein Lernstand erhoben. Beginne mit einer kurzen Diagnose; erfinde keinen Lernstand.
