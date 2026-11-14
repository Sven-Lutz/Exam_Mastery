"""B9: product quality layer: didactic rules, numeric checks, exam integrity, typesetting, Anki v2 identities and updates."""
import json
import tempfile
import unittest
from pathlib import Path

from exam_mastery import anki_v2, didactic_rules, figures_svg, numeric_checks, typeset
from exam_mastery.common import ContractError


def mini_book(**over):
    book = {'meta': {'title': 'Test', 'course': 'Kurs', 'chapter_no': 1, 'status_line': 's', 'date': 'd', 'engine': 'x', 'lang': 'de'},
            'figures': {'f': {'type': 'bar', 'data': [['a', 1.0], ['b', 2.0]], 'source': 'Folie 1'}},
            'sections': [{'title': 'A', 'blocks': [
                {'type': 'lead', 'md': 'Worum es geht und warum es wichtig ist.'},
                {'type': 'definition', 'term': 'Begriff', 'md': 'Die Bedeutung ist klar und wird erklärt.'},
                {'type': 'figure', 'id': 'f', 'caption': 'c'},
                {'type': 'table', 'caption': 't', 'columns': ['x', 'n'], 'numeric': [1], 'rows': [['a', '1'], ['b', '2'], {'cells': ['Summe', '3'], 'total': True}]},
                {'type': 'misconception', 'wrong': 'falsch', 'right': 'richtig'},
                {'type': 'example', 'title': 'E', 'given': 'g', 'steps': [['\\(1 + 2 = 3\\)']], 'result': 'r'},
                {'type': 'summary', 'md': 'Zusammenhang der Begriffe.'}]}],
            'stages': [{'title': f'S{k}', 'level': k, 'items': [
                {'id': f'w{k}', 'no': str(k), 'prompt': 'Berechnen Sie die Summe von 1 und 2.', 'operation': 'CALCULATE', 'kc_keys': ['k'],
                 'faded': k == 1, 'solution': {'steps': [['\\(1 + 2 = 3\\)']], 'answer': '3', 'errors': ['4']}}]} for k in range(1, 5)],
            'competencies': [{'key': 'k', 'operation': 'CALCULATE'}], 'quantitative': True,
            'exam': {'subtitle': 's', 'self_designed_notice': 'selbst entworfen', 'header': [['Punkte', '3']], 'total_points': 3,
                     'items': [{'id': 'k1', 'no': '1', 'topic': 't', 'points': 3, 'prompt': 'p',
                                'solution': {'steps': [['x']], 'answer': 'a', 'rubric': [['r1', 2], ['r2', 1]]}}]},
            'cards': [{'key': 'k/def', 'kind': 'concept', 'front': 'Was bedeutet der Begriff?', 'answer': 'Die Bedeutung.', 'source': 'Folie 1'}]}
    book.update(over)
    return book


