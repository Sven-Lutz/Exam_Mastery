# Recherche-Nachweis: Neuronale Sequenzmarkierung

Automatisch aus `research_log.jsonl` erzeugt. Schnappschüsse liegen nur lokal (SHA-256 angegeben).

## Bedarf (2026-11-15): decoding
Validator: Quelle lafferty ohne URL/DOI. Verifizierte Fundstelle beschaffen, nichts erfinden.

**Prüfung** lafferty: https://repository.upenn.edu/cis_papers/159 → 626475 Bytes, SHA-256 `d55268fba74fb1a2…`, 2026-11-15T12:41:50+00:00
- ✓ „We present conditional random fields, a framework for building probabilistic models to segment and label sequence data“
- ✓ „can be biased towards states with few successor states“

**Entscheidung** lafferty: URL ergänzt – Seite abgerufen, Titel/Abstract-Passagen wörtlich gefunden; Penn-Postprint, ICML 2001 S. 282–289 laut Repositorium

## Bedarf (2026-11-15): position
Validator: Quelle su ohne URL/DOI. Verifizierte Fundstelle beschaffen, nichts erfinden.

**Prüfung** su: https://arxiv.org/abs/2104.09864 → 43899 Bytes, SHA-256 `4297c6176ca9bf10…`, 2026-11-15T12:41:50+00:00
- ✓ „RoFormer: Enhanced Transformer with Rotary Position Embedding“
- ✓ „encodes the absolute position with a rotation matrix and meanwhile incorporates the explicit relative position dependency in self-attention formulation“

**Entscheidung** su: URL ergänzt – Seite abgerufen, Titel/Abstract-Passagen wörtlich gefunden; Neurocomputing-DOI der Folie NICHT bestätigt, daher nicht eingetragen

## Verknüpfungen Quelle → Kompetenz → Produkte
- **spans** (Spannenkodierung (IO, BIO, BILOU)): Quellen kurs, ratinov, lample, conll; Produkte {"book": ["spannen", "ner"], "tasks": ["S1", "S0", "S2", "S3", "S4"], "cards": ["spans/io-not-injective", "spans/label-count", "spans/conlleval-i", "spans/encode-mini", "spans/bilou-evidence"], "lab": [{"lab": "spans", "item": "s5"}]}
- **birnn** (Abhängigkeitsbereich und BiRNN): Quellen kurs, schuster; Produkte {"book": ["tagger", "rnn", "birnn"], "tasks": ["G1", "W1", "B1", "B2", "W1F", "R1", "T1"], "cards": ["birnn/abhaengigkeit-vorwaerts", "birnn/washington", "birnn/definition", "birnn/latenz", "birnn/softmax-unabhaengig", "birnn/params", "birnn/error-wo"], "lab": [{"lab": "birnn", "item": "b1"}, {"lab": "birnn", "item": "b2"}, {"lab": "birnn", "item": "n-sat"}]}
- **attention** (Self-Attention): Quellen kurs, vaswani, jain, wiegreffe; Produkte {"book": ["attention", "architektur"], "tasks": ["AT1", "AT0", "AT2", "AT3", "AT4", "AT5", "AT6", "AT7", "AT8", "AT9"], "cards": ["attention/formel", "attention/gelernt", "attention/skalierung", "attention/sharpening", "attention/convex", "attention/burger", "attention/multihead", "attention/shift-invariance", "attention/length-temperature", "attention/uniform-condition", "attention/jacobian", "attention/hull-impossible"], "lab": [{"lab": "attention", "item": "a1"}, {"lab": "attention", "item": "a2"}, {"lab": "attention", "item": "a3"}, {"lab": "attention", "item": "a4"}, {"lab": "attention", "item": "a5"}, {"lab": "attention", "item": "a6"}, {"lab": "attention", "item": "c-impossible"}]}
- **position** (Positionsinformation): Quellen kurs, vaswani, su; Produkte {"book": ["position"], "tasks": ["PO1", "PO2", "PO3", "PO4"], "cards": ["position/permutation", "position/sinus-linear", "position/rope", "position/learned-nachteil"], "lab": [{"lab": "attention", "item": "a7"}, {"lab": "attention", "item": "c-order"}]}
- **decoding** (Labelabhängigkeiten und Viterbi): Quellen kurs, lafferty, andor, ratinov, huang, lample; Produkte {"book": ["struktur", "fallstudie"], "tasks": ["C1", "F1", "C0", "C2", "C3", "C4"], "cards": ["decoding/crf-score", "decoding/crf-prob", "decoding/forward-vs-viterbi", "decoding/prob-mini", "decoding/garantie", "decoding/label-vs-exposure", "decoding/greedy-evidence"], "lab": [{"lab": "crf", "item": "r1"}, {"lab": "crf", "item": "r2"}, {"lab": "crf", "item": "r4"}, {"lab": "crf", "item": "k-mm"}]}
- **prf** (Precision, Recall, F1): Quellen kurs; Produkte {"book": ["prf"], "tasks": ["B7", "P0", "P1", "P2", "P3"], "cards": ["prf/zaehlform", "prf/schranke", "prf/keine-tn", "prf/fbeta"], "lab": [{"lab": "spans", "item": "s1"}, {"lab": "spans", "item": "f-prec"}]}
- **prf-edge** (Grenzfälle mit Nenner 0): Quellen kurs, sklearn; Produkte {"book": ["prf"], "tasks": ["B3", "E1"], "cards": ["prf-edge/nichts-ausgegeben", "prf-edge/tp-null", "prf-edge/beide-leer"], "lab": [{"lab": "spans", "item": "s3"}]}
- **prf-level** (Phrasen- vs. Token-Zählung): Quellen kurs, conll, manning; Produkte {"book": ["einheit"], "tasks": ["B4", "B5", "L1"], "cards": ["prf-level/doppelt", "prf-level/rangfolge"], "lab": [{"lab": "spans", "item": "s2"}, {"lab": "spans", "item": "f-half"}]}
- **micro-macro** (Micro- und Macro-Mittelung): Quellen kurs, opitz; Produkte {"book": ["mittelung"], "tasks": ["B6", "M0", "M1", "M2"], "cards": ["micro-macro/gewicht", "micro-macro/error-support", "micro-macro/unterschied", "micro-macro/accuracy"], "lab": [{"lab": "spans", "item": "s4"}, {"lab": "spans", "item": "f-macro"}]}
