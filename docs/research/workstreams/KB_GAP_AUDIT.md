# R0 — Kritischer Audit der lernwissenschaftlichen Knowledge Base

Stand: 26.11.2026. **Forschungszwischenstand zur unabhängigen Begutachtung, keine Freigabe.** Ein einzelner Codex-Agent führte Recherche, Extraktion und Selbstkritik durch. Keine Subagents; keine unabhängige Zweitextraktion. Die im Charter geforderte unabhängige Kritik bleibt deshalb ausdrücklich offen; die aktuelle Ein-Agent-Anweisung hat Vorrang. R1–R9 wurden nicht begonnen.

Basis: PR #20, `research/learning-science-foundations-20261126`, Commit `3fdbc7d01ee45ecaf33bc17be5f2b1295d14d115`; eigener Branch `research/r0-evidence-audit-20261126`. PR #28 und RL-Pilot wurden nicht übernommen oder geändert. Diese Arbeit ergänzt drei Forschungsdateien; sie ersetzt keine bestehenden KB-Klassifikationen.

## 1. Ergebnis und Reichweite

Vollständig triagiert: **55 Quellen, 17 Prinzipien, 52 Claims, 7 Spezifikationen und 17 Zeilen der älteren Evidenzmatrix**. Die Zahl 54 im Forschungsauftrag ist veraltet: `kalyuga2007` ist zusätzlich vorhanden. Der aktuelle Claim-Bestand lautet 29 `abstract_checked`, 16 `metadata_only`, 7 `fulltext_checked`. Der Quellenbestand und der Claim-Lesestand sind verschiedene Größen.

Die lokale bibliografische Prüfung wurde für alle 55 Quellen gegen den vorhandenen Crossref/OpenLibrary/OpenAlex-Cache wiederholt: **55/55 nach vorhandenen Kriterien passend; 40 Abstracts verfügbar; 48/48 hinterlegte Abstract-Ausschnitte wiedergefunden**. Dies ist keine neue Online-Verifikation aller Referenzen und keine Aussage über ihre wissenschaftliche Tragfähigkeit. Der Prüfer akzeptiert einen Titelbestandteil und teilweise ±1 Jahr; bei ISBN setzt er `year_match=True`, ohne das Jahr zu prüfen. Vollständige Autorenlisten, bibliografische Detailfehler, Korrekturen und Retraktionen sind dadurch nicht zuverlässig geprüft.

`verification.json` zählt 78 Quellen (74 VERIFIED, 4 PRIMARY_TEXT_READ), weil es zusätzlich Fachregister umfasst. Seine vier Primärtexte sind nicht vier lernwissenschaftliche Volltextreviews. 55/54, 78/55 und die unterschiedlichen Statusachsen dürfen nicht vermischt werden. `carpenter2022`, `renkl2014`, `kapur2016` haben keinen direkten Claim-Verweis; sie bleiben als Quellen erhalten.

**Elf risikobasierte Deep Reviews** folgen in Abschnitt 5: zehn mit gezielt gelesenen Methodik-/Ergebnispassagen in zugänglichen Artikeltexten bzw. Autorenmanuskripten (darunter Brunmair/Richter als akzeptiertes Manuskript), eines (Kestin) an einer explizit bezeichneten Preprint-Version, während der veröffentlichte Volltext nicht erreichbar war. „Volltext geprüft“ heißt hier claimbezogene Passage plus Methodik/Grenzen geprüft, nicht jede Referenz oder jeder Rohdatensatz repliziert. Alle übrigen Claims haben eine individuelle Triage, keine vorgetäuschte Volltextprüfung. Keine neue Metaanalyse, keine erschöpfende systematische Literaturübersicht, keine PRISMA-Vollständigkeitsbehauptung.

## 2. Wichtigste Korrekturen an wissenschaftlichen Anforderungen

| Priorität | Fundstelle im Bestand | Problem | Erforderliche Anforderung, noch nicht implementiert |
|---|---|---|---|
| P0 | `ai_tutoring.engine_rules` AI-R1; Forschungsgrundlage | Auch „nur Schadensvermeidung“ ist eine ungeprüfte Wirksamkeitsbehauptung über Exam Mastery. Nichtsignifikanz ist keine Äquivalenz. | Nur „soll das Risiko reduzieren“; Schaden separat messen, vorab begründete Nichtunterlegenheitsgrenze, ausreichende Präzision. |
| P0 | `ai_tutoring.contradictions`; `tutor_hints.evidence_note` | „Design ist der Moderator“ behauptet einen kausalen Mechanismus aus verschiedenen Studien. | Paketwirkung, einzelne Komponente und Moderation trennen; Population, Inhalt, Vergleichsbedingung und Messzeitpunkt als Alternativerklärungen führen. |
| P0 | Evidenzmatrix `IMPLEMENTED`; `policy.kc_status` | Technische Ereignisse werden leicht als Kompetenznachweis gelesen. Zwei verschiedene Kalenderdaten können Minuten auseinanderliegen; lokale Ereignisse schließen externe Hilfe nicht aus. | Reale Zeitabstände, unbekannte Aufgaben, Hilfestatus und Bewertungsverfahren separat; keine validierte Mastery-Schwelle aus einer Kalenderregel. |
| P1 | rp.2 → RP-R1 | Cued-recall-Vorrang und Publikationsbias werden aus unbereinigten Moderatorvergleichen übergeneralisiert. | Sensitivitätsanalysen mitführen; Zieloperation statt universeller Abrufformat-Rangliste wählen. D2. |
| P1 | rp.3; tr.1 | Mittlerer Transfer ist keine Garantie für Beweiskonstruktion, neue Domänen oder eigenständiges Problemlösen. | Transferdimension, Testnähe und Erfolg ohne Hilfe separat vorab festlegen. D3. |
| P1 | interleaving `contradictions`, Forschungsgrundlage | Sachtexte werden teils als negativ statt uneindeutig/nichtsignifikant beschrieben. „Nur ähnliche Kategorien“ ist stärker als die Evidenz. | Negative Wortbefunde von unklaren Textbefunden unterscheiden; Kontextregel als vorläufige Produktentscheidung markieren. D5. |
| P1 | we.4 → WE-R2 | Einzelstudien-Effektgrößen sind kein universeller Algorithmus für einen Erste-Schritt-Test. | Diagnosevalidität, Fehlklassifikationen und Fading getrennt prüfen; keine Expertenklassifikation aus einem Item. D6. |
| P1 | fb.1/fb.2 → FB-R1 | Moderatorgruppen sind keine randomisierten Vergleiche der Feedbackkomponenten; Leistung ist nicht immer langfristiges Lernen. | Teilschritt-Feedback als zu prüfende Entscheidung; Outcome und Zeitpunkt verpflichtend. D7/D8. |
| P1 | cl.1/cl.2; Guided Mode | Reduzierte Anzeige oder subjektive Leichtigkeit belegen weder geringere lernirrelevante Belastung noch besseren Transfer. | Zielrelevante Denkarbeit bewahren; Belastung, Leistung und Lernen separat messen. D9. |
| P1 | `EVALUATION_PROTOCOL.md`; `evaluation.assign` | n≥30 pro Arm ist kein ausreichender Wirksamkeitsstandard. Hash-Parität garantiert weder exakte Balance noch verdeckte Zuteilung. | Fallzahl aus minimal relevantem Effekt/Präzision, Clusterung und Ausfallrate planen; Zuteilung unabhängig und manipulationsgeschützt organisieren. |
| P1 | as.2; sp.3 | Logische Taxonomievalidierung ist keine experimentelle Validierung jeder MC-Regel; modellbedingte Scheduler-Optimierung ist keine allgemeine Lerngarantie. | Validierungsart und Optimierungsziel explizit angeben; FSRS-Version und Lernoperation nicht aus einer historischen Modellarbeit ableiten. |

Diese Anforderungen sind Audit-Empfehlungen, keine Änderungen am Produktvertrag. Vier Produkte und Anki als einziger Scheduler bleiben Arbeitsgrundlage. Detaillierte Effekte und Quellen werden unten genau einmal extrahiert; die Matrix verweist dorthin.

## 3. Vollständiges Quellenregister

Legende: **B** = vorhandene bibliografische Cache-Evidenz erneut geprüft; **A** = Abstract verfügbar, noch keine Methodikprüfung; **F** = in diesem Sprint ausgewählte Volltextpassagen geprüft; **Fv** = Kestin nur als Preprint geprüft, veröffentlichte Fassung offen. F bezeichnet keine garantierte Version of Record; die konkret gelesene Fassung steht im Zugangsprotokoll. `alt` gibt den bisherigen Quellenzugriff wieder. Jeder Eintrag hat B; B bedeutet nicht frischen Online-Zugriff. Studiendesign ist zunächst das registrierte `kind`, bei Deep Reviews kritisch präzisiert. Nicht vertiefte Quellen bleiben zur Methodik/Population/kausalen Schlussfolgerung **offen**. DOI/ISBN sind Identitätsanker, kein Beleg, dass das Ziel jetzt zugänglich war.

