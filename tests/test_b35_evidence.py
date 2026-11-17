"""B35 claim evidence registry: one negative fixture per rule, positives that must pass, and the legacy mapping that
stops a Crossref 'VERIFIED' from counting as content support."""
import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import evidence as EV

ROOT = Path(__file__).resolve().parents[1]
ABSTRACT = ('We show that all of these algorithms converge at least as quickly as successive approximations and obtain '
            'estimates of their rates of convergence.')
GOOD = {'id': 'c1', 'claim_type': 'MATHEMATICAL', 'statement': 'Die Verfahren konvergieren mindestens so schnell wie die sukzessive Approximation.',
        'source': {'id': 's'}, 'access': 'ABSTRACT_ONLY', 'accessed_text': ABSTRACT,
        'quote': 'converge at least as quickly as successive approximations', 'review': {'status': 'UNREVIEWED'}}


def codes(c, graphs=None, sev='FAIL'):
    return {f['code'] for f in EV.check_claim(c, graphs) if f['severity'] == sev}


def mut(**kw):
    c = copy.deepcopy(GOOD); c.update(kw); return c


class Rules(unittest.TestCase):
    def test_good_abstract_claim_passes(self):
        self.assertEqual(codes(GOOD), set())
        self.assertEqual(EV.publish_label(GOOD), 'nur Abstract gelesen')

    def test_doi_alone_never_supports_content(self):
        self.assertIn('E1', codes(mut(access='METADATA_ONLY', accessed_text='', quote='')))
        self.assertEqual(codes(mut(access='METADATA_ONLY', claim_type='BIBLIOGRAPHIC', quote='')), set())

    def test_quote_must_be_in_accessed_text(self):
        self.assertIn('E2', codes(mut(quote='converge twice as fast as successive approximations')))

    def test_number_beyond_read_passage(self):
        self.assertIn('E3', codes(mut(statement='Die Verfahren konvergieren mit Rate 0.5 schneller als die Approximation.')))

    def test_fulltext_detail_from_abstract(self):
        self.assertIn('E4', codes(mut(statement='Der Beweis zeigt, dass die Verfahren mindestens so schnell konvergieren.')))

    def test_fulltext_needs_locator(self):
        self.assertIn('E5', codes(mut(access='PRIMARY_FULLTEXT')))
        self.assertNotIn('E5', codes(mut(access='PRIMARY_FULLTEXT', locator='S. 1130, Satz 3.1')))

    def test_author_derivation_needs_audited_graph(self):
        g = json.loads((ROOT / 'fixtures/arguments/bellman_expectation.json').read_text())
        c = mut(access='AUTHOR_DERIVATION', derivation_ref='bellman-expectation', quote='')
        self.assertEqual(codes(c, {'bellman-expectation': g}), set())
        self.assertEqual(EV.level(c), 'AUTHOR_DERIVATION_AUDITED')
        self.assertEqual(EV.level(dict(c, review={'status': 'HUMAN_REVIEWED'})), 'AUTHOR_DERIVATION_REVIEWED')
        bad = copy.deepcopy(g); bad['claim']['assumptions'].remove('A_markov')
        self.assertIn('E6', codes(c, {'bellman-expectation': bad}))
        self.assertIn('E6', codes(mut(access='AUTHOR_DERIVATION', quote='')))

    def test_claim_type_requirements(self):
        legal = mut(claim_type='NORMATIVE_LEGAL', access='OFFICIAL_COURSE', locator='Folie 12', quote='')
        self.assertIn('E7', codes(legal))
        self.assertEqual(codes(dict(legal, jurisdiction='DE', valid_as_of='2026-01-01')), set())
        self.assertIn('E7', codes(mut(claim_type='CLINICAL', access='OFFICIAL_COURSE', locator='S. 3', quote='', valid_as_of='2025')))

    def test_model_inference_needs_marker(self):
        self.assertIn('E8', codes(mut(access='MODEL_INFERENCE', claim_type='INTERPRETATION', quote=''), sev='WARN'))
        self.assertIn('nicht geprüft', EV.publish_label({'access': 'MODEL_INFERENCE'}))


class Legacy(unittest.TestCase):
    def test_crossref_verified_is_metadata_only(self):
        kb = json.loads((ROOT / 'exam_mastery/knowledge/verification.json').read_text())['sources']
        levels = {k: EV.from_legacy_verification(v) for k, v in kb.items()}
        self.assertTrue(levels)
        self.assertTrue(set(levels.values()) <= {'METADATA_ONLY', 'ABSTRACT_ONLY', 'UNVERIFIED'})
        self.assertNotIn('PRIMARY_FULLTEXT', levels.values())


if __name__ == '__main__':
    unittest.main()
