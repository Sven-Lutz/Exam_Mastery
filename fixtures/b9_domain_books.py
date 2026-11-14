"""Three short DEMONSTRATION chapters (mathematics, law, machine learning) for the B9 typesetting and rule checks.

Written for Exam Mastery as clearly labelled fixtures: standard textbook knowledge, not taken from any course and
not independently reviewed. They prove that the layout, the rule set and the Anki v2 deck handle proofs and
formulas, legal case analysis and pseudocode; they say nothing about the quality of model-produced chapters.
"""

STATUS = '**DEMONSTRATIONSKAPITEL (Fixture):** selbst verfasstes Standardwissen zur Prüfung von Satz, Regeln und Karten; kein Kursinhalt, nicht fachlich begutachtet.'


def _meta(title, course, no):
    return {'title': title, 'course': course, 'chapter_no': no, 'lang': 'de', 'date': '08.11.2026', 'engine': 'fixture', 'status_line': STATUS}


def _stages(items):
    titles = ['Grundverständnis', 'Anwendung', 'Rechnen und Herleiten', 'Transfer']
    return [{'title': titles[k], 'level': k + 1, 'items': [items[k]]} for k in range(4)]


def _it(no, prompt, op, kc, steps, answer, err, faded=False, points=None, rubric=None):
    d = {'id': f'w{no}', 'no': no, 'prompt': prompt, 'operation': op, 'kc_keys': [kc], 'space': 40, 'faded': faded,
         'solution': {'steps': [[s] for s in steps], 'answer': answer, 'errors': [err]}}
    if points:
        d['points'] = points; d['solution']['rubric'] = rubric
    return d


