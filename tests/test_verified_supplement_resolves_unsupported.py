"""A slide-unsupported claim is resolved only by an edition that replaces exactly that block with a supplement citing
verified subject sources; anything weaker keeps the FAIL."""
import json, tempfile, unittest
from pathlib import Path
from exam_mastery.product import _edition_supplemented_blocks


def chapter(ops):
    course = Path(tempfile.mkdtemp()); ch = course / 'run' / 'chapters' / 'ch-x'; ch.mkdir(parents=True)
    (course / 'editions').mkdir()
    (course / 'editions' / 'ch-x.json').write_text(json.dumps({'schema': 'em-edition-v1', 'chapter_id': 'ch-x', 'ops': ops}))
    return ch


def rep(block_id, **blk):
    return {'op': 'replace', 'block_id': block_id, 'reason': 'r', 'block': {'type': 'text', 'md': 'x', **blk}}


class VerifiedSupplement(unittest.TestCase):
    def test_verified_supplement_counts(self):
        ch = chapter([rep('b1', prov='supplement', sources=['epo-guidelines-g-vii-5'])])
        self.assertEqual(_edition_supplemented_blocks(ch), {'b1': ['epo-guidelines-g-vii-5']})

    def test_weaker_cases_do_not(self):
        for ops in ([rep('b1', prov='supplement', sources=['unknown-source'])],
                    [rep('b1', prov='supplement', sources=['epo-guidelines-g-vii-5', 'unknown-source'])],
                    [rep('b1', prov='didactic', sources=['epo-guidelines-g-vii-5'])],
                    [rep('b1', prov='supplement')],
                    [{'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'text', 'md': 'x', 'prov': 'supplement', 'sources': ['epo-guidelines-g-vii-5']}]}]):
            self.assertEqual(_edition_supplemented_blocks(chapter(ops)), {}, ops)

    def test_no_edition(self):
        ch = Path(tempfile.mkdtemp()) / 'run' / 'chapters' / 'ch-y'; ch.mkdir(parents=True)
        self.assertEqual(_edition_supplemented_blocks(ch), {})


if __name__ == '__main__':
    unittest.main()
