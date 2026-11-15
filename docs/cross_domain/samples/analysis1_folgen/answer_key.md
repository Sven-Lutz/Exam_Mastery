# Lösungsschlüssel Analysis 1 – Konvergenz von Folgen

Nur hochladen, wenn der Tutor Antworten prüfen soll. Der Tutor gibt Lösungen erst nach eigenem Versuch preis.

## AN1
**Kurzschlüssel.** |aₙ − 2| = 7/(n+3); N(ε) = ⌊7/ε − 3⌋ + 1; für ε = 1/100: N = 698.

**Ausführliche Lösung.** aₙ − 2 = (2n − 1 − 2n − 6)/(n+3) = −7/(n+3), also |aₙ − 2| = 7/(n+3). Sei ε > 0. Für n > 7/ε − 3 gilt 7/(n+3) < ε. Wähle N als kleinste natürliche Zahl > 7/ε − 3. Da 7/(n+3) in n fällt, gilt die Ungleichung für alle n ≥ N. Für ε = 1/100: n > 697, also N = 698; für n = 697 ist 7/700 = 1/100 nicht kleiner als ε.

**Bewertung.** Abstand exakt umgeformt (2 P.) · N in Abhängigkeit von ε und Monotonie-Argument für alle n ≥ N (2 P.) · Randfall n = 697 (1 P.)

## AN2
**Kurzschlüssel.** AM-GM ⇒ aₙ₊₁ ≥ √2; aₙ₊₁ − aₙ = (2 − aₙ²)/(2aₙ) ≤ 0; monoton und beschränkt ⇒ konvergent; Grenzwert a = (a + 2/a)/2 ⇒ a² = 2, a ≥ √2 > 0 ⇒ a = √2. Für a₁ = −1: −√2.

**Ausführliche Lösung.** Induktiv aₙ > 0 (Summe positiver Zahlen). Für x > 0 gilt (x + 2/x)/2 − √2 = (x − √2)²/(2x) ≥ 0, also aₙ₊₁ ≥ √2. Damit aₙ² ≥ 2 für n ≥ 1 (a₁ = 2), und aₙ₊₁ − aₙ = (2 − aₙ²)/(2aₙ) ≤ 0. Monoton fallend und durch √2 nach unten beschränkt ⇒ konvergent (Theorem 2.14), Grenzwert a ≥ √2. Grenzübergang in 2aₙ₊₁aₙ = aₙ² + 2 liefert 2a² = a² + 2, a² = 2, also a = √2. Fehler: aₙ₊₁ − √2 = (aₙ − √2)²/(2aₙ) – quadratische Konvergenz. Für a₁ = −1 ist die Folge negativ (Symmetrie f(−x) = −f(x)); dasselbe Argument liefert −√2. Die Fixpunktgleichung allein hat zwei Lösungen; erst die Vorzeichen-Invarianz wählt die richtige.

**Bewertung.** Positivität und untere Schranke (2 P.) · Monotonie (1 P.) · Satz 2.14 korrekt angewendet (1 P.) · Wahl der Wurzel begründet (1 P.) · negativer Start (1 P.)

## AN3
**Kurzschlüssel.** aₙ = √n: |aₙ₊₁ − aₙ| = 1/(√(n+1) + √n) → 0, aber unbeschränkt, also divergent. Cauchy verlangt |aₘ − aₙ| < ε für ALLE m, n ≥ N.

**Ausführliche Lösung.** Für aₙ = √n gilt √(n+1) − √n = 1/(√(n+1) + √n) ≤ 1/(2√n) → 0. Aber aₙ ist unbeschränkt, also nicht konvergent (Satz 2.4) und damit nicht Cauchy (in ℝ äquivalent). Fehler: Die Cauchy-Bedingung kontrolliert beliebig weite Abstände aₘ − aₙ, nicht nur Nachbarn; die Summe vieler kleiner Schritte kann beliebig groß werden (vgl. Bemerkung 2.28 der Vorlesung).

**Bewertung.** korrektes Gegenbeispiel mit Rechnung (2 P.) · Fehler präzise benannt (1 P.)

## AN4
**Kurzschlüssel.** q = sin 1 ≈ 0,8415 auf [cos 1, 1]; |a₂ − a₁| = 1 − cos 1 ≈ 0,4597; kleinstes n mit qⁿ⁻¹/(1−q)·0,4597 ≤ 10⁻³ ist n = 48 (tatsächlich reichen 16).

**Ausführliche Lösung.** cos fällt auf [0, 1]; mit c = cos 1 ≈ 0,5403 gilt cos([c, 1]) = [cos 1, cos c] ≈ [0,5403; 0,8576] ⊂ [c, 1]. Also bleiben alle aₙ in [c, 1]. Nach dem Mittelwertsatz |cos x − cos y| ≤ (max_{[c,1]} |sin|)|x − y| = sin(1)|x − y|, q = sin 1 < 1. Damit |aₙ₊₂ − aₙ₊₁| ≤ q|aₙ₊₁ − aₙ| (Satz 2.31) ⇒ Cauchy ⇒ konvergent, und der Grenzwert erfüllt a = cos a. A-priori: |aₙ − a| ≤ Σ_{k≥n} |aₖ₊₁ − aₖ| ≤ qⁿ⁻¹/(1−q)·|a₂ − a₁|. Mit 1 − q ≈ 0,1585: qⁿ⁻¹ ≤ 3,45·10⁻⁴ ⇒ n − 1 ≥ 47, n = 48. Numerisch genügen 16 Glieder: Die Schranke nutzt das ungünstigste q auf dem ganzen Intervall.

**Bewertung.** invariantes Intervall (2 P.) · q über Mittelwertsatz (2 P.) · a-priori-Schranke und n (2 P.) · Deutung pessimistische Schranke (1 P.)