class DidacticRules(unittest.TestCase):
    def test_clean_book_passes(self):
        res = didactic_rules.check_book(mini_book())
        self.assertEqual(didactic_rules.blocking(res), [], res)

    def test_meta_language_of_the_old_products_is_blocked(self):
        b = mini_book()
        b['sections'][0]['blocks'].insert(1, {'type': 'text', 'md': 'The permitted text states that the lecture says so, laut Folie.'})
        rules = {r['rule'] for r in didactic_rules.blocking(didactic_rules.check_book(b))}
        self.assertIn('T6', rules)
        self.assertEqual(didactic_rules.meta_language('Quelle: laut Folie 6 sind es zehn'), [])   # concrete reference is fine

    def test_mixed_language_is_blocked(self):
        b = mini_book()
        b['sections'][0]['blocks'].insert(1, {'type': 'text', 'md': 'The lifecycle label provides context rather than a financing guarantee, and the stages of the venture are different for this reason. This is the view of the lecture and it should be read with care because the labels are not a promise of the investors.'})
        self.assertIn('T7', {r['rule'] for r in didactic_rules.blocking(didactic_rules.check_book(b))})

    def test_alignment_and_progression(self):
        b = mini_book(competencies=[{'key': 'k', 'operation': 'EXPLAIN'}])
        self.assertIn('A1', {r['rule'] for r in didactic_rules.blocking(didactic_rules.check_book(b))})
        b = mini_book(); b['stages'] = b['stages'][:2]
        self.assertIn('A2', {r['rule'] for r in didactic_rules.blocking(didactic_rules.check_book(b))})

    def test_old_essay_card_fails_card_rules(self):
        old = {'key': 'k/x', 'kind': 'concept', 'source': 's',
               'front': 'Erklären Sie die Trennung zwischen Insolvenzgründen und Managementverantwortung in der Vorlesungsdarstellung. Gehen Sie insbesondere darauf ein, weshalb die Gründe Zahlungsunfähigkeit, drohende Zahlungsunfähigkeit und Überschuldung genannt werden.',
               'answer': 'Insolvenzgründe betreffen die Unternehmenslage; die Vorlesung nennt die drei Gründe und verlangt Handeln sowie Behördeninformation; ihre Fristaussage bleibt hier eine Wiedergabe des Vorlesungstextes, und im Vorlesungstext steht es so.'}
        p = anki_v2.card_lint(old)
        self.assertTrue(any('essay-style' in x for x in p) and any('T6' in x for x in p), p)
        self.assertEqual(anki_v2.card_lint({'key': 'k/c', 'kind': 'cloze', 'text': 'A {{c1::B}} C', 'source': 's'}), [])


class Numbers(unittest.TestCase):
    def test_equations_recomputed(self):
        eq = numeric_checks.equations('\\(0.15 \\cdot 1{,}700{,}000 / 0.85 = 300{,}000\\) und 150 + 100 = 250 und 150 + 100 = 260 und 25,000 / 33,350 = 74.96 %')
        self.assertEqual([e[3] for e in eq], [True, True, False, True])

    def test_table_totals_like_slide_49(self):
        t = {'type': 'table', 'caption': 'x', 'columns': ['p', 'nom', 'pct'], 'numeric': [1, 2],
             'rows': [['a', '25,000', '56.22'], ['b', '3,350', '7.53'], ['c', '6,650', '14.95'], ['d', '9,500', '21.36'],
                      {'cells': ['Summe', '44,467', '100.06'], 'total': True}]}
        r = numeric_checks.table_total(t)
        self.assertEqual([x['ok'] for x in r], [False, True])          # amounts do not add up; the stated 100.06 % does
        b = mini_book(); b['sections'][0]['blocks'].append(dict(t, known_inconsistency='explained'))
        self.assertIn('DOCUMENTED', {x['status'] for x in numeric_checks.check_book_numbers(b)})

    def test_excluded_cell(self):
        t = {'caption': 'x', 'columns': ['l', 'v'], 'numeric': [1], 'exclude_cells': [[2, 1]],
             'rows': [['A', '150'], ['B', '200'], ['C', '100'], {'cells': ['Summe', '350'], 'total': True}]}
        self.assertTrue(numeric_checks.table_total(t)[0]['ok'])


class ExamIntegrity(unittest.TestCase):
    def test_gap_item_missing_solution_and_rubric_mismatch_refused(self):
        b = mini_book()
        self.assertEqual(typeset.exam_check(b), [])
        b['exam']['items'].append({'id': 'a-17', 'no': '2', 'topic': 't', 'points': 2, 'prompt': 'p', 'evidence_gap': True, 'solution': {}})
        b['exam']['total_points'] = 5
        p = typeset.exam_check(b)
        self.assertTrue(any('evidence-gap' in x for x in p) and any('no solution' in x for x in p) and any('rubric' in x for x in p))
        with self.assertRaises(ContractError):
            typeset.publish_book(b, tempfile.mkdtemp())
        b = mini_book(); b['exam']['self_designed_notice'] = ''
        self.assertIn('exam is not labelled as self-designed', typeset.exam_check(b))