MATH = {
    'meta': _meta('Lineare Ausgleichsrechnung', 'Demonstration Mathematik', 3), 'quantitative': True, 'figures': {},
    'sections': [
        {'title': 'Das Problem der kleinsten Quadrate', 'blocks': [
            {'type': 'lead', 'md': 'Messdaten passen selten exakt zu einem Modell. Die Methode der kleinsten Quadrate wählt die Parameter so, '
                                   'dass die Summe der quadrierten Abweichungen minimal wird – und führt auf ein lineares Gleichungssystem.'},
            {'type': 'definition', 'term': 'Kleinste-Quadrate-Lösung', 'prov': 'didactic', 'md':
             'Für \\(A \\in \\mathbb{R}^{m \\times n}\\) mit \\(m \\ge n\\) und \\(b \\in \\mathbb{R}^m\\) heißt \\(\\hat{x}\\) Kleinste-Quadrate-Lösung, '
             'wenn \\(\\lVert A\\hat{x} - b \\rVert_2 \\le \\lVert Ax - b \\rVert_2\\) für alle \\(x \\in \\mathbb{R}^n\\).'},
            {'type': 'box', 'kind': 'key', 'title': 'Satz (Normalgleichungen)', 'prov': 'didactic', 'md':
             '\\(\\hat{x}\\) ist genau dann Kleinste-Quadrate-Lösung, wenn \\[A^\\top A\\,\\hat{x} = A^\\top b.\\] Hat \\(A\\) vollen Spaltenrang, '
             'ist \\(A^\\top A\\) invertierbar und die Lösung eindeutig.'},
            {'type': 'example', 'label': 'Beweis', 'title': 'Normalgleichungen über Orthogonalität', 'prov': 'didactic',
             'given': 'Zu zeigen: \\(\\hat{x}\\) minimiert \\(\\lVert Ax - b\\rVert_2\\) genau dann, wenn \\(A^\\top(A\\hat{x} - b) = 0\\).',
             'steps': [['Für beliebiges \\(x\\) setze \\(d = x - \\hat{x}\\) und \\(r = A\\hat{x} - b\\).', 'Zerlegung des Residuums.'],
                       ['\\(\\lVert Ax - b \\rVert^2 = \\lVert r + Ad \\rVert^2 = \\lVert r \\rVert^2 + 2\\,d^\\top A^\\top r + \\lVert Ad \\rVert^2\\).', 'Ausmultiplizieren des Skalarprodukts.'],
                       ['Gilt \\(A^\\top r = 0\\), so ist \\(\\lVert Ax - b\\rVert^2 = \\lVert r\\rVert^2 + \\lVert Ad\\rVert^2 \\ge \\lVert r\\rVert^2\\).', 'Der Mischterm verschwindet; \\(\\hat{x}\\) ist minimal.'],
                       ['Ist umgekehrt \\(A^\\top r \\neq 0\\), so senkt \\(x = \\hat{x} - t\\,A^\\top r\\) für kleines \\(t > 0\\) den Wert.', 'Der lineare Term \\(-2t\\lVert A^\\top r\\rVert^2\\) dominiert den quadratischen.']],
             'result': 'Also ist \\(A^\\top r = 0\\), d. h. \\(A^\\top A\\hat{x} = A^\\top b\\), notwendig und hinreichend. \\(\\square\\)'},
            {'type': 'misconception', 'wrong': 'Man löst \\(Ax = b\\) einfach, indem man beide Seiten durch \\(A\\) teilt.',
             'right': 'Für \\(m > n\\) ist \\(A\\) nicht invertierbar; das System ist meist unlösbar. Man löst stattdessen die Normalgleichungen.',
             'why': 'Gesucht ist kein exaktes, sondern das bestmögliche \\(x\\) im Sinne der euklidischen Norm.'},
            {'type': 'summary', 'md': 'Die Kleinste-Quadrate-Lösung macht das Residuum orthogonal zum Spaltenraum von \\(A\\); daraus folgen die Normalgleichungen, die bei vollem Spaltenrang eindeutig lösbar sind.'}]}],
    'stages': _stages([
        _it('1', 'Geben Sie die Normalgleichungen zu \\(A\\) und \\(b\\) an.', 'RECALL', 'ls', ['\\(A^\\top A x = A^\\top b\\)'], '\\(A^\\top A\\hat{x} = A^\\top b\\)', '\\(AA^\\top\\) statt \\(A^\\top A\\) schreiben.'),
        _it('2', 'Unter welcher Bedingung an \\(A\\) ist die Kleinste-Quadrate-Lösung eindeutig?', 'EXPLAIN', 'ls', ['Voller Spaltenrang ⇒ \\(A^\\top A\\) invertierbar.'], 'Wenn \\(A\\) vollen Spaltenrang hat.', 'Quadratische Matrix verlangen.'),
        _it('3', 'Berechnen Sie die Ausgleichsgerade \\(y = c\\) (Konstante) für die Messwerte 2, 4, 9.', 'CALCULATE', 'ls',
            ['\\(A = (1,1,1)^\\top\\), \\(A^\\top A = 3\\), \\(A^\\top b = 2 + 4 + 9 = 15\\).', '\\(c = 15 / 3 = 5\\).'], '\\(c = 5\\): der Mittelwert.', 'Median statt Mittelwert nehmen.', faded=True),
        _it('4', 'Zeigen Sie, dass das Residuum der Kleinste-Quadrate-Lösung orthogonal zu jeder Spalte von \\(A\\) ist.', 'PROVE', 'ls',
            ['Aus den Normalgleichungen folgt \\(A^\\top(A\\hat{x} - b) = 0\\).', 'Die \\(j\\)-te Zeile ist das Skalarprodukt der \\(j\\)-ten Spalte mit dem Residuum.'], 'Jede Komponente von \\(A^\\top r\\) ist null.', 'Orthogonalität zu den Zeilen behaupten.')]),
    'competencies': [{'key': 'ls', 'operation': 'CALCULATE'}],
    'cards': [{'key': 'ls/normal-equations', 'kind': 'math', 'front': 'Wie lauten die Normalgleichungen des Ausgleichsproblems \\(\\min \\lVert Ax - b\\rVert_2\\)?',
               'answer': '\\(A^\\top A\\,x = A^\\top b\\)', 'source': 'Demonstration'},
              {'key': 'ls/residual-orthogonal', 'kind': 'mechanism', 'front': 'Welche geometrische Eigenschaft hat das Residuum der Kleinste-Quadrate-Lösung?',
               'answer': 'Es steht senkrecht auf dem Spaltenraum von \\(A\\): \\(A^\\top(A\\hat{x} - b) = 0\\).', 'source': 'Demonstration',
               'explanation': 'Wäre ein Rest des Residuums parallel zum Spaltenraum, könnte man ihn durch eine bessere Wahl von \\(x\\) abziehen und den Abstand verkleinern.'}],
}

