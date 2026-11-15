# Recherche-Nachweis: Analysis 1 – Konvergenz von Folgen

Automatisch aus `research_log.jsonl` erzeugt. Schnappschüsse liegen nur lokal (SHA-256 angegeben).

## Bedarf (2026-11-15): konv, grenzw (Neuprüfung)
QC v6: Abdeckung darf nur zählen, wenn eine gelesene Passage die Kompetenz trägt. Für konv (Definition) und grenzw (Sandwich) fehlte eine KC-genaue Passage in Lebl.

**Suche** – Volltext Lebl v6.3 (bereits als offene Quelle identifiziert, 2026-11-15): „Definition convergence sequence“; „squeeze lemma“
- Kandidat: Lebl §2.1 Definition 2.1.2
- Kandidat: Lebl §2.2 Lemma 2.2.1

**Prüfung** lebl: https://www.jirka.org/ra/realanal.pdf → 1901622 Bytes, SHA-256 `9c204ae1f1ee1641…`, 2026-11-15T12:45:37+00:00
- ✓ „is said to converge to a number“
- ✓ „there exists an 𝑀 ∈ ℕ such that“
- ✓ „Lemma 2.2.1 (Squeeze lemma)“
- ✓ „Theorem 2.1.10 (Monotone convergence theorem)“
- ✓ „Theorem 2.3.8 (Bolzano–Weierstrass)“
- ✓ „is not a Cauchy sequence“
- ✓ „Theorem 7.6.2 (Contraction mapping principle or Banach fixed point theorem“
- ✓ „The words complete and contraction are necessary“
- ✓ „It is Newton's method“

**Entscheidung** lebl: Passagen KC-genau zugeordnet – alle Phrasen im Volltext (Version 6.3) gefunden

**Integration** lebl → konv: Def. 2.1.2 → AN1, Labor f1/g-minN, grenzw: Lemma 2.2.1 → Lehrbezug (keine Pilotaufgabe), monoton: Bsp. 2.2.8, Satz 2.1.10 → E1, AN2, Labor f4/g-fast, hp: Satz 2.3.8, cauchy: Bsp. 2.4.3 → AN3, kontraktion: Def. 7.6.1/Satz 7.6.2 → E2, AN4, Labor g-contr/g-xinv

## Verknüpfungen Quelle → Kompetenz → Produkte
- **konv** (ε-N-Konvergenz und ihre Verneinung): Quellen skript, lebl; Produkte {"lab": [{"lab": "folgen", "item": "f1"}, {"lab": "folgen", "item": "f3"}, {"lab": "folgen", "item": "g-noN"}], "tasks": ["AN1"]}
- **grenzw** (Grenzwertsätze und Sandwichkriterium): Quellen skript, lebl; Produkte {}
- **monoton** (Monotone Konvergenz und rekursive Folgen): Quellen skript, lebl; Produkte {"lab": [{"lab": "folgen", "item": "f4"}, {"lab": "folgen", "item": "g-fast"}], "tasks": ["AN2"]}
- **hp** (Teilfolgen, Häufungspunkte, Bolzano–Weierstraß): Quellen skript, lebl; Produkte {}
- **cauchy** (Cauchy-Kriterium und Vollständigkeit): Quellen skript, lebl; Produkte {"tasks": ["AN3"]}
- **kontraktion** (Kontraktionsbedingung und Fixpunkt): Quellen skript, lebl; Produkte {"lab": [{"lab": "folgen", "item": "f5"}, {"lab": "folgen", "item": "g-contr"}], "tasks": ["AN4"]}
