"""Human scope decisions may add an anchored competency; models may not, and anchors must exist."""
import unittest
from exam_mastery.curriculum import SemanticDecisions
from exam_mastery.common import ContractError


def dec(**kw):
    d = {'kind': 'competency', 'subject_id': 'ch-1', 'decided_by': 'human', 'rationale': 'owner decision',
         'evidence_element_ids': ['e1'], 'value': {'statement': 'P/R/F1 berechnen', 'operations': ['CALCULATE'], 'anchor_element_ids': ['e1']}}
    d.update(kw); return d


class ScopeDecision(unittest.TestCase):
    def test_valid(self):
        SemanticDecisions([dec()]).validate({'e1'})

    def test_rejected(self):
        for bad in (dec(decided_by='model'), dec(value={'statement': '', 'operations': ['CALCULATE'], 'anchor_element_ids': ['e1']}),
                    dec(value={'statement': 'x', 'operations': ['FLY'], 'anchor_element_ids': ['e1']}),
                    dec(value={'statement': 'x', 'operations': ['EXPLAIN'], 'anchor_element_ids': ['nope']}),
                    dec(value={'statement': 'x', 'operations': ['EXPLAIN'], 'anchor_element_ids': []})):
            with self.assertRaises(ContractError):
                SemanticDecisions([bad]).validate({'e1'})


if __name__ == '__main__':
    unittest.main()


class DecisionDigest(unittest.TestCase):
    def test_path_string_is_hashed(self):
        import tempfile, os
        from exam_mastery.runtime import _semantic_digest
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False); f.write('{"schema":"em-semantic-decisions-v1","decisions":[]}'); f.close()
        self.assertEqual(_semantic_digest(f.name), _semantic_digest(__import__('pathlib').Path(f.name)))
        os.unlink(f.name)