class Figures(unittest.TestCase):
    def test_all_types_render_valid_svg(self):
        import xml.etree.ElementTree as ET
        specs = [{'type': 'bar', 'data': [['a', 1], ['b', 2]]}, {'type': 'stacked_bar', 'categories': ['x'], 'series': [['s', [1]], ['t', [2]]]},
                 {'type': 'process', 'steps': [['A', 'eine lange Beschreibung mit vielen Wörtern'], ['B']]},
                 {'type': 'cycle_hub', 'inner': ['a', 'b', 'c'], 'satellites': [['M', 'tl']]},
                 {'type': 'phases', 'groups': [['G', ['p1', 'p2']]], 'rows': [['r', [['x', 0, 2]]]]},
                 {'type': 'ladder', 'rows': [['A', ['x']]]}, {'type': 'share_bars', 'rows': [['r', [['a', 60], ['b', 40]]]]}]
        for s in specs:
            ET.fromstring(figures_svg.render(s))
        with self.assertRaises(ValueError):
            figures_svg.render({'type': 'pie'})


class Typeset(unittest.TestCase):
    def test_markup(self):
        self.assertIn('<strong>x</strong>', typeset.md('**x**'))
        self.assertIn('\\(a*b\\)', typeset.md('\\(a*b\\)'))                     # math untouched
        self.assertIn('<table>', typeset.md('| a | b |\n|---|---|\n| 1 | 2 |'))

    def test_documents_have_own_numbering_toc_and_bookmarks(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            res = typeset.publish_book(mini_book(), td)
            self.assertEqual(set(res), {'1_Lehrbuch', '2_Arbeitsbuch', '3_Musterloesungen', '4_Probeklausur', '5_Probeklausur_Loesungen'})
            d = pymupdf.open(res['1_Lehrbuch']['pdf'])
            self.assertTrue(d.get_toc())
            last = d[d.page_count - 1].get_text()
            self.assertIn(f'{d.page_count - 1} / {d.page_count - 1}', last)    # cover not counted, numbering starts at 1
            ex = pymupdf.open(res['4_Probeklausur']['pdf']).get_text('text') if hasattr(pymupdf.open(res['4_Probeklausur']['pdf']), 'get_text') else \
                ''.join(p.get_text() for p in pymupdf.open(res['4_Probeklausur']['pdf']))
            self.assertNotIn('Bewertung', ex)                                 # no solutions in the question paper
            sol = ''.join(p.get_text() for p in pymupdf.open(res['5_Probeklausur_Loesungen']['pdf']))
            self.assertIn('Bewertung', sol)


class AnkiV2(unittest.TestCase):
    def cards(self, answer2='Antwort zwei.'):
        return [{'key': 'topic/one', 'kind': 'concept', 'front': 'Frage eins?', 'answer': 'Antwort eins.', 'source': 'Folie 1'},
                {'key': 'topic/two', 'kind': 'mechanism', 'front': 'Frage zwei?', 'answer': answer2, 'source': 'Folie 2'},
                {'key': 'topic/gap', 'kind': 'cloze', 'text': 'Die Frist beträgt {{c1::drei}} bzw. {{c2::sechs}} Wochen.', 'source': 'InsO'}]

    def test_update_keeps_identity_scheduling_and_history(self):
        try:
            from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
        except ImportError:
            self.skipTest('anki not installed')
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            r1 = anki_v2.build_deck(self.cards(), 'EM::Test', 'course', 'chapter', t / 'v1', state_dir=t)
            self.assertEqual((r1['notes'], r1['cards']), (3, 4))
            user = Collection(str(t / 'user.anki2'))
            try:
                opts = ImportAnkiPackageOptions(merge_notetypes=False, with_scheduling=False, with_deck_configs=False)
                user.import_anki_package(ImportAnkiPackageRequest(package_path=r1['package'], options=opts))
                user.decks.select(user.decks.id('EM::Test'))
                for _ in range(4):                                   # real reviews through Anki's scheduler
                    q = user.sched.get_queued_cards(fetch_limit=1)
                    if not q.cards:
                        break
                    card = user.get_card(q.cards[0].card.id); card.start_timer()
                    states = user._backend.get_scheduling_states(card.id)
                    from anki.scheduler_pb2 import CardAnswer
                    user.sched.answer_card(user.sched.build_answer(card=card, states=states, rating=CardAnswer.GOOD))
                before = user.db.all('select id, nid, type, queue, due, ivl, reps from cards order by id')
                revlog = user.db.all('select * from revlog order by id')
                self.assertTrue(revlog)
                n_types = len(user.models.all_names_and_ids())
                # v2: one answer corrected, one card removed, one card added
                cards2 = self.cards('Antwort zwei, korrigiert.')[:2] + [{'key': 'topic/new', 'kind': 'concept', 'front': 'Neue Frage?', 'answer': 'Neu.', 'source': 'Folie 3'}]
                r2 = anki_v2.build_deck(cards2, 'EM::Test', 'course', 'chapter', t / 'v2', state_dir=t)
                self.assertEqual(r2['update_delta']['changed'], ['topic/two'])
                self.assertEqual(r2['update_delta']['retirement_candidates'], ['topic/gap'])
                for _ in range(2):                                  # importing twice never duplicates
                    user.import_anki_package(ImportAnkiPackageRequest(package_path=r2['package'], options=opts))
                after = user.db.all('select id, nid, type, queue, due, ivl, reps from cards order by id')
                self.assertEqual([r for r in after if r[0] in {b[0] for b in before}], before)    # scheduling unchanged
                self.assertEqual(user.db.all('select * from revlog order by id'), revlog)          # history unchanged
                self.assertEqual(user.note_count(), 4)                                           # 3 old (none deleted) + 1 new
                self.assertEqual(len(user.models.all_names_and_ids()), n_types)                  # no parallel note type
                answers = [user.get_note(n)['Answer'] for n in user.db.list('select id from notes') if 'Answer' in user.get_note(n).keys()]
                self.assertIn('Antwort zwei, korrigiert.', answers)
            finally:
                user.close()

    def test_identity_independent_of_wording(self):
        try:
            import anki  # noqa: F401
        except ImportError:
            self.skipTest('anki not installed')
        self.assertEqual(anki_v2.guid('c', 'ch', 'k/a'), anki_v2.guid('c', 'ch', 'k/a'))
        self.assertNotEqual(anki_v2.guid('c', 'ch', 'k/a'), anki_v2.guid('c', 'ch2', 'k/a'))

    def test_lint_blocks_deck(self):
        with self.assertRaises(ContractError):
            anki_v2.build_deck([{'key': 'BAD KEY', 'kind': 'concept', 'front': 'x', 'answer': 'y', 'source': 's'}], 'D', 'c', 'h', tempfile.mkdtemp())


if __name__ == '__main__':
    unittest.main()


class DomainDemonstrations(unittest.TestCase):
    """Mathematics, law and ML demonstration chapters (fixtures/b9_domain_books.py) pass the rules and render."""

    def test_three_domains(self):
        import sys
        import pymupdf
        sys.path.insert(0, str(Path(__file__).parents[1] / 'fixtures'))
        from b9_domain_books import BOOKS
        with tempfile.TemporaryDirectory() as td:
            for k, b in BOOKS.items():
                with self.subTest(domain=k):
                    self.assertEqual(didactic_rules.blocking(didactic_rules.check_book(b)), [])
                    self.assertFalse([n for n in numeric_checks.check_book_numbers(b) if n['status'] == 'FAIL'])
                    res = typeset.publish_book(b, Path(td) / k)
                    text = ''.join(p.get_text() for p in pymupdf.open(res['1_Lehrbuch']['pdf']))
                    self.assertNotIn('\\(', text); self.assertNotIn('\\frac', text)          # all TeX typeset
            self.assertIn('for t in range(T)', ''.join(p.get_text() for p in pymupdf.open(Path(td) / 'ml' / '1_Lehrbuch.pdf')))
