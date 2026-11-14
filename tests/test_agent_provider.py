"""B8: the calling agent answers the model roles; clean stop, exact-prompt answers, resumable product run."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest import mock
from exam_mastery.providers import AgentProvider, AGENT_TURN_REQUIRED
from exam_mastery.budget import BudgetBlocked

LECTURE = """# Break-even Analysis

Learning objectives:
- Define the break-even point as the output where total revenue equals total cost.
- Calculate the break-even quantity as fixed cost divided by the contribution margin per unit.
- Explain why a higher contribution margin lowers the break-even quantity.

Model: fixed cost F, price p, variable cost v per unit. Break-even quantity Q = F/(p - v).
Example: F = 12000 EUR, p = 50 EUR, v = 30 EUR. Then Q = 12000/20 = 600 units.
"""


class Agent(unittest.TestCase):
    def test_stop_then_answer_for_exactly_this_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            p = AgentProvider()
            with self.assertRaises(BudgetBlocked) as e:
                p.ask('chapter_author', 'PROMPT A', td)
            self.assertEqual(e.exception.state, AGENT_TURN_REQUIRED)
            nxt = json.loads((Path(td) / 'agent_io' / 'NEXT.json').read_text())
            self.assertEqual(Path(nxt['prompt_file']).read_text(), 'PROMPT A')
            Path(nxt['answer_file']).write_text('{"blocks": []}')
            self.assertEqual(p.ask('chapter_author', 'PROMPT A', td), {'blocks': []})
            with self.assertRaises(BudgetBlocked):           # another prompt (e.g. a contract repair) needs its own answer
                p.ask('chapter_author', 'PROMPT B', td)
            self.assertFalse(p.external)

    def test_product_run_stops_resumable_and_resumes_same_run(self):
        from exam_mastery.product import setup, load_config, run_product
        with tempfile.TemporaryDirectory() as td:
            t = Path(td); src = t / 'course'; src.mkdir(); (src / '01 Break-even.md').write_text(LECTURE)
            with mock.patch.dict(os.environ, {'EXAM_MASTERY_OUTPUT': str(t / 'out'), 'EXAM_MASTERY_CONFIG': str(t / 'c.json')}):
                setup('agent', None, True)
                cfg = load_config()
                with mock.patch('exam_mastery.providers.execute', side_effect=AssertionError('no model process')):
                    out1, st1, _ = run_product(src, cfg)
                    self.assertEqual(st1['run_state'], AGENT_TURN_REQUIRED)
                    self.assertTrue(st1['resumable'])
                    nxt = json.loads(Path(st1['agent_next']).read_text())
                    self.assertEqual(nxt['role'], 'chapter_author')
                    out2, st2, _ = run_product(src, cfg)
                self.assertEqual(out1, out2); self.assertTrue(st2['resumed'])


if __name__ == '__main__':
    unittest.main()