| Quellen-ID / bibliografischer Anker | Design laut KB | Zugriff alt → R0 | Zugeordnete Claims / weiterer Bedarf |
|---|---|---|---|
| `roediger2006` — [Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. Psychological Science, 17(3), 249-255.](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | primary_experiment | abstract → B/A/F | rp.1, mc.2; D1 |
| `dunlosky2013` — [Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques. Psychological Science in the Public Interest, 14(1), 4-58.](https://doi.org/10.1177/1529100612453266) | narrative_review | abstract → B/A | rp.5; Volltext/Methodik offen |
| `rowland2014` — [Rowland, C. A. (2014). The effect of testing versus restudy on retention: A meta-analytic review of the testing effect. Psychological Bulletin, 140(6), 1432-1463.](https://doi.org/10.1037/a0037559) | meta_analysis | fulltext → B/A/F | rp.2; D2 |
| `adesope2017` — [Adesope, O. O., Trevisan, D. A., & Sundararajan, N. (2017). Rethinking the use of tests: A meta-analysis of practice testing. Review of Educational Research, 87(3), 659-701.](https://doi.org/10.3102/0034654316689306) | meta_analysis | abstract → B/A | rp.4; Volltext/Methodik offen |
| `pan2018` — [Pan, S. C., & Rickard, T. C. (2018). Transfer of test-enhanced learning: Meta-analytic review and synthesis. Psychological Bulletin, 144(7), 710-756.](https://doi.org/10.1037/bul0000151) | meta_analysis | abstract → B/A/F | rp.3; D3 |
| `carpenter2022` — [Carpenter, S. K., Pan, S. C., & Butler, A. C. (2022). The science of effective learning with spacing and retrieval practice. Nature Reviews Psychology, 1(9), 496-511.](https://doi.org/10.1038/s44159-022-00089-1) | narrative_review | metadata → B | Kein direkter Claim; Volltext/Methodik offen |
| `cepeda2006` — [Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. Psychological Bulletin, 132(3), 354-380.](https://doi.org/10.1037/0033-2909.132.3.354) | meta_analysis | abstract → B/A | sp.1; Volltext/Methodik offen |
| `cepeda2008` — [Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008). Spacing effects in learning: A temporal ridgeline of optimal retention. Psychological Science, 19(11), 1095-1102.](https://doi.org/10.1111/j.1467-9280.2008.02209.x) | primary_experiment | abstract → B/A/F | sp.2; D4 |
| `rawson2013` — [Rawson, K. A., Dunlosky, J., & Sciartelli, S. M. (2013). The power of successive relearning: Improving performance on course exams and long-term retention. Educational Psychology Review, 25(4), 523-548.](https://doi.org/10.1007/s10648-013-9240-4) | narrative_review | metadata → B | sp.4; Volltext/Methodik offen |
| `ye2022` — [Ye, J., Su, J., & Cao, Y. (2022). A stochastic shortest path algorithm for optimizing spaced repetition scheduling. Proceedings of KDD '22, 4381-4390.](https://doi.org/10.1145/3534678.3539081) | primary_modeling | abstract → B/A | sp.3; Volltext/Methodik offen |
| `rohrer2007` — [Rohrer, D., & Taylor, K. (2007). The shuffling of mathematics problems improves learning. Instructional Science, 35(6), 481-498.](https://doi.org/10.1007/s11251-007-9015-8) | primary_experiment | metadata → B | il.2; Volltext/Methodik offen |
| `brunmair2019` — [Brunmair, M., & Richter, T. (2019). Similarity matters: A meta-analysis of interleaved learning and its moderators. Psychological Bulletin, 145(11), 1029-1052.](https://doi.org/10.1037/bul0000209) | meta_analysis | fulltext → B/A/F | il.1; D5 |
| `sweller1988` — [Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. Cognitive Science, 12(2), 257-285.](https://doi.org/10.1207/s15516709cog1202_4) | primary_experiment | abstract → B/A/F | cl.2; D9 |
| `sweller2019` — [Sweller, J., van Merriënboer, J. J. G., & Paas, F. (2019). Cognitive architecture and instructional design: 20 years later. Educational Psychology Review, 31(2), 261-292.](https://doi.org/10.1007/s10648-019-09465-5) | narrative_review | abstract → B/A | cl.1; Volltext/Methodik offen |
| `kirschner2006` — [Kirschner, P. A., Sweller, J., & Clark, R. E. (2006). Why minimal guidance during instruction does not work. Educational Psychologist, 41(2), 75-86.](https://doi.org/10.1207/s15326985ep4102_1) | position_paper | abstract → B/A | pf.2; Volltext/Methodik offen |
| `atkinson2000` — [Atkinson, R. K., Derry, S. J., Renkl, A., & Wortham, D. (2000). Learning from examples: Instructional principles from the worked examples research. Review of Educational Research, 70(2), 181-214.](https://doi.org/10.3102/00346543070002181) | narrative_review | abstract → B/A | we.3; Volltext/Methodik offen |
| `renkl2003` — [Renkl, A., & Atkinson, R. K. (2003). Structuring the transition from example study to problem solving in cognitive skill acquisition: A cognitive load perspective. Educational Psychologist, 38(1), 15-22.](https://doi.org/10.1207/S15326985EP3801_3) | narrative_review | abstract → B/A | we.1, we.2; Volltext/Methodik offen |
| `renkl2014` — [Renkl, A. (2014). Toward an instructionally oriented theory of example-based learning. Cognitive Science, 38(1), 1-37.](https://doi.org/10.1111/cogs.12086) | narrative_review | abstract → B/A | Kein direkter Claim; Volltext/Methodik offen |
| `kalyuga2003` — [Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The expertise reversal effect. Educational Psychologist, 38(1), 23-31.](https://doi.org/10.1207/S15326985EP3801_4) | narrative_review | abstract → B/A | we.4; Volltext/Methodik offen |
| `barbieri2023` — [Barbieri, C. A., Miller-Cotto, D., Clerjuste, S. N., & Chawla, K. (2023). A meta-analysis of the worked examples effect on mathematics performance. Educational Psychology Review, 35(1), 11.](https://doi.org/10.1007/s10648-023-09745-1) | meta_analysis | metadata → B | we.5; Volltext/Methodik offen |
| `kapur2016` — [Kapur, M. (2016). Examining productive failure, productive success, unproductive failure, and unproductive success in learning. Educational Psychologist, 51(2), 289-299.](https://doi.org/10.1080/00461520.2016.1155457) | narrative_review | abstract → B/A | Kein direkter Claim; Volltext/Methodik offen |
| `sinha2021` — [Sinha, T., & Kapur, M. (2021). When problem solving followed by instruction works: Evidence for productive failure. Review of Educational Research, 91(5), 761-798.](https://doi.org/10.3102/00346543211019105) | meta_analysis | abstract → B/A | pf.1; Volltext/Methodik offen |
| `chi2014` — [Chi, M. T. H., & Wylie, R. (2014). The ICAP framework: Linking cognitive engagement to active learning outcomes. Educational Psychologist, 49(4), 219-243.](https://doi.org/10.1080/00461520.2014.965823) | theoretical_framework | abstract → B/A | se.3; Volltext/Methodik offen |
| `bisra2018` — [Bisra, K., Liu, Q., Nesbit, J. C., Salimi, F., & Winne, P. H. (2018). Inducing self-explanation: A meta-analysis. Educational Psychology Review, 30(3), 703-725.](https://doi.org/10.1007/s10648-018-9434-x) | meta_analysis | metadata → B | se.1; Volltext/Methodik offen |
| `fiorella2016` — [Fiorella, L., & Mayer, R. E. (2016). Eight ways to promote generative learning. Educational Psychology Review, 28(4), 717-741.](https://doi.org/10.1007/s10648-015-9348-9) | narrative_review | metadata → B | se.2; Volltext/Methodik offen |
| `mayer2020` — [Mayer, R. E. (2020). Multimedia Learning (3rd ed.). Cambridge University Press.](https://doi.org/10.1017/9781316941355) | book | abstract → B/A | mm.1; Volltext/Methodik offen |
| `ainsworth2006` — [Ainsworth, S. (2006). DeFT: A conceptual framework for considering learning with multiple representations. Learning and Instruction, 16(3), 183-198.](https://doi.org/10.1016/j.learninstruc.2006.03.001) | theoretical_framework | metadata → B | mm.2; Volltext/Methodik offen |
| `hattie2007` — [Hattie, J., & Timperley, H. (2007). The power of feedback. Review of Educational Research, 77(1), 81-112.](https://doi.org/10.3102/003465430298487) | narrative_review | abstract → B/A | fb.4; Volltext/Methodik offen |
| `kluger1996` — [Kluger, A. N., & DeNisi, A. (1996). The effects of feedback interventions on performance. Psychological Bulletin, 119(2), 254-284.](https://doi.org/10.1037/0033-2909.119.2.254) | meta_analysis | fulltext → B/A/F | fb.1; D7 |
| `shute2008` — [Shute, V. J. (2008). Focus on formative feedback. Review of Educational Research, 78(1), 153-189.](https://doi.org/10.3102/0034654307313795) | narrative_review | abstract → B/A | fb.3; Volltext/Methodik offen |
| `wisniewski2020` — [Wisniewski, B., Zierer, K., & Hattie, J. (2020). The power of feedback revisited: A meta-analysis of educational feedback research. Frontiers in Psychology, 10, 3087.](https://doi.org/10.3389/fpsyg.2019.03087) | meta_analysis | fulltext → B/A/F | fb.2; D8 |
| `black1998` — [Black, P., & Wiliam, D. (1998). Assessment and classroom learning. Assessment in Education, 5(1), 7-74.](https://doi.org/10.1080/0969595980050102) | narrative_review | abstract → B/A | as.4; Volltext/Methodik offen |
| `dunlosky2012` — [Dunlosky, J., & Rawson, K. A. (2012). Overconfidence produces underachievement: Inaccurate self evaluations undermine students' learning and retention. Learning and Instruction, 22(4), 271-280.](https://doi.org/10.1016/j.learninstruc.2011.08.003) | primary_experiment | metadata → B | mc.1; Volltext/Methodik offen |
| `barnett2002` — [Barnett, S. M., & Ceci, S. J. (2002). When and where do we apply what we learn? A taxonomy for far transfer. Psychological Bulletin, 128(4), 612-637.](https://doi.org/10.1037/0033-2909.128.4.612) | theoretical_framework | abstract → B/A | tr.1; Volltext/Methodik offen |
| `bjork1994` — [Bjork, R. A. (1994). Memory and metamemory considerations in the training of human beings. In J. Metcalfe & A. Shimamura (Eds.), Metacognition: Knowing about knowing (pp. 185-205). MIT Press.](https://openlibrary.org/isbn/9780262132985) | book_chapter | metadata → B | mc.3; Volltext/Methodik offen |
| `pashler2008` — [Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008). Learning styles: Concepts and evidence. Psychological Science in the Public Interest, 9(3), 105-119.](https://doi.org/10.1111/j.1539-6053.2009.01038.x) | narrative_review | abstract → B/A | ls.1; Volltext/Methodik offen |
| `corbett1994` — [Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge. User Modeling and User-Adapted Interaction, 4(4), 253-278.](https://doi.org/10.1007/BF01099821) | primary_modeling | metadata → B | its.6; Volltext/Methodik offen |
| `anderson1995` — [Anderson, J. R., Corbett, A. T., Koedinger, K. R., & Pelletier, R. (1995). Cognitive tutors: Lessons learned. Journal of the Learning Sciences, 4(2), 167-207.](https://doi.org/10.1207/s15327809jls0402_2) | narrative_review | abstract → B/A | its.4; Volltext/Methodik offen |
| `koedinger2012` — [Koedinger, K. R., Corbett, A. T., & Perfetti, C. (2012). The Knowledge-Learning-Instruction framework. Cognitive Science, 36(5), 757-798.](https://doi.org/10.1111/j.1551-6709.2012.01245.x) | theoretical_framework | abstract → B/A | its.7; Volltext/Methodik offen |
| `pelanek2017` — [Pelánek, R. (2017). Bayesian knowledge tracing, logistic models, and beyond: An overview of learner modeling techniques. User Modeling and User-Adapted Interaction, 27(3-5), 313-350.](https://doi.org/10.1007/s11257-017-9193-2) | narrative_review | metadata → B | its.6; Volltext/Methodik offen |
| `vanlehn2011` — [VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. Educational Psychologist, 46(4), 197-221.](https://doi.org/10.1080/00461520.2011.611369) | meta_analysis | abstract → B/A | its.1; Volltext/Methodik offen |
| `ma2014` — [Ma, W., Adesope, O. O., Nesbit, J. C., & Liu, Q. (2014). Intelligent tutoring systems and learning outcomes: A meta-analysis. Journal of Educational Psychology, 106(4), 901-918.](https://doi.org/10.1037/a0037123) | meta_analysis | abstract → B/A | its.2; Volltext/Methodik offen |
| `kulik2016` — [Kulik, J. A., & Fletcher, J. D. (2016). Effectiveness of intelligent tutoring systems: A meta-analytic review. Review of Educational Research, 86(1), 42-78.](https://doi.org/10.3102/0034654315581420) | meta_analysis | abstract → B/A | its.3; Volltext/Methodik offen |
| `aleven2016` — [Aleven, V., Roll, I., McLaren, B. M., & Koedinger, K. R. (2016). Help helps, but only so much: Research on help seeking with intelligent tutoring systems. International Journal of Artificial Intelligence in Education, 26(1), 205-223.](https://doi.org/10.1007/s40593-015-0089-1) | narrative_review | abstract → B/A | its.5; Volltext/Methodik offen |
| `bastani2025` — [Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakcı, Ö., & Mariman, R. (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. PNAS, 122(26), e2422633122.](https://doi.org/10.1073/pnas.2422633122) | primary_rct | fulltext → B/A/F | ai.1; D10 |
| `kestin2025` — [Kestin, G., Miller, K., Klales, A., Milbourne, T., & Ponti, G. (2025). AI tutoring outperforms in-class active learning: An RCT introducing a novel research-based design in an authentic educational setting. Scientific Reports, 15, 17458.](https://doi.org/10.1038/s41598-025-97652-6) | primary_rct | fulltext → B/A/Fv | ai.2; D11 (Fv, 2024 v1) |
| `biggs1996` — [Biggs, J. (1996). Enhancing teaching through constructive alignment. Higher Education, 32(3), 347-364.](https://doi.org/10.1007/BF00138871) | theoretical_framework | metadata → B | as.1; Volltext/Methodik offen |
| `haladyna2002` — [Haladyna, T. M., Downing, S. M., & Rodriguez, M. C. (2002). A review of multiple-choice item-writing guidelines for classroom assessment. Applied Measurement in Education, 15(3), 309-333.](https://doi.org/10.1207/S15324818AME1503_5) | narrative_review | abstract → B/A | as.2; Volltext/Methodik offen |
| `krathwohl2002` — [Krathwohl, D. R. (2002). A revision of Bloom's taxonomy: An overview. Theory Into Practice, 41(4), 212-218.](https://doi.org/10.1207/s15430421tip4104_2) | theoretical_framework | abstract → B/A | as.3; Volltext/Methodik offen |
| `dehaene2020` — [Dehaene, S. (2020). How We Learn: Why Brains Learn Better Than Any Machine... for Now. Viking.](https://openlibrary.org/isbn/9780525559887) | popular_science | metadata → B | ps.1; Volltext/Methodik offen |
| `carey2014` — [Carey, B. (2014). How We Learn: The Surprising Truth About When, Where, and Why It Happens. Random House.](https://openlibrary.org/isbn/9780812993882) | popular_science | metadata → B | ps.2; Volltext/Methodik offen |
| `brod2021` — [Brod, G. (2021). Predicting as a learning strategy. Psychonomic Bulletin & Review, 28(6), 1839-1847.](https://doi.org/10.3758/s13423-021-01904-1) | narrative_review | abstract → B/A | pr.1; Volltext/Methodik offen |
| `butterfield2001` — [Butterfield, B., & Metcalfe, J. (2001). Errors committed with high confidence are hypercorrected. Journal of Experimental Psychology: Learning, Memory, and Cognition, 27(6), 1491-1494.](https://doi.org/10.1037/0278-7393.27.6.1491) | primary_experiment | abstract → B/A | pr.2; Volltext/Methodik offen |
| `dejong1998` — [de Jong, T., & van Joolingen, W. R. (1998). Scientific discovery learning with computer simulations of conceptual domains. Review of Educational Research, 68(2), 179-201.](https://doi.org/10.3102/00346543068002179) | narrative_review | abstract → B/A | pr.3; Volltext/Methodik offen |
| `kalyuga2007` — [Kalyuga, S. (2007). Expertise reversal effect and its implications for learner-tailored instruction. Educational Psychology Review, 19(4), 509-539.](https://doi.org/10.1007/s10648-007-9054-3) | review | fulltext → B/F | we.4; D6 |

## 4. Vollständige Claim-Traceability

Die folgenden 52 Zeilen sind eine relationale Matrix: Quellen-ID → bibliografischer Anker/Design in §3; D1–D11 → Population, Comparator, Zeitpunkt, Effekt und Unsicherheit in §5; T1–T17 → genaue Implementierungsregel und technische Fundstelle in §6. So bleibt jede Zeile vollständig rückverfolgbar, ohne Effekte mehrfach abzuschreiben. **Nicht ermittelt** ist eine explizite Evidenzlücke, keine Nullwirkung. Nicht vertiefte Abstract-Aussagen haben keine neue methodische oder kausale Freigabe.

Status alt ist der übernommene **Prinzipstatus**, keine eigenständige Bewertung jedes Claims: ES=EMPIRICAL_STRONG, EC=EMPIRICAL_CONDITIONAL, TM=THEORETICAL_MODEL, RJ=REJECTED. Basis alt: A=abstract_checked, M=metadata_only, F=fulltext_checked. R0: **K**=kontextabhängiger empirischer Befund, **T**=Theorie/Rahmen, **O**=Volltext/Methodik offen, **P**=Produktableitung unvalidiert; mehrere gelten gleichzeitig. Risiko **H/M/L** bezeichnet Auswirkungen einer Fehlanwendung, keine numerische Evidenzsicherheit. Für keine Zeile existiert eine Exam-Mastery-Lernwirksamkeitsprüfung.

| Claim: Aussagekern | Quelle(n); Status/Basis alt | Population, Operation → Outcome / Effektzugriff | R0: Bedingungen, Übergriff, Empfehlung; Risiko | Regel-/Technikpfad |
|---|---|---|---|---|
| `rp.1` Abruf vs. Wiederlesen | roediger2006; ES/A | D1: Studierende; Textabruf → verzögertes Behalten | K; keine generelle Überlegenheit in unmittelbaren Tests; H | T1 |
| `rp.2` Moderatorwerte des Testeffekts | rowland2014; ES/F | D2: laborlastig; Abrufformate → Retention | K/P; keine kausale Format-Rangliste; H | T1 |
| `rp.3` Transfer nach Testen | pan2018; ES/A | D3: experimentelle Stichproben; Abruf → geänderter Test | K; Problemlösen nicht pauschal bestätigt; H | T1 |
| `rp.4` Tests allen Alternativen überlegen | adesope2017; ES/A | Synthese; genaue Population offen; Testen → Lernleistung; nur Abstract | O/K; Mittelwerte der untersuchten Vergleiche, kein Allquantor über Lernmethoden; H | T1 |
| `rp.5` High-/low-utility-Kategorien | dunlosky2013; ES/M | Review; keine einzelne Population; Lerntechniken → Nutzenklassifikation | O; Kategorien mit Bewertungskriterien und Grenzen nachlesen, keine universelle Rangliste; M | T1 |
| `sp.1` Optimaler Abstand wächst | cepeda2006; ES/A | Meta-Analyse; genaue Population offen; verteiltes Üben → Retention; Abstract | O/K; Intervallabhängigkeit plausibel, kein universeller individueller Zeitplan; H | T2 |
| `sp.2` Prozentuale optimale Abstände | cepeda2008; ES/A | D4: Online-Erwachsene; Faktenabruf → Retention | K/P; keine Übertragung der Prozentwerte auf Beweise oder FSRS-Konfiguration; H | T2 |
| `sp.3` Scheduler optimieren Lernlogs | ye2022; ES/A | Modellarbeit; MaiMemo-Gedächtnislogs laut Abstract; Wiederholung → Modellkosten | O/T; Garantie nur unter Modellannahmen; keine allgemeine FSRS-Wirksamkeit; H | T2 |
| `sp.4` Successive Relearning | rawson2013; ES/M | Review; Population offen; Abruf bis Kriterium → Prüfung/Langzeitbehalten | O; Kriterium, Sitzungszahl und Kursdaten am Volltext prüfen; M | T2 |
| `il.1` Interleaving nach Material | brunmair2019; EC/F | D5: verschiedene Stichproben; Kategorien unterscheiden → Testleistung | K; Text-null und Wort-negativ getrennt; H | T3 |
| `il.2` Mathematik: Methodenwahl | rohrer2007; EC/M | Experiment; genaue Population offen; gemischte Aufgaben → spätere Leistung | O; Methodenwahl als Mechanismus nicht allein aus Gruppenunterschied beweisen; M | T3 |
| `we.1` Beispiele früh, Probleme später | renkl2003; EC/A | Review; Population offen; Prozedurerwerb → Lösungsleistung | O/K; Aufgaben-/Vorwissensabhängigkeit, kein fixes Stufengesetz; H | T4 |
| `we.2` Schrittweises Fading | renkl2003; EC/A | Review; Population offen; Beispielergänzung → selbstständiges Lösen | O/P; Beschreibung eines Designs, noch keine optimale Schrittzahl; M | T4 |
| `we.3` Merkmale guter Beispiele | atkinson2000; EC/A | Review; Population offen; Beispielstudium → Lernen | O/P; Merkmalsbündel, keinen Effekt jeder Einzelregel behaupten; M | T4 |
| `we.4` Expertise Reversal und Diagnose | kalyuga2007, kalyuga2003; EC/F | D6: Review technischer Lernaufgaben; Hilfen → Wissenszuwachs | K/P; Primärstudien nicht direkt nachgeprüft, Diagnosegrenze unkalibriert; H | T4 |
| `we.5` Mathematik-Worked-Example-Mittelwert | barbieri2023; EC/M | Meta-Analyse; Population/Effekt unextrahiert; Beispiele → Mathematikleistung | O; keine Zahl ergänzen, Volltext beschaffen; H | T4 |
| `pf.1` Problemlösen vor Instruktion | sinha2021; EC/A | 53 Studien/166 Vergleiche laut Abstract; PS-I → Lernen; g=0.36 [0.20;0.51] | O/K; jüngere Lernende/domänenallgemeine Ziele Gegenrichtung; prozeduraler Teil nicht durch gespeicherten Ausschnitt belegt; H | T5 |
| `pf.2` Anleitung für Novizen | kirschner2006; EC/A | Positionspapier, keine einzelne Population; Anleitung → Lernen | T/O; kein unabhängiger kausaler Gesamtnachweis; PF nicht mit ungelenktem Entdecken gleichsetzen; H | T5 |
| `cl.1` Arbeitsgedächtnis und Schemata | sweller2019; TM/A | Narrativer Review; kognitive Architektur → theoretische Erklärung | T; Schemata heben nicht beliebige Kapazitätsgrenzen auf; keine Neurogarantie; H | T6 |
| `cl.2` Means-Ends-Suche bindet Kapazität | sweller1988; TM/A | D9: 24 Jugendliche; Trigonometrie/Doppelaufgabe → Reproduktion | T/K; nicht weniger Denken generell empfehlen; H | T6 |
| `pr.1` Vorhersage verändert Feedbackverarbeitung | brod2021; EC/A | Review; Population offen; Vorhersage → Verarbeitung/Lernen | O/T; Mechanismus und beobachteter Effekt separat; M | T7 |
| `pr.2` Hyperkorrektur sicherer Fehler | butterfield2001; EC/A | Experiment; Population offen; Konfidenz/Fehler → Retestkorrektur | O/K; Konfidenzbeziehung kein Effekt des verpflichtenden Abfragens; H | T7 |
| `pr.3` Simulation braucht Unterstützung | dejong1998; EC/A | Review; Population offen; Experimentplanung → Lernprobleme | O/P; Reglerbedienung kein Experimentierkompetenznachweis; M | T7 |
| `mm.1` Multimedia-Prinzipien | mayer2020; EC/A | Buch; Population pro Studie offen; Darstellung → Verarbeitung | O/P; Prinzipienverzeichnis nicht Effektbeleg für jede Grafik; M | T8 |
| `mm.2` Repräsentationen verknüpfen | ainsworth2006; EC/M | Rahmenmodell; keine einzelne Population; Übersetzung → Verstehen | T/O; „nur wenn“ ist stärkere Notwendigkeitsbehauptung als Modellrahmen; M | T8 |
| `se.1` Angeleitete Selbsterklärung | bisra2018; EC/M | Meta-Analyse; Population/Effekt offen; Erklärung → Lernen | O; Effekt und Moderatorbedingungen zuerst extrahieren; M | T9 |
| `se.2` Generative Strategien wirken | fiorella2016; EC/M | Review; Population offen; verschiedene Operationen → verschiedene Outcomes | O/P; „richtig angeleitet“ operationalisieren, nicht unfalsifizierbar lassen; M | T9 |
| `se.3` ICAP-Rangfolge | chi2014; EC/A | Theorierahmen; Interaktionsqualität → Lernhypothese | T; Freitext oder Dialog allein erfüllt konstruktiv/interaktiv nicht; H | T9 |
| `fb.1` Feedback-Mittelwert und Untergruppen | kluger1996; EC/F | D7: vielfältige Aufgaben/Populationen; Feedback → Performanz | K; Komplexitätsmoderation nur eingeschränkt abgesichert; H | T10 |
| `fb.2` Informationsgehalt von Feedback | wisniewski2020; EC/F | D8: Bildungskontexte; Feedback → heterogene Outcomes | K; unkontrollierte Prä-Post- und kontrollierte Studien trennen; H | T10 |
| `fb.3` Zeitnahes spezifisches Feedback | shute2008; EC/A | Review; Population offen; formative Rückmeldung → Lernen | O/P; zeitnah nicht immer sofort, Testzweck und Schwierigkeit berücksichtigen; M | T10 |
| `fb.4` Drei Feedbackfragen | hattie2007; EC/M | Review; Population offen; Aufgabe/Prozess/Selbstregulation → Lernen | O/T; Rahmen und Einzelbefunde getrennt extrahieren; M | T10 |
| `mc.1` Überschätzung führt zu Abbruch | dunlosky2012; EC/M | Experiment registriert; Population/Manipulation nicht gelesen | O; kausales „führt“ bis Designprüfung konditionieren; H | T11 |
| `mc.2` Wiederlesen steigert Zuversicht | roediger2006; EC/A | D1 ergänzend; Textlernen → Konfidenz vs. Retention | K; Urteil und Leistung nicht gleichsetzen; M | T11 |
| `mc.3` Desirable Difficulties | bjork1994; EC/M | Buchkapitel; Operationen verschieden → verzögertes Lernen | T/O; Schwierigkeit allein weder notwendig noch hinreichend; H | T11 |
| `tr.1` Transferdimensionen | barnett2002; TM/A | Taxonomie; keine einzelne Population; Aufgabenänderung → Klassifikation | T/P; Metadaten setzen belegt keinen Transfer; H | T12 |
| `its.1` ITS fast wie menschliche Tutoren | vanlehn2011; EC/A | Review; genaue Population offen; Tutoring → Tests; Abstract 0.76/0.79 | O/K; studienübergreifende Mittelwerte kein Äquivalenztest; H | T13 |
| `its.2` ITS über Großgruppe/Arbeitsbuch | ma2014; EC/A | Meta-Analyse; heterogene Lernende; Tutoring → Achievement; Abstract .42/.35 | O/K; Nullvergleich zu Einzeltutoren/kleinen Gruppen mitführen; H | T13 |
| `its.3` ITS Median 0.66 SD | kulik2016; EC/A | Meta-Analyse; Population offen; Tutor → lokal/standardisiert gemessene Tests | O/K; Median nicht gepoolter Effekt, Testnähe entscheidend; H | T13 |
| `its.4` Kurzes direktes Fehlerfeedback am besten | anderson1995; EC/A | Narrativer Review; genaue Population offen; Cognitive Tutors → Lernleistung | O; Abstract belegt nicht „beste“ aller Interaktionen oder generelle Tutorüberlegenheit; H | T13 |
| `its.5` Hilfesuchen verbessert, Fachlernen nicht | aleven2016; EC/A | Review mit Klassenstudie; Population offen; Hilfeverhalten → getrennte Outcomes | O/K; wichtiger Gegenbefund gegen Prozessindikatoren als Erfolgsersatz; H | T13 |
| `its.6` Knowledge Tracing | corbett1994, pelanek2017; EC/M | Modellierung/Review; Datenpopulation offen; Antworten → Zustandsschätzung | T/O; Vorhersagegüte, Kalibrierung und Unterrichtswirkung unterscheiden; H | T13 |
| `its.7` KLI-Passung | koedinger2012; EC/A | Rahmenmodell; Gedächtnis/Induktion/Verstehen → Instruktionshypothesen | T; keine empirisch universelle Ontologie; M | T13 |
| `ai.1` Ungeschützter KI-Zugang | bastani2025; EC/F | D10: türkische Schule; Übung mit KI → Prüfung ohne KI | K; relativer Rückgang, kein Langzeittest; Neutralität keine Sicherheit; H | T14 |
| `ai.2` KI-Tutor in Harvard-Physik | kestin2025; EC/F | D11: Studierende; zwei Lektionen → unmittelbarer Test | K/O; veröffentlichte Version nicht frisch lesbar; Paketvergleich statt isolierter Mechanismus; H | T14 |
| `as.1` Constructive Alignment | biggs1996; TM/M | Rahmenmodell; Operatoren → curriculare Passung | T/P; gleiche Verben garantieren keine gleiche Anforderung; H | T15 |
| `as.2` 31 validierte MC-Leitlinien | haladyna2002; TM/A | Review/Taxonomie; Lehrbücher und Studien → logische Validierung | O/K; kein RCT jeder Leitlinie; Distraktorqualität fachlich prüfen; M | T15 |
| `as.3` Bloom zweidimensional | krathwohl2002; TM/M | Taxonomie; keine Interventionspopulation → Lernzielklassifikation | T; nicht Schwierigkeit, Lernfortschritt oder Wirksamkeit; M | T15 |
| `as.4` Formative Assessment bringt Gewinne | black1998; TM/A | Review; Population offen; Interventionsbündel → Lernen | O/K; häufiges Feedback nicht isoliert identifiziert; H | T15 |
| `ls.1` Meshing nicht ausreichend belegt | pashler2008; RJ/M | Review; Population offen; Präferenzpassung → behaupteter Nutzen | O; fehlender Beleg nicht Beweis aller denkbaren Nullwirkungen; keine Lernstilsteuerung; M | T16 |
| `ps.1` Dehaenes vier Säulen | dehaene2020; TM/M | Populärsynthese; keine eigenständige Population/Schätzung | T/O; nur Orientierung, keine neuronale Begründung einer UI-Regel; L | T17 |
| `ps.2` Careys Popularisierung | carey2014; TM/M | Wissenschaftsjournalismus; kein eigenständiger Outcome | T/O; Primärarbeiten statt Popularisierung als Beleg; L | T17 |

## 5. Elf vertiefte Reviews

Risikobasierte Auswahl nach Produktreichweite, numerischen Behauptungen und Gefahr falscher Kompetenzzertifizierung. Zugang jeweils 26.11.2026. Keine gepoolte Neuberechnung; Zahlen sind berichtete Schätzungen. Die folgenden Bias-Einwände sind eine begründete Einzelbewertung, **keine abgeschlossene RoB-2-/AMSTAR-2-Bewertung** aller eingeschlossenen Studien.

### D1 — rp.1: Abruf und Retentionsintervall

[Roediger & Karpicke 2006, Originalartikel als Hochschul-PDF](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf), S.250–253, Experimente 1/2, Methoden und Ergebnisse. Experiment 1: 120 Studierende, 18–24 Jahre, zwei kurze Sachtexte; gegenbalancierter Wiederlese-/Abrufvergleich, Tests nach fünf Minuten, zwei Tagen oder einer Woche. Outcome: erinnerte Sinneinheiten, keine Beweiskonstruktion. Wiederlesen hilft beim unmittelbaren Test, Abruf beim verzögerten. Experiment 2 zeigt keinen eindeutig abgesicherten Zusatzvorteil dreier gegenüber einem Abruf nach einer Woche.

**Inferenz:** experimenteller, zeitabhängiger Effekt in diesem Setting; Konfidenz ist kein Lernerfolg. Kleine Materialauswahl und campusgebundene Population begrenzen Generalisierung. Die Prüfung wiederverwendet den gelernten Inhalt; unbekannter struktureller Transfer wurde damit nicht nachgewiesen. Korrektur: RP-R1 als operationsbezogene Empfehlung, nicht „alle Aufgaben zuerst durch Abruf lernen“. Gegenhypothese: Mehr Abrufe können bei festem Zeitbudget benötigte Erklärung verdrängen. Technischer Pfad T1; unabhängiger Test muss verzögert und ohne Lösungshinweis erfolgen.

### D2 — rp.2: Die Abrufformat-Rangliste hält der Sensitivität nicht stand

[Rowland 2014, vom Autor hochgeladener Volltext](https://www.researchgate.net/publication/264988491_The_Effect_of_Testing_Versus_Restudy_on_Retention_A_Meta-Analytic_Review_of_the_Testing_Effect), Tabellen 1/2, „Categorical Moderator Analyses“, „Initial test type“, Publikationsstatus. 159 Effekte; überwiegend laborgestütztes Gedächtnislernen, keine universelle Lernoperation. Gesamt-g=0.50 [0.42;0.58]. Ohne Feedback bei niedriger Erstabrufquote: g=0.03 [−0.21;0.27], **unsicher statt bewiesene Null**.

Die Vollstichprobe ergibt cued/free/recognition 0.61/0.29/0.29; im High-exposure-Subset stehen cued 0.72 [0.61;0.83] und free 0.81 [0.45;1.18]. Feedback und Erstabrufleistung kovariieren mit Format. Ebenso verschwindet dort der Unterschied publiziert/unpubliziert. Daher sind „Hinweisreiz verursacht den größten Nutzen“ und „0.25 beweist Publikationsbias“ überzogen. Untergruppenunterschiede sind keine randomisierte Moderatorintervention. Die 50%-Grenze ist eine Analysegruppe, keine diagnostisch validierte Engine-Schwelle. RP-R1: Format nach Zielkompetenz wählen, Fehlabrufe korrigieren, Formatwahl experimentell prüfen. T1.

### D3 — rp.3: Transfer ist nicht gleich Problemlösen

[Pan & Rickard 2018, Autoren-PDF](https://rickardlab.ucsd.edu/pdf/PR_2018.pdf), Manuskript S.25–27, Tabellen 2–5, „Analyses adjusted for publication bias“. 122 Experimente, 192 Transfer-Effekte, N=10.382; Abruf versus erneute Darbietung. Gesamt-d=0.40 [0.31;0.50], aber Problemlösegruppe d=0.29 [−0.078;0.65], p=.10; ungetestetes zuvor gesehenes Material ebenfalls nicht signifikant. Laborlastigkeit und Unterschiede zwischen Transferkategorien begrenzen Übertragbarkeit.

Response congruency und elaborierter Abruf moderieren die Ergebnisse; biasadjustierte Intercepts können ohne diese Bedingungen nahe null liegen. Das ist weder ein Beweis genereller Unwirksamkeit noch ein kausaler Nachweis der Moderatoren. **Korrektur:** rp.3 darf keinen sicheren Beweis-/Ferntransfer nahelegen. Der Anspruch an eigenständige Aufgaben bleibt eine Produktanforderung, die getrennt geprüft werden muss. Neue Zahlen allein verändern nicht zwingend die Denkoperation. T1/T12; Fall M unten operationalisiert die Differenz. Primärstudien-Rohdaten wurden nicht repliziert.

### D4 — sp.2: Abstandsprozente sind keine Scheduling-Konstanten

[Cepeda et al. 2008, Autoren-PDF](https://www.yorku.ca/ncepeda/publications/CVRWP2008.pdf), S.1096–1100, „The Current Study“, Method/Results, Tabelle 1 und Retentionskurven. Online-Experiment, 1.354 berichtete Teilnehmende, 26 zufällig zugewiesene Gap×Retention-Bedingungen; 32 Fakten, erneutes Lernen mit Feedback, später Abruf/Wiedererkennen. Unter den Completern: mittleres Alter 34, Bereich 18–72. Optimale relative Abstände hängen vom Prüfintervall ab; die KB-Prozentangaben beschreiben diese Retentionsfläche.

**Bias/Übertragbarkeit:** stärkere Ausfälle bei längeren Verzögerungen; fehlende beobachtete Ausgangsunterschiede beseitigen Selektionsrisiko nicht. Fakten mit kurzen Antworten, nicht Mathematikbeweise oder klinische Diagnosen. Optima sind gruppen-/designabhängige Schätzungen, keine individuellen sicheren Grenzwerte; hier keine Präzisionsintervalle für jedes Optimum extrahiert. SP-R1 ist eine Datenintegritäts-/Produktentscheidung; SP-R2 braucht empirisch begründete Messabstände. Kein eigener Scheduler und keine FSRS-Parameter aus den Prozentwerten. T2.

### D5 — il.1: Text-null ist nicht Wort-negativ

[Brunmair & Richter 2019, DOI](https://doi.org/10.1037/bul0000209); gelesenes [akzeptiertes Autorenmanuskript](https://www.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf), „Coding of Moderator Variables“, „Generalizability across learning materials“, Tabellen 2/3. 59 Studien, 238 Effekte in 158 Stichproben; 173 Effekte aus Studierendenstichproben. Interleaving versus Blocken bei induktivem Lernen. Mathematik g=0.34 [0.11;0.57], Wörter −0.39 [−0.64;−0.14], Sachtexte nicht signifikant; hohe Heterogenität.

**Korrektur:** Der alte Locator „Table 3“ allein ist unzureichend: Materialmittelwerte stehen in Tabelle 2, Regressionen in Tabelle 3. Materialähnlichkeit ist kodierte Meta-Regression, kein Beweis einer notwendigen Bedingung. Fehlende Altersangaben und materialabhängige Stichproben erschweren externe Validität. Textbefunde rechtfertigen kein pauschales Verbot, juristische Fälle zu mischen; deren Operation müsste separat untersucht werden. IL-R1 als vorsichtige Auswahlhypothese führen, keine feste Naturregel. T3. Manuskript enthält beim negativen Wortbefund einen widersprüchlichen p-Ausdruck; deshalb CI berichtet, p nicht übernommen, Version-of-record-Abgleich offen.

### D6 — we.4: Expertise Reversal stützt keine Ein-Item-Expertendiagnose

[Kalyuga 2007, Volltext](https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf), S.515–518, Tabelle 1; S.530–532, Diagnose/adaptive Instruktion. Review experimenteller technischer Lernaufgaben; keine neue Meta-Analyse. Berichtete Beispiele: Worked Examples versus Problemlösen 1.20/−0.36 für niedriges/hohes Vorwissen; langsames/schnelles Fading 1.30/−0.47. Die Werte gehören zu verschiedenen Primärstudien, nicht zu einem gepoolten Expertise-Effekt. Unsicherheitsintervalle werden hier nicht neu konstruiert.

**Methodische Grenze:** Der Review beschreibt vielfach querschnittliche Vorwissensgruppen, kleine Stichproben und teils rekonstruierte Effektgrößen. Vorwissen ist nicht durchgehend randomisiert. Kalyuga & Sweller 2004 und Reisslein 2005 wurden in R0 nicht im Original nachgelesen; Primärquellenkette bleibt offen. Ein Erste-Schritt-Verfahren über ausgewählte Aufgaben validiert nicht jede beliebige erste Antwort. WE-R2/RA/RD sind daher unkalibrierte Policy-Entscheidungen. Prozedur-, Beweisverständnis- und Beweiskonstruktionsaufgaben getrennt diagnostizieren; Hilfen reversibel anbieten. T4.

### D7 — fb.1: Feedback kann schaden, Komplexität ist kein harter Schwellwert

[Kluger & DeNisi 1996, zugänglicher Originalartikel-Text](https://www.academia.edu/43519881/Kluger_DeNisi_1996_meta_analysis), S.258–260, Method; S.272–275, Ausschlüsse, Tabelle 2, Results/Limitations. 607 Effektgrößen, 23.663 Beobachtungen; viele Populationen und Leistungsaufgaben, kein homogener Schulkurs. Mittel-d=.41, erheblicher Anteil negativer Effekte. Nach Ausschlüssen bleiben 470 Effekte; Tabelle 2 gehört zu diesem eingeschränkten Datensatz.

Komplexitätsgruppen .03/.55 sind keine experimentell randomisierte Komplexitätswirkung; die Autoren behandeln diesen Moderator mit Vorsicht, da er das strengere α=.01-Kriterium nicht erreicht. Abhängigkeiten und Ausschlussentscheidungen sind relevant. Konfidenzintervalle für diese Gruppen sind hier nicht extrahiert; Varianzen nicht als CI ausgeben. **Korrektur:** „bei komplexen Aufgaben wirkt Feedback nicht“ ist unzulässig. FB-R1 kann begründet zielgerichtete Rückmeldung vorsehen, aber diese konkrete Teilschritt-Regel bleibt eine zu prüfende Ableitung. Leistung, Transfer und Behalten getrennt messen. T10.

### D8 — fb.2: Ein positiver Mittelwert verdeckt Designunterschiede

[Wisniewski et al. 2020, veröffentlichter Volltext](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.03087/full), „General Impact“, „Bias and Heterogeneity“, „Outlier Analysis“, Tabellen 2/3. 435 Studien/994 Effekte, etwa 61.000 Lernende; Feedback gegen unterschiedliche Vergleiche und auch Prä-Post-Designs. Nach 35 ausgeschlossenen Extremwerten d=.48 [.44;.51], I²=83.40%. Kontrollierte Studien .42 [.37;.46], Prä-Post-Studien .63 [.56;.69]; Ausgangsdatensatz 17% negative Effekte.

**Risiko:** Prä-Post-Zuwachs nicht mit kausaler Zusatzwirkung gleichsetzen; Funnel-Asymmetrie ist ein Bias-Signal, nicht eindeutig dessen Ursache. Informationsgehalt und Outcome moderieren, aber keine Zufallszuweisung zu den Meta-Untergruppen. Der Publikationsmedian liegt 1985: kein direkter Test heutiger LLM-Feedbacksysteme. Nachträgliche Ausreißerbereinigung benötigt Sensitivität. Hohe Information ersetzt keine Prüfung, ob Lernende selbst erklären oder nur übernehmen. FB-R1 und Fehlerklassifikation bleiben produktbezogene Hypothesen. T10.

### D9 — cl.2: Kognitive Entlastung wovon, für welches Ziel?

[Sweller 1988, Originalartikel-PDF](https://www.waddesdonschool.com/wp-content/uploads/2021/02/Cognitive-Load-Theory-Sweller-J-1988.pdf), S.277–282, „Measures of Cognitive Load“, Method, Tabellen 3–6. Computermodell plus Experiment mit 24 Schülern der Jahrgangsstufe 10, 15–16 Jahre, Trigonometrievorwissen; konventionelle versus unspezifische Ziele, je zwölf Teilnehmende. Reproduktion von Problemangaben/Lösung als Sekundäraufgabe dient als Belastungsindikator.

Der Versuch sollte ausdrücklich nicht spätere Problemlöseleistung testen. Gesamt-Lösezeit und mathematische Fehler unterschieden sich nicht signifikant; Reproduktionsbefunde tragen die Interpretation. Kleine Stichprobe, enges Material, indirekte Belastungsmessung; das Modell ist keine Messung neuronaler Kapazität. **Korrektur:** CL-R2 darf Exploration nicht generell als schädlich behandeln und kein „weniger kognitive Arbeit = mehr Lernen“ behaupten. Auslagern nebensächlicher Suche kann helfen; Auslagern der Zieloperation beseitigt die Übung. Das ist eine begründete Unterscheidung, deren konkrete UI-Umsetzung zu evaluieren bleibt. T6, Fälle M/T.

### D10 — ai.1: Assistierte Leistung und selbstständige Prüfung divergieren

[Bastani et al. 2025, veröffentlichter Volltext](https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/), „Experimental Design“, „Main Results“, Fig.2, Fußnote zur Klassenzuteilung. Fast 1.000 Schüler, Klassen 9–11, eine türkische Schule, vier 90-Minuten-Sitzungen; Klassenarme Kontrolle/GPT Base/GPT Tutor. Unterricht, Übung und **unmittelbar anschließende** Prüfung ohne KI bilden jeweils eine Sitzung; Prüfung unter schulischer Aufsicht. Keine Langzeitmessung durch diesen Endpunkt.

Base: assistierte Übung +48% relativ; selbstständige Prüfung −.054 auf der 0–1-Skala, entsprechend −17% relativ, nicht −17 Prozentpunkte. Tutor-Schätzung −.004, nicht signifikant. Zufällige Klassenzusammensetzung und eingeschränkte Klassenzuteilung verlangen designspezifische Prüfung; Honors-Klassen sind aus der Hauptanalyse ausgeschlossen. SI/Präregistrierung nicht vollständig auditiert. Lehrerbasierte Aufgaben, nahe Prüfaufgaben und ein Standort begrenzen Transfer. **Korrektur:** weder Tutor-Äquivalenz noch langfristige Schadensfreiheit belegt; Offloading ist plausible Erklärung, kein vollständig isolierter Mechanismus. T14.

### D11 — ai.2: Positiver Paketvergleich, veröffentlichte Version offen

[Kestin et al., Preprint v1, 14.05.2024](https://assets-eu.researchsquare.com/files/rs-4243877/v1/5ebc554a-9a22-4dbf-a25c-8998783fd358.pdf?c=1750944764), PDF S.3–4, Tabelle 1; S.9–10, Methoden. Die [publizierte Identität 2025](https://pubmed.ncbi.nlm.nih.gov/40537565/) ist bestätigt; Nature/PMC-Zugriff scheiterte in diesem Lauf. Deshalb kein neuer Volltextstatus für die Version of Record.

Harvard-Einführungsphysik; zwei Lektionen mit gewechselter Bedingung, 194 eingeschlossene von 233 eingeschriebenen Studierenden. KI zu Hause versus aktive Präsenzlehre; unmittelbare Vor-/Nachtests. .63 ist ein adjustierter standardisierter Regressionskoeffizient, kein hier neu berechnetes universelles Cohen-d. Keine verzögerte Transfermessung in diesem Design. Peergruppen bleiben bei Zuteilung zusammen; Ausschlüsse, Periodenabhängigkeit, Setting, Selbsttaktung und Zeitmessung erfordern Prüfung. Ein isolierter Prompt-/Hint-Effekt ist nicht identifiziert. **Korrektur:** bisherige Limitations-Zitate der 2025-Version nicht ungeprüft fortschreiben; finale Fassung und Supplement nachbeschaffen. T14. Befund kann mit D10 koexistieren, ohne dass ein einzelner Moderator bewiesen ist.

## 6. Implementierungsregeln und tatsächlicher technischer Nachweis

Nur **statische Code-/Testinspektion**, keine erneute Ausführung der Engine-Suiten. „Test vorhanden“ bedeutet nicht „in R0 ausgeführt“ und niemals „Lernwirkung belegt“. Pfade beziehen sich auf den eingefrorenen Forschungsbaseline-Commit; PR #28 ist ein anderer Implementierungsstand. Regeln sind aus `principles.json` vollständig zugeordnet, nicht automatisch akzeptiert.

| Pfad | Prinzip / Regeln | Tatsächlicher Anknüpfungspunkt und Grenze |
|---|---|---|
| T1 | retrieval_practice; RP-R1–R3 | `knowledge.context_for` gibt Regeln an Autoren; `learning/policy.py:helped` und RF unterscheiden protokollierte Hilfe. `tests/test_b19_integration_design.py:test_full_learning_flow_inside_the_chapter` prüft eine Browserfolge. Kein Nachweis erfolgreichen mentalen Abrufs oder ausgeschlossener externer Hilfe. |
| T2 | spacing; SP-R1–R2 | `policy.kc_status` zählt unterschiedliche Datumswerte; `decide` liefert Anki-Tags. Review-Historienerhalt ist technische Integrität, kein Langzeitlernen. Ein neuer Kalendertag ist kein festes Mindestintervall. |
| T3 | interleaving; IL-R1 | Agentencheckliste, kein validierter materialabhängiger Interleaving-Algorithmus nachgewiesen; Evidenzmatrix nennt selbst IMPLEMENTED_PARTIAL. |
| T4 | worked_examples; WE-R1–R2 | `policy.decide` RA/RD/RF; eine richtige unabhängige Antwort kann zum Transfer führen. Spec `worked_example_fading`; Felder/Stufen beweisen keine valide Expertise-Diagnose. |
| T5 | productive_failure; PF-R1 | Spec erlaubt kurze Exploration; ≤5 Minuten ist eine eigene Setzung. Keine experimentell validierte PF-Umsetzung aus dem Vorhandensein einer Vorhersagefrage. |
| T6 | cognitive_load; CL-R1–R2 | B19-Browsertest `test_lab_guided_step_and_explore_check`; Sichtbarkeit/Modus technisch prüfbar, Belastungsreduktion und Schemaerwerb nicht. |
| T7 | prediction_simulation; PR-R1–R3 | Spec `visualization`; Vorhersagevertrag/Referenzrechnungen. Konfidenz vor Auflösung ist beobachtbar, Hyperkorrektur oder bessere Experimentplanung daraus nicht bewiesen. |
| T8 | multimedia; MM-R1–R2 | Figuren-/Layoutchecklisten und B19 `test_stage_design_and_dark_mode`; keine Messung von Repräsentationsübersetzung oder Effekt der Farbwahl. |
| T9 | self_explanation; SE-R1–R2 | `learning/diagnose.py:diagnose`, Zweig `open`, liefert `UNVERIFIED`; korrekt vorsichtig. Text vorhanden ≠ gute Selbsterklärung. |
| T10 | feedback; FB-R1–R2 | `diagnose` vergleicht numerische Antworten/Teilschritte mit Sollwerten und Fehlerbibliothek; Fehlerursache wird damit nicht eindeutig identifiziert. |
| T11 | metacognition; MC-R1–R2 | Vorhersage-/Konfidenzanforderungen im Regelkontext; keine empirische Kalibrierungswirkung belegt. Speicherung einer Angabe ersetzt keinen Brier-/Kalibrationsvergleich. |
| T12 | transfer; TR-R1 | `knowledge.check_item`/`check_item_set`; `tests/test_knowledge_base.py:test_number_only_variants_are_flagged`. Metadaten und Zahlendubletten prüfen, nicht semantisch neuen Transfer beweisen. |
| T13 | intelligent_tutoring; ITS-R1–R2 | Statusvokabular in `policy`; numerische Steps in `diagnose`; kein kalibriertes BKT. Constraints prüfen ausgewählte Prämissen, keinen freien Beweis. |
| T14 | ai_tutoring; AI-R1–R2 | Spec `tutor_hints`, Brief-/Eventverträge; `agent_judgement` ist Kennzeichnung, keine Validität. Kein RCT des konkreten Tutors. Spec verlangt Level4 nach Versuch, Regel AI-R1 lässt ausdrücklichen Lösungswunsch als Alternative erkennen: Regelkonsistenz klären, nicht hier ändern. |
| T15 | assessment_alignment; AS-R1–R2 | `knowledge.check_exam_against_blueprint`; Summen, Zeiten und ±10%-Abweichung. Diese Schwelle ist gesetzt; ein Operatorfeld garantiert keine passende Prüfungsanforderung. |
| T16 | learning_styles; LS-R1 | Negativregel im Kontext; `test_rejected_principles_have_no_positive_rules_leaking_into_context`. Keine Präferenztypisierung einführen; Accessibility-Bedarf ist etwas anderes als Meshing. |
| T17 | popular_syntheses; keine Regeln | Reine Orientierung; keine eigene technische oder empirische Validierung. |

**Zusätzliche Matrix-Triage:** Alle 17 Zeilen von `learning_design_evidence_matrix.json` sind abgedeckt: Retrieval→T1, Spacing→T2, Worked Examples→T4, Feedback→T10, Step tutoring→T13, Constraint modelling→T13, Selbsterklärung→T9, Interleaving→T3/T12, Multimedia→T8, Load→T6, BKT→T13, LLM→T14, kein Mastery-Prozent→T13, Metakognition→T7/T11, adaptives Scaffolding→T4/T13, Farbrollen→T8, dunkle Bühne→T8. Die letzte Zeile und die Vermeidung eines Prozentwerts sind ausdrücklich Produktentscheidungen. ICAP wird in der Matrix stärker formuliert als im theoretisch markierten KB-Claim. Constraint-Modelling nennt Ohlsson ohne eindeutig verifiziertes Jahr: bibliografische Lücke außerhalb der 55 Kernquellen, nicht stillschweigend als geprüft zählen. Mitrovic et al. 2007 und die Mayer-Jahresvariante 2020/2021 brauchen eindeutige Registerzuordnung. Paas 1992 wird im Evaluationsprotokoll benutzt, besitzt dort aber keinen vollständigen Quellen-/Instrumentnachweis.

**Alle sieben Specs:** `worked_example_fading`, `error_taxonomy`, `tutor_hints`, `assessment_item`, `exam_blueprint`, `anki_card`, `visualization` bleiben DESIGN_HYPOTHESIS. Insbesondere 4 Fading-Stufen, 3 Hinweise plus Lösung, ≤5 Minuten Exploration, ±10% Blueprint, ≤60 Wörter/≤4 Listenelemente einer Karte sind keine experimentell validierten Universalwerte. Atomisierung kann notwendige Bedingungen zerschneiden; stabile Anki-IDs schützen Daten, nicht Verständnis. Eine Fehlerbibliothek kann gleiche Antworten aus unterschiedlichen Denkwegen nicht eindeutig diagnostizieren.

### Historische menschliche Evidenz und Evaluationslücke

[Issue #4, verbindlicher Human Review vom 14.11.2026](https://github.com/Sven-Lutz/Exam_Mastery/issues/4): Lehrbuch 1/4, Mathematik 0/4, Visualisierung 0/4, Lernprozess 1/4, Exam readiness 1/4. Der berichtete Mittelwert 0.6/4 ist keine validierte Gesamtskala. Keine vollständigen seitenweisen Human-Annotationen vorhanden. Diese Evidenz belegt Ablehnung des damaligen Produkts, **keine kausale Widerlegung von Retrieval/Spacing** und keine neue Bewertung von PR #28.

Lesend geprüft: `docs/ENGINEERING_RECOVERY_20261126.md` sowie die im unveränderten lokalen Pilot vorhandenen Berichte `docs/reference_unit/V3_REPORT.md` und `ISSUE4_CORRECTIONS.md`. Letztere sind technische Autorenberichte, keine unabhängige positive Human-Abnahme; ihre lokalen Referenzen werden nicht als öffentlich verfügbare Forschungsdaten ausgegeben oder kopiert. Historische Defekte betreffen unter anderem unzureichende Beweis-/Visualerklärung, ungeprüfte Kompetenzlabels und uneindeutige Aufgaben. Eine KB-Checkliste kann diese Inhaltsvalidität nicht ersetzen. **HUMAN_REJECTED bleibt bestehen.**

`EVALUATION_PROTOCOL.md` ist korrekt als NOT_RUN markiert. Es benötigt vor einer tatsächlichen Studie: primären Endpunkt, präzisen Messzeitpunkt statt frei wählbarer 7–14 Tage, begründete Fallzahl, Zuteilungsverdeckung, Ausfall-/Missing-Data-Plan, Umgang mit Wiederholung/externen Hilfen, blindes Scoring und empirische Prüfung der Parallelformen. `learning/evaluation.py:forms` liefert kleine modellbasierte X/Y-Sätze; deren Äquivalenz ist nicht geprüft. Ein Hash erzeugt reproduzierbare Zuweisung, keine garantierte Balance und keine von Rekrutierung unabhängige Zufallszuteilung. Kleine Piloten dürfen Machbarkeit/Unsicherheit berichten; n≥30 erlaubt umgekehrt nicht automatisch Wirkungsbehauptungen.

## 7. Zwei ausgearbeitete Transfers in Exam Mastery

Die folgenden Beispiele sind eigene synthetische Forschungsentwürfe, keine Teilnehmerdaten, keine automatisch validierte Didaktik und keine neuen Produktfeatures.

### Fall M — Mathematische Operation: Varianz einer Summe herleiten

**Wissenschaftliche Evidenz → Geltungsbedingungen.** D1/D2 stützen Üben des Abrufs bereits eingeführter Inhalte, D6 eine vorwissensabhängige Unterstützung, D3 begrenzt die Gleichsetzung von Abruf und Problemlösen. Ziel ist hier **eine Herleitung mit Voraussetzungen und Gegenbeispiel**, nicht allein das Erinnern einer Formel. Die Übertragung dieser Evidenz auf den konkreten Ablauf ist eine Designhypothese; Voraussetzung sind reelle Zufallsvariablen X,Y mit endlichen zweiten Momenten, Kenntnisse des Erwartungswerts und distributives Rechnen.

**Didaktische Entscheidung.** Erst Definitionen ohne Vorlage abrufen: Var(X)=E[(X−E[X])²], Cov(X,Y)=E[(X−E[X])(Y−E[Y])]. Wer sie noch nicht kennt, erhält Erklärung und Beispiel statt wiederholter erfolgloser Tests. Anschließend ein Worked Example:

Für μ=E[X], ν=E[Y] gilt durch Linearität des Erwartungswerts

`Var(X+Y) = E[((X−μ)+(Y−ν))²]`

`= E[(X−μ)²] + 2 E[(X−μ)(Y−ν)] + E[(Y−ν)²]`

`= Var(X) + 2 Cov(X,Y) + Var(Y)`.

Jeder Schritt begründet eine Operation: Zentrieren, binomische Formel, Linearität, Definition. Endliche zweite Momente sichern die benötigten Erwartungen. Bei unabhängigen X,Y ist die Kovarianz null; Unabhängigkeit ist hinreichend, nicht notwendig. Fading: für feste reelle Konstanten a,b bei `Var(aX+bY)` die Expansion und den gemischten Term selbst ergänzen. Lösung: `a² Var(X)+2ab Cov(X,Y)+b² Var(Y)`. Fortgeschrittene dürfen direkt die neue Aufgabe versuchen; ein einzelner korrekter Start wird nicht als umfassende Expertise gewertet.

**Technische Anforderung → beobachtbare Handlung.** Voraussetzungen, Begründungen und Rechnung getrennt erfassen; Hilfe/Beispielansicht kennzeichnen, Fehlinterpretationen nicht nur Zahlenfehler klassifizieren. T10 kann eine Zahl prüfen, T13 keine freie Herleitung zertifizieren. Beobachtbar sind eigener erster Ansatz, benannte Kovarianzbedingung und selbst erzeugtes Gegenbeispiel. Auch bei korrektem Endwert bleibt die Begründung extern zu bewerten.

**Unabhängiger Nachweis.** Nach einem vorab festgelegten Abstand (z.B. sieben Tage als Studienentscheidung, nicht bewiesenes Optimum) ohne Unterlagen: Sei X gleichverteilt auf {−1,0,1}, Y=X². Berechne Cov(X,Y), prüfe Unabhängigkeit und bestimme Var(X+Y). Vollständige Lösung: E[X]=0, E[Y]=2/3, E[XY]=E[X³]=0; Cov=0. X,Y sind abhängig, denn `P(Y=0|X=0)=1`, aber `P(Y=0)=1/3`. Var(X)=2/3, Var(Y)=2/3−4/9=2/9, also Var(X+Y)=8/9. Direktcheck: X+Y nimmt 0,0,2 an; E[(X+Y)²]−E[X+Y]²=4/3−4/9=8/9.

Rubrik (vor Einsatz zu pilotieren): 2 Punkte Zentrieren/Annahmen, 2 Expansion, 2 Erwartungswerte, 2 Gegenargument zur Unabhängigkeit, 2 begründeter Transfer. Blindes fachliches Scoring und Zweitbewertung strittiger Schritte. Erstabruf der Definition wird separat ausgewiesen.

**Mögliche Fehlinterpretation / harter Gegenfall.** „Unkorreliert ⇒ unabhängig“ ist trotz richtiger Varianzformel falsch; Y=X mit nichtkonstantem X widerlegt außerdem das Weglassen der Kovarianz, denn Var(X+Y)=4 Var(X), nicht 2 Var(X). Eine Anki-Erinnerung, ein ausgefülltes Lückenbeispiel oder ein numerisch richtiges Ergebnis beweist keine eigenständige Herleitung. Wiederverwendung der exakt geübten Gegenbeispiele im Erfolgstest wäre Kontamination, deshalb wären für eine tatsächliche Studie weitere unbekannte Parallelfälle vorzubereiten.

### Fall T — AI-Tutoring: richtige Softmax-Antwort ohne Verständnis

**Wissenschaftliche Evidenz → Geltungsbedingungen.** D10 zeigt, dass assistierte Übung und anschließendes selbstständiges Können auseinanderfallen können; D11 untersucht einen anders gestalteten Gesamtunterricht. Keiner dieser Befunde belegt eine universelle Offloading-Kausalität oder die Wirksamkeit unseres Hint-Protokolls. D9 motiviert die Unterscheidung zwischen Entlastung irrelevanter Rechenarbeit und Wegnahme der Zieloperation. Ziel hier: Invarianz von Softmax verstehen und von Temperaturänderung unterscheiden; Voraussetzungen sind Exponentialregeln und Bruchrechnung.

**Didaktische Entscheidung.** Der Tutor erhält eine geprüfte Lösung, fragt nach dem eigenen Ansatz und bietet bedarfsgerechte Hinweise. Das ist eine zu testende Produktentscheidung, keine garantierte Schadensvermeidung. Aufgabe: Scores `(0, ln 3)`, Values `(2,6)`. Gewichte `(1/4,3/4)`, gewichtete Summe `5`. Für eine nichtleere endliche Menge endlicher reeller Scores und eine endliche reelle Konstante c (hier zwei Scores) bleibt nach Addition von c zu allen Scores

`exp(z_i+c)/Σ_j exp(z_j+c) = exp(c)exp(z_i)/(exp(c)Σ_j exp(z_j))`

unverändert. Abziehen des Maximums ist der Fall c=−max(z); in exakter Arithmetik gleiche Gewichte, numerisch kleinere Exponenten. Keine unbewiesene Garantie für jede Gleitkommasituation.

**Technische Anforderung → beobachtbare Handlung.** Eigener erster Ansatz, benutzte Hintstufe und Lösungsansicht getrennt protokollieren; ein nach Vorlage eingegebenes `5` bleibt assistiert. Der Tutor darf die Qualität der Erklärung nicht selbst als unabhängigen Lernerfolg bestätigen. Falsche Tutorbehauptung als kontrollierter Negativfall: „Auch Multiplikation aller Scores mit 2 lässt die Gewichte gleich.“ Das System muss eine fachlich geprüfte Gegenrechnung bereitstellen können; ein korrekt wiederholter Satz allein reicht nicht.

**Unabhängiger Nachweis.** Ohne Tutor und ohne Lösungstext muss der Lernende bei `(0,2 ln 3)` Gewichte `(1/10,9/10)` und Ausgabe `2/10+54/10=5.6` herleiten und den Unterschied zum gemeinsamen additiven Shift begründen. Zusätzlich ein unbekannter Transferfall mit drei Scores, anderer Darstellung und begründeter Maske; vollständige Rubrik vor Erhebung festlegen. Unmittelbare Leistung, verzögerte Leistung und Transfer separat ausweisen. Geprüft werden Rechenweg, Invarianzargument und selbstständige Fehlerkorrektur, nicht nur Antwortkorrektheit oder Zufriedenheit.

**Mögliche Fehlinterpretation.** Höhere Sitzungsgenauigkeit kann Kopieren, Feedbacknutzung oder echtes Lernen bedeuten. Ein nichtsignifikanter Unterschied im verzögerten Test beweist weder Nutzen noch Harmlosigkeit. Vergleichsdesign: identischer Inhalt und transparente Zeitbudgets; eine starke statische Beispiel-/Übungsbedingung gegen Tutor-Unterstützung, blind bewertete unbekannte Aufgaben, vorab primärer verzögerter Endpunkt. Ein späterer Komponententest muss Hinting von Lösungsvorgabe und Selbsttaktung trennen. Keine solche Studie wurde hier durchgeführt.

## 8. Priorisierter Backlog R1–R9 — nicht gestartet

Priorität bezeichnet Reihenfolge/Abhängigkeit, nicht eine autorisierte Folgeausführung. Nächster Sprint soll zuerst R0-Funde unabhängig prüfen; dieses Dokument endet mit R0.

| Rang / Workstream | Präzise Forschungsfrage und falsifizierbarer Output | Voraussetzung / Abbruchregel |
|---|---|---|
| 1 / R1 | Repliziert sich ein Retrieval-/Spacing-Vorteil für komplexe Inhalte unter Feedback-/Expositionskontrolle? Numerische Moderatorübergriffe, PF und Selbsterklärung prüfen; danach Schlaf, Fatigue, nachhaltige Intensität. | Volltexte der offenen Meta-Analysen, keine universellen Stundenquoten. Null-/Schadensfälle aufnehmen; kein „Neurohack“ aus Korrelaten. |
| 2 / R2 | Welche Unterstützung verbessert verzögerte Beweiskonstruktion bzw. Debugging gegenüber bloßem Definitionsabruf? Getrennte Operatoren und fachlich bewertbare Holdouts liefern. | D3/D6-Primärketten schließen; mathematische Beispielrubriken unabhängig prüfen. Keine Übertragung von Prozedurrechnen auf Beweisen ohne Daten. |
| 3 / R5 | Reduziert ein Tutor Hilfeabhängigkeit und verbessert er unbekannte Aufgaben ohne Tutor? Welche Schadensgrenze ist relevant? | D10-SI/Präregistrierung und D11-Version of Record/Reanalyse; Verzögerung, Ausfälle, Clusterung. Keine Wirksamkeit aus Prompt-Compliance. |
| 4 / R3 | Tragen Retrieval und Beispiele zur juristischen Subsumtion bzw. klinischen Differentialdiagnose bei? | Rechtsstand, konkurrierende vertretbare Lösungen, diagnostische Kalibrierung und Sicherheit; kein Wissensquiz als Berufskompetenz. |
| 5 / R4 | Wann transferieren Simulation/Demonstration auf reale motorische, Labor- oder CAD-Leistung? | Instrumentierte oder externe praktische Prüfung und Sicherheitsaufsicht; Simulationserfolg allein unzureichend. |
| 6 / R9 | Welche Tutorressourcen liefern prüfbare Lerninterventionen und Vergleichsprotokolle gegenüber direktem Modellchat? | R5-Outcomevertrag; vorhandenes Ressourcenregister behalten. Keine neue Tutor-Implementierung. |
| 7 / R7 | Welche Visual-/Coding-Ressourcen ermöglichen die von R2–R4 geforderten Handlungen? | Technische Fähigkeit, Lizenz und Lernwirkung getrennte Spalten; Produktwerbung keine Outcome-Evidenz. |
| 8 / R8 | Wie lassen sich native Anki-Historie und optionaler Markdown-Workspace sicher erhalten, ohne Kompetenzbegriffe zu verwischen? | Datenintegrität getrennt von Lernvalidität; kein eigener Scheduler. Toolfähigkeit versionieren, keinen Erinnerungswert als Transferwahrscheinlichkeit ausgeben. |
| 9 / R6 | Welche minimale Architektur trägt die nachgewiesenen Operationen und kann auf unzureichender Evidenz abstainieren? | Erst nach vorläufigen R1–R5 und relevanten R7–R9-Befunden; Alternativen und unabhängige Kritik, keine automatische Freigabe. |

**Claude-Prioritäten:** (1) D2/D3/D7 erneut extrahieren und abweichende Interpretationen dokumentieren; (2) veröffentlichte Kestin-Fassung einschließlich Supplement gegen v1 vergleichen und Bastani-Analyseplan/Zuteilung prüfen; (3) Renkl/Kalyuga-Primärstudien, Barbieri/Bisra/Sinha vollständig lesen; (4) einen fachlich begründeten Messvertrag für unabhängiges mathematisches Können formulieren. Dies sind Forschungspakete, kein Implementierungsauftrag.

## 9. What we cannot claim

Keine umfassend bewiesene Lernarchitektur, keine unabhängige menschliche Begutachtung, keine repräsentative Fachabdeckung, keine vollständig neu verifizierten 55 Volltexte, keine Lernerdaten, keine Wirksamkeit von Exam Mastery. Keine kausale Auflösung aller Widersprüche. Quellenzugang kann wechseln; ein Mirror ist keine neue Studie. R0 ist vollständig als Triage/gezielter Audit dokumentiert, **die Evidenzbasis selbst ist nicht vollständig validiert**.

Offen bleiben die Volltext-/Methodikprüfung der nicht vertieften Claims (insbesondere 16 bisher metadata_only), die zugrunde liegenden Primärstudien der Reviews, Instrumentvalidität, Retractions-/Update-Screening und unabhängige Doppelprüfung. Ressourcenregistries und neue Neuro-/Domänenliteratur wurden bewusst nicht expandiert. Datenschutz-/Ethikprüfung einer späteren Studie wäre ein eigener Schritt, nicht durch diesen Bericht erfüllt.

## 10. Reproduktion und Prüfstand

Ausgangsdateien und Prüfungen sind in [SEARCH_PROTOCOL.md](SEARCH_PROTOCOL.md) beschrieben; das vorgeschlagene Register in [EVIDENCE_REGISTER_SCHEMA.md](EVIDENCE_REGISTER_SCHEMA.md). Quellen-/Claim-IDs bleiben unverändert. Volltexte werden nicht ins öffentliche Repository kopiert. Nur neue Forschungsprosa, kurze bibliografische Einträge und eigene synthetische Beispiele sind Teil des PR.

Eingabe-SHA256:

| Datei unter `exam_mastery/knowledge/` | SHA256 |
|---|---|
| sources.json | `9f2cc09ecc5f43f5df0359a4759a8c11e11edfc86b92be8948316e602ef0fe1b` |
| principles.json | `8a35e363429c2ed77f598166b31e875d757bd54e9c3ef393bc91717b4f027ce5` |
| specs.json | `b7119c96ad6521621a9d2a68e5473472ab6cd8f21a38a3236b3bf5b6a7dd6c3b` |
| verification.json | `63c2d41d927f16694962caf31d94f26fd3db005bf0e9a8e6826806179ed0293c` |

### Abschlussprüfung der Forschungsdateien (26.11.2026)

Das Shell-Prüfbeispiel aus `SEARCH_PROTOCOL.md` wurde erfolgreich ausgeführt: 55 Quellen und 52 Claims jeweils genau einmal inventarisiert, elf Deep-Review-Abschnitte, 55 bibliografische Cache-Matches und 48 passende Abstract-Ausschnitte. Zusätzlich bestanden: 78 Einträge im breiteren Verifikationsregister, alle relativen Dokumentlinks, Parsing des illustrativen JSON-Datensatzes, Abgleich aller vier oben genannten Eingabe-Hashes sowie exakte rationale Nachrechnung der Varianz- und gewichteten Summenbeispiele. Diese Nachrechnung ersetzt keinen allgemeinen mathematischen Beweis.

Der Veröffentlichungsumfang ist auf diese drei Markdown-Dateien beschränkt. Die lokale Whitespace-Prüfung wird auch am gestagten Diff vor Commit ausgeführt. Keine Engine-Tests, neue Online-Recherche oder Produktionsläufe im Recovery-Schritt; keine wissenschaftliche oder menschliche Freigabe aus den bestandenen Strukturprüfungen.
