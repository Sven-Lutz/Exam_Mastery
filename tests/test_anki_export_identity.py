"""Re-importing an updated deck must keep the learner's own edits, scheduling and note types (CD-8, R8 EF-1..EF-4).

Before this fix every export stamped ALL notes and both note types with a new modification time, so Anki's default
import ('update notes if newer') overwrote every learner edit even when the content had not changed, and note-type
IDs were hashed from the display name, so a rename would have created new note types.

The checks import real packages with the anki library into throwaway collections in a temporary directory; no
learner collection is ever opened.
"""
import json
import tempfile
import unittest
from pathlib import Path

try:
    from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
except ImportError:  # pragma: no cover - anki is part of the tested requirements
    Collection = None

from exam_mastery import anki_v2

CARDS = [
    {'key': 'cd8/unchanged', 'kind': 'concept', 'front': 'Was ist der Finanzbedarf?',
     'answer': 'Der Betrag des tiefsten kumulierten Liquiditätsstandes.'},
    {'key': 'cd8/changed', 'kind': 'concept', 'front': 'Was ist ein Cashflow?',
     'answer': 'Der Saldo der Zahlungen einer Periode.'},
]
DECK, COURSE, CHAPTER = 'Exam Mastery::CD8', 'cd8-kurs', 'kapitel-1'


@unittest.skipIf(Collection is None, 'anki library not installed')
class AnkiExportIdentity(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.root = Path(self.td.name)
        self.state = self.root / 'state'; self.state.mkdir()
        (self.root / 'learner').mkdir()
        self.learner = Collection(str(self.root / 'learner' / 'collection.anki2'))

    def tearDown(self):
        self.learner.close(); self.td.cleanup()

    def build(self, cards, out):
        return anki_v2.build_deck(cards, DECK, COURSE, CHAPTER, self.root / out, state_dir=self.state)

    def state_file(self):
        return next(self.state.glob('.anki-v2-state-*.json'))

    def import_(self, rep):
        self.learner.import_anki_package(ImportAnkiPackageRequest(package_path=rep['package'], options=ImportAnkiPackageOptions()))

    def note(self, key):
        nid = next(n for n in self.learner.find_notes('') if self.learner.get_note(n)['Key'] == key)
        return self.learner.get_note(nid)

    def later_export(self, seconds):
        """Make the next export happen `seconds` after the previous one without touching the clock."""
        p = self.state_file(); st = json.loads(p.read_text()); st['last_export'] += seconds; p.write_text(json.dumps(st))

    def learner_edits_and_reviews(self, t_edit):
        n = self.note('cd8/unchanged'); n['Explanation'] = 'Meine eigene Eselsbrücke'; self.learner.update_note(n)
        self.learner.db.execute('update notes set mod=? where id=?', t_edit, n.id)        # edited after the import
        cid = n.cards()[0].id
        self.learner.db.execute('update cards set type=2, queue=2, ivl=12, due=40 where id=?', cid)
        self.learner.db.execute('insert into revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type) '
                                'values (?, ?, -1, 3, 12, 4, 2500, 6000, 1)', t_edit * 1000, cid)
        return cid

    def test_reimport_keeps_learner_edit_and_updates_only_changed_content(self):
        v1 = self.build(CARDS, 'v1'); self.import_(v1)
        t1 = json.loads(self.state_file().read_text())['last_export']
        cid = self.learner_edits_and_reviews(t1 + 100)
        cards_before = sorted(self.learner.db.list('select id from cards'))
        changed = [dict(CARDS[0]), dict(CARDS[1], answer='Einzahlungen minus Auszahlungen einer Periode.')]
        self.later_export(1000)
        v2 = self.build(changed, 'v2'); self.import_(v2)
        self.assertEqual(v2['restamped'], ['cd8/changed'])
        self.assertEqual(v2['update_delta']['changed'], ['cd8/changed'])
        self.assertEqual(self.note('cd8/unchanged')['Explanation'], 'Meine eigene Eselsbrücke')    # learner edit kept
        self.assertIn('Einzahlungen minus Auszahlungen', self.note('cd8/changed')['Answer'])          # real change arrives
        self.assertEqual(sorted(self.learner.db.list('select id from cards')), cards_before)        # same cards
        self.assertEqual(self.learner.db.scalar('select ivl from cards where id=?', cid), 12)        # scheduling kept
        self.assertEqual(self.learner.db.scalar('select count() from revlog where cid=?', cid), 1)   # history kept

    def test_unchanged_rebuild_restamps_nothing(self):
        v1 = self.build(CARDS, 'v1')
        self.later_export(1000)
        v2 = self.build(CARDS, 'v2')
        self.assertEqual(v2['restamped'], [])
        st = json.loads(self.state_file().read_text())
        self.assertEqual(len(set(st['mods'].values())), 1)                    # both keep the first export's time
        self.assertLess(st['notetypes']['basic']['mod'], st['last_export'])

    def test_state_from_before_this_fix_falls_back_to_last_export(self):
        self.build(CARDS, 'v1')
        p = self.state_file(); st = json.loads(p.read_text()); t1 = st['last_export']
        for k in ('mods', 'notetypes'):
            st.pop(k)
        p.write_text(json.dumps(st))          # an earlier export stamped every note with last_export
        v2 = self.build(CARDS, 'v2')
        self.assertEqual(v2['restamped'], [])
        self.assertEqual(json.loads(self.state_file().read_text())['mods']['cd8/unchanged'], t1)

    def test_note_type_identity_is_frozen_against_display_renames(self):
        legacy = anki_v2._id('em-notetype-v2', 'Exam Mastery · Basis (v2)', n=6, signed=False)
        v1 = self.build(CARDS, 'v1'); self.import_(v1)
        ids_before = {m['id'] for m in self.learner.models.all()}
        self.assertIn(legacy, ids_before)                                    # bit-identical to every earlier export
        saved = dict(anki_v2.NOTETYPE_NAME)
        try:
            anki_v2.NOTETYPE_NAME.update(basic='Mastery · Basis', cloze='Mastery · Lückentext')
            self.later_export(1000)
            v2 = self.build(CARDS, 'v2'); self.import_(v2)
        finally:
            anki_v2.NOTETYPE_NAME.clear(); anki_v2.NOTETYPE_NAME.update(saved)
        self.assertEqual({m['id'] for m in self.learner.models.all()}, ids_before)    # no new note type
        # Anki keeps the learner's existing note-type name on import (observed with anki 26.9.3); a display rename
        # therefore reaches only new installations. Identity, notes and cards are what must not change.
        self.assertEqual(len(self.learner.find_notes('')), 2)


if __name__ == '__main__':
    unittest.main()