LAW = {
    'meta': _meta('Der Kaufvertrag', 'Demonstration Recht', 1), 'quantitative': False, 'figures': {},
    'sections': [
        {'title': 'Pflichten aus dem Kaufvertrag', 'blocks': [
            {'type': 'lead', 'md': 'Der Kaufvertrag ist der häufigste Vertrag des Alltags. Wer seine Hauptpflichten kennt, kann jeden Kauffall strukturiert prüfen.'},
            {'type': 'box', 'kind': 'law', 'title': '§ 433 BGB (Auszug, sinngemäß)', 'prov': 'didactic', 'md':
             'Der Verkäufer ist verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum zu verschaffen, frei von Sach- und Rechtsmängeln (Abs. 1). '
             'Der Käufer ist verpflichtet, den vereinbarten Kaufpreis zu zahlen und die Sache abzunehmen (Abs. 2).'},
            {'type': 'table', 'caption': 'Hauptpflichten im Überblick.', 'columns': ['Partei', 'Hauptpflicht', 'Norm'],
             'rows': [['Verkäufer', 'Übergabe und Eigentumsverschaffung, mangelfrei', '§ 433 Abs. 1 BGB'], ['Käufer', 'Kaufpreiszahlung, Abnahme', '§ 433 Abs. 2 BGB']]},
            {'type': 'example', 'label': 'Prüfung am Fall', 'title': 'Anspruch auf Kaufpreiszahlung', 'prov': 'didactic',
             'given': 'V verkauft K ein Fahrrad für 300 €. K holt das Rad ab, zahlt aber nicht. Hat V gegen K einen Anspruch auf Zahlung von 300 €?',
             'steps': [['Obersatz: V könnte gegen K einen Anspruch auf Zahlung von 300 € aus § 433 Abs. 2 BGB haben.', 'Gutachtenstil: Hypothese zuerst.'],
                       ['Voraussetzung: wirksamer Kaufvertrag durch Angebot und Annahme (§§ 145 ff. BGB).', 'Einigung über Sache und Preis liegt vor.'],
                       ['Subsumtion: V und K haben sich über das Fahrrad und 300 € geeinigt.', 'Sachverhalt unter die Merkmale ordnen.'],
                       ['Keine Einwendungen ersichtlich (z. B. Erfüllung, Anfechtung).', 'Einwendungen prüfen, bevor man schließt.']],
             'result': 'Ergebnis: V hat gegen K einen Anspruch auf Zahlung von 300 € aus § 433 Abs. 2 BGB.'},
            {'type': 'misconception', 'wrong': 'Mit dem Kaufvertrag wird der Käufer automatisch Eigentümer.',
             'right': 'Der Kaufvertrag verpflichtet nur; das Eigentum geht erst durch die Übereignung über (Trennungsprinzip).',
             'why': 'Verpflichtungs- und Verfügungsgeschäft sind getrennte Rechtsgeschäfte.'},
            {'type': 'summary', 'md': 'Der Kaufvertrag begründet gegenseitige Pflichten; Ansprüche prüft man im Gutachtenstil vom Obersatz über Voraussetzungen und Subsumtion zum Ergebnis.'}]}],
    'stages': _stages([
        _it('1', 'Nennen Sie die Hauptpflichten des Verkäufers aus § 433 Abs. 1 BGB.', 'RECALL', 'kauf', ['Übergabe, Eigentumsverschaffung, mangelfrei.'], 'Übergabe und Eigentumsverschaffung, frei von Mängeln.', 'Nur die Übergabe nennen.'),
        _it('2', 'Erklären Sie das Trennungsprinzip am Beispiel eines Kaufs.', 'EXPLAIN', 'kauf', ['Kaufvertrag verpflichtet.', 'Übereignung verfügt.'], 'Verpflichtung (Kaufvertrag) und Verfügung (Übereignung) sind getrennt.', 'Beide Geschäfte gleichsetzen.'),
        _it('3', 'Prüfen Sie im Gutachtenstil: K bestellt bei V ein Buch für 20 €, V liefert nicht. Hat K gegen V einen Anspruch auf Übergabe und Übereignung?', 'SUBSUME', 'kauf',
            ['Obersatz: Anspruch aus § 433 Abs. 1 S. 1 BGB.', 'Kaufvertrag: Einigung über Buch und Preis.', 'Keine Einwendungen.'], 'Ja, aus § 433 Abs. 1 S. 1 BGB.', 'Mit dem Ergebnis beginnen (Urteilsstil).'),
        _it('4', 'Warum muss in einer Fallprüfung auch nach Einwendungen gefragt werden?', 'EXPLAIN', 'kauf', ['Ein entstandener Anspruch kann erloschen oder nicht durchsetzbar sein.'], 'Weil ein Anspruch trotz Entstehung erloschen (z. B. Erfüllung) oder gehemmt sein kann.', 'Prüfung nach den Voraussetzungen abbrechen.')]),
    'competencies': [{'key': 'kauf', 'operation': 'SUBSUME'}],
    'cards': [{'key': 'kauf/seller-duties', 'kind': 'concept', 'front': 'Welche Hauptpflichten hat der Verkäufer nach § 433 Abs. 1 BGB?',
               'answer': 'Übergabe der Sache und Verschaffung des Eigentums, frei von Sach- und Rechtsmängeln.', 'source': 'Demonstration'},
              {'key': 'kauf/separation-principle', 'kind': 'misconception', 'front': 'Wird der Käufer schon mit Abschluss des Kaufvertrags Eigentümer?',
               'answer': 'Nein. Der Kaufvertrag verpflichtet nur; das Eigentum geht erst durch die Übereignung über.', 'source': 'Demonstration',
               'explanation': 'Trennungsprinzip: Verpflichtungsgeschäft (§ 433 BGB) und Verfügungsgeschäft (§ 929 BGB) sind getrennte Rechtsgeschäfte.'}],
}

