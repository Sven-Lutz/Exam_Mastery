# Recherche-Nachweis: Entrepreneurship – Funding a Venture

Automatisch aus `research_log.jsonl` erzeugt. Schnappschüsse liegen nur lokal (SHA-256 angegeben).

## Bedarf (2026-11-15): vc
Lückenanalyse: Kernkompetenz „VC-Fondslogik und Potenzialanforderung“ hat keine geprüfte Ergänzungsquelle. Benötigt: belastbare Aussage zur Schiefe der Renditeverteilung von VC-Investitionen und zur Rolle seltener Ausreißer, die das Fondsbeispiel X2 fachlich verankert.

**Suche** – WebSearch (Agent-Sitzung, 2026-11-16): „Kerr Nanda Rhodes-Kropf 2014 Entrepreneurship as Experimentation venture capital returns distribution“; „venture capital returns power law fund economics“
- Kandidat: Kerr, Nanda, Rhodes-Kropf (2014), JEP 28(3) 25–48; offen: NBER w20358 und Harvard DASH
- Kandidat: Gompers (1995) – bereits zuvor nicht zugänglich (HTTP 403)

**Prüfung** knr-2014: https://www.nber.org/papers/w20358.pdf → 525099 Bytes, SHA-256 `ea777f3a8946de27…`, 2026-11-15T12:41:48+00:00
- ✓ „the probabilities of success are low, extremely skewed and unknowable until an investment is made“
- ✓ „the actual distribution of returns in such ventures has a low median value but very high variance“
- ✓ „venture capital investors make their returns on the one investment out of many that turns out to be a wild success“
- ✓ „The vast majority of venture capital investments, however, return less than the face value of the investment“
- ✓ „the majority of venture capital-backed firms fail“

**Entscheidung** knr-2014: aufgenommen (extension, full_text, used_for: claim, example) – alle fünf Passagen wörtlich im Volltext gefunden; Übersichtsartikel – Verteilungsaussagen stützen sich auf zitierte Studien (Scherer & Harhoff 2000; Hall & Woodward 2010), nicht auf eigene Daten; Google-Beispiel ist eine Fallanekdote (Sahlman 2010).

**Integration** knr-2014 → kc: vc, example: X2 (Fondslogik: Ausreißer tragen die Rendite), task: EN5 (neu: Median vs. Mittelwert), lab: runden/v4 (Begründung zitiert die Passage), tutor: tutor_context (Quelle mit Passagen)

## Verknüpfungen Quelle → Kompetenz → Produkte
- **formen** (Kapitalformen und Risikoklassen): Quellen kurs; Produkte {}
- **zyklus** (Lebens- und Finanzierungszyklus, passende Kapitalquelle): Quellen kurs, htgf; Produkte {}
- **vc** (VC-Fondslogik und Potenzialanforderung): Quellen kurs, knr-2014; Produkte {"lab": [{"lab": "runden", "item": "v4"}, {"lab": "runden", "item": "w-fund"}], "tasks": ["EN3", "EN5"]}
- **prozess** (Finanzierungsprozess, Tranchen, Vertragsrechte): Quellen kurs, kaplan-stromberg; Produkte {}
- **bewertung** (Pre-/Post-Money, Wandelinstrumente und Verwässerung): Quellen kurs, yc-safe; Produkte {"lab": [{"lab": "runden", "item": "v1"}, {"lab": "runden", "item": "v2"}, {"lab": "runden", "item": "v3"}, {"lab": "runden", "item": "w-imp"}], "tasks": ["EN1", "EN2", "EN4"]}
