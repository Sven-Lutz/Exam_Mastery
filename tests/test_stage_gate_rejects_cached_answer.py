"""A stage gate FAIL after a SUCCEEDED role must not be replayed from the checkpoint or the agent answer file."""
import json, tempfile, unittest
from pathlib import Path
from exam_mastery.checkpoints import Checkpoints
from exam_mastery.providers import AgentProvider
from exam_mastery.budget import BudgetBlocked


class Fake:
    budget = None; external = False
    def __init__(self): self.asked = 0
    def fingerprint(self): return {'name': 'fake'}
    def ask(self, role, prompt, out, images=None):
        self.asked += 1; return {'v': self.asked}
    def discard(self, role, out, reason): return []


class RejectCached(unittest.TestCase):
    def test_rejected_answer_is_not_served_again(self):
        cp = Checkpoints(tempfile.mkdtemp()); prov = Fake()
        cp.engine_identity = lambda: 'E'
        self.assertEqual(cp.invoke('chapter_author', 'P', prov, lambda o: None), {'v': 1})
        self.assertEqual(cp.invoke('chapter_author', 'P', prov, lambda o: None), {'v': 1})   # cache hit
        self.assertEqual(prov.asked, 1)
        cp.reject('chapter_author', prov, 'stage gate after chapter_author: X')
        self.assertEqual(cp.invoke('chapter_author', 'P', prov, lambda o: None), {'v': 2})   # asked again
        self.assertEqual(prov.asked, 2)

    def test_agent_answer_file_moved_aside(self):
        out = Path(tempfile.mkdtemp()); cp = Checkpoints(out); cp.engine_identity = lambda: 'E'
        prov = AgentProvider()
        with self.assertRaises(BudgetBlocked):
            cp.invoke('chapter_author', 'P', prov, lambda o: None)
        nxt = json.loads((out / 'agent_io' / 'NEXT.json').read_text())
        Path(nxt['answer_file']).write_text('{"a": 1}')
        self.assertEqual(cp.invoke('chapter_author', 'P', prov, lambda o: None), {'a': 1})
        moved = cp.reject('chapter_author', prov, 'gate')
        self.assertEqual(len(moved), 1)
        self.assertFalse(Path(nxt['answer_file']).exists())
        with self.assertRaises(BudgetBlocked):           # the agent is asked for a new answer
            cp.invoke('chapter_author', 'P', prov, lambda o: None)


if __name__ == '__main__':
    unittest.main()