ML = {
    'meta': _meta('Gradientenabstieg', 'Demonstration Machine Learning', 2), 'quantitative': True, 'figures': {},
    'sections': [
        {'title': 'Optimierung durch Gradientenabstieg', 'blocks': [
            {'type': 'lead', 'md': 'Fast jedes Lernverfahren minimiert eine Verlustfunktion. Gradientenabstieg tut das schrittweise: Er geht in die Richtung, in der der Verlust am stärksten fällt.'},
            {'type': 'definition', 'term': 'Gradientenschritt', 'prov': 'didactic', 'md':
             'Für eine differenzierbare Verlustfunktion \\(L(\\theta)\\) und eine Lernrate \\(\\eta > 0\\) ist \\[\\theta_{t+1} = \\theta_t - \\eta\\,\\nabla L(\\theta_t).\\]'},
            {'type': 'text', 'prov': 'didactic', 'md': 'Der Algorithmus in Pseudocode:\n\n```\ntheta = theta_0\nfor t in range(T):\n    g = grad_L(theta)          # Gradient am aktuellen Punkt\n    theta = theta - eta * g    # Schritt entgegen dem Gradienten\n    if norm(g) < tol: break    # Abbruch bei kleinem Gradienten\nreturn theta\n```'},
            {'type': 'example', 'title': 'Zwei Schritte auf einer Parabel', 'prov': 'didactic',
             'given': '\\(L(\\theta) = (\\theta - 3)^2\\), also \\(\\nabla L(\\theta) = 2(\\theta - 3)\\); Start \\(\\theta_0 = 0\\), Lernrate \\(\\eta = 0.25\\).',
             'steps': [['\\(\\theta_1 = 0 - 0.25 \\cdot 2 \\cdot (0 - 3) = 1.5\\)', 'Gradient am Start ist −6.'],
                       ['\\(\\theta_2 = 1.5 - 0.25 \\cdot 2 \\cdot (1.5 - 3) = 2.25\\)', 'Der Abstand zum Minimum halbiert sich je Schritt.']],
             'result': 'Mit \\(\\eta = 0.25\\) gilt \\(\\theta_t - 3 = 0.5^t\\,(\\theta_0 - 3)\\); das Verfahren konvergiert gegen 3.'},
            {'type': 'box', 'kind': 'pitfall', 'title': 'Zu große Lernrate', 'md': 'Bei \\(\\eta = 1.25\\) wird \\(\\theta_t - 3 = (-1.5)^t(\\theta_0 - 3)\\): Die Iteration schwingt mit wachsender Amplitude und divergiert.'},
            {'type': 'summary', 'md': 'Gradientenabstieg folgt dem negativen Gradienten; die Lernrate entscheidet über Konvergenz, Geschwindigkeit oder Divergenz.'}]}],
    'stages': _stages([
        _it('1', 'Geben Sie die Update-Regel des Gradientenabstiegs an.', 'RECALL', 'gd', ['\\(\\theta_{t+1} = \\theta_t - \\eta\\nabla L(\\theta_t)\\)'], '\\(\\theta_{t+1} = \\theta_t - \\eta\\nabla L(\\theta_t)\\)', 'Plus statt Minus.'),
        _it('2', 'Warum kann eine zu große Lernrate zur Divergenz führen?', 'EXPLAIN', 'gd', ['Der Schritt überspringt das Minimum.', 'Der Fehler wächst mit Faktor \\(|1 - 2\\eta| > 1\\).'], 'Weil jeder Schritt über das Minimum hinausschießt und der Abstand wächst.', 'Nur „zu schnell“ sagen.'),
        _it('3', 'Berechnen Sie für \\(L(\\theta) = (\\theta - 3)^2\\), \\(\\theta_0 = 1\\), \\(\\eta = 0.1\\) den Wert \\(\\theta_1\\).', 'CALCULATE', 'gd',
            ['\\(\\nabla L(1) = 2 \\cdot (1 - 3) = -4\\)', '\\(\\theta_1 = 1 - 0.1 \\cdot (-4) = 1.4\\)'], '\\(\\theta_1 = 1.4\\)', 'Vorzeichen des Gradienten vertauschen.', faded=True),
        _it('4', 'Für welche Lernraten konvergiert Gradientenabstieg auf \\(L(\\theta) = (\\theta - 3)^2\\)? Begründen Sie.', 'EXPLAIN', 'gd',
            ['\\(\\theta_{t+1} - 3 = (1 - 2\\eta)(\\theta_t - 3)\\).', 'Konvergenz genau bei \\(|1 - 2\\eta| < 1\\), also \\(0 < \\eta < 1\\).'], '\\(0 < \\eta < 1\\).', '\\(\\eta < 2\\) angeben.')]),
    'competencies': [{'key': 'gd', 'operation': 'CALCULATE'}],
    'cards': [{'key': 'gd/update-rule', 'kind': 'math', 'front': 'Wie lautet die Update-Regel des Gradientenabstiegs mit Lernrate \\(\\eta\\)?',
               'answer': '\\(\\theta_{t+1} = \\theta_t - \\eta\\,\\nabla L(\\theta_t)\\)', 'source': 'Demonstration'},
              {'key': 'gd/learning-rate', 'kind': 'condition', 'front': 'Für welche Lernraten konvergiert Gradientenabstieg auf \\((\\theta - 3)^2\\)?',
               'answer': 'Für \\(0 < \\eta < 1\\), denn der Fehler schrumpft je Schritt um den Faktor \\(|1 - 2\\eta|\\).', 'source': 'Demonstration'}],
}

BOOKS = {'math': MATH, 'law': LAW, 'ml': ML}
