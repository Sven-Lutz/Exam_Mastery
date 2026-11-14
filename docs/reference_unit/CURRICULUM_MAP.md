| Kompetenz | Vorlesung | Lehrbuch | Forschung/Vertiefung | Szene | Arbeitsbuch | Prüfung A | Prüfung B | Anki |
|---|---|---|---|---|---|---|---|---|
| Spannenkodierung (IO, BIO, BILOU) (`spans`) | PDF-S. 4–18 | SLP3 §9.5.2 S. 239; §18.3 S. 405 | Ratinov, L.; Roth, D. (2009); Lample, G. et al. (2016); Tjong Kim Sang, E. F.; De Meulder, F. (2003) | – | S1 | A1, A2 (T) | B-1, B-2 (T) | io-not-injective, label-count, conlleval-i, bilou-evidence |
| Abhängigkeitsbereich und BiRNN (`birnn`) | PDF-S. 24–29, 77–80 | SLP3 §14.4–14.4.2 S. 312–314 | Schuster, M.; Paliwal, K. K. (1997) | birnn | G1, W1, B1, B2 | A3, A4 (T) | B-3, B-4 (T) | abhaengigkeit-vorwaerts, washington, definition, latenz, softmax-unabhaengig, params |
| Self-Attention (`attention`) | PDF-S. 31–58, 72–76 | SLP3 §7.1–7.3 S. 179–188 | Vaswani, A. et al. (2017) | attention | AT1 | A5, A6 (T) | B-5, B-6 (T) | formel, gelernt, skalierung, multihead, burger |
| Positionsinformation (`position`) | PDF-S. 60–70 | SLP3 §7.4 S. 191–193 | Vaswani, A. et al. (2017); Su, J. et al. (2024) | attention | PO1 | A7, A8 (T) | B-7, B-8 (T) | permutation, sinus-linear, rope, learned-nachteil |
| Labelabhängigkeiten und Viterbi (`decoding`) | PDF-S. 82–85 | SLP3 §18.4.5–18.5 S. 411–419; §9.5.3 S. 239–241 | Lafferty, J.; McCallum, A.; Pereira, F. (2001); Andor, D. et al. (2016); Ratinov, L.; Roth, D. (2009); Huang, Z.; Xu, W.; Yu, K. (2015); Lample, G. et al. (2016) | viterbi | C1, F1 | A9, A10 (T) | B-9, B-10 (T) | crf-score, garantie, label-vs-exposure, greedy-evidence |
| Precision, Recall, F1 (`prf`) | PDF-S. 20–21 | SLP3 §4.9 S. 112–114 | – | f1 | B7 | A11, A12 (T) | B-11, B-12 (T) | zaehlform, schranke, keine-tn |
| Grenzfälle mit Nenner 0 (`prf-edge`) | – (Vertiefung) | SLP3 §4.9; scikit-learn zero_division | scikit-learn 1.9.1, sklearn.metrics.precision_recall_fscore_support, Parameter zero_division (Abruf 14.11.2026). | f1 | B3 | A13, A14 | B-13, B-14 | nichts-ausgegeben, tp-null, beide-leer |
| Phrasen- vs. Token-Zählung (`prf-level`) | PDF-S. 21–22 | SLP3 §9.5.4 S. 241 | Tjong Kim Sang, E. F.; De Meulder, F. (2003); Manning, C. (2006) | counter | B4, B5 | A15, A16 (T) | B-15, B-16 (T) | doppelt, rangfolge |
| Micro- und Macro-Mittelung (`micro-macro`) | – (Vertiefung) | SLP3 §4.9.1 S. 114–115 | Opitz, J.; Burst, S. (2019) | micromacro | B6 | A17, A18 | B-17, B-18 (T) | gewicht, unterschied, accuracy |

