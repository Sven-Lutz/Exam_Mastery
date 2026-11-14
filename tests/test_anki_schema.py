import copy,importlib.util,tempfile,time,unittest
from pathlib import Path
from exam_mastery.common import read_json,write_json
@unittest.skipUnless(importlib.util.find_spec('anki'),'Native Anki backend unavailable')
class PackageIdentityTests(unittest.TestCase):
 def test_fresh_package_builds_preserve_schema_cards_and_history(self):
  from anki.collection import Collection,ImportAnkiPackageRequest,ImportAnkiPackageOptions
  from exam_mastery.publish import publish_cards
  from exam_mastery.anki_qa import verify
  fixture=Path(__file__).resolve().parents[1]/'fixtures/synthetic_responses'
  bp=read_json(fixture/'architect.json');bp['course_id']='synthetic-stable-course'
  cards=read_json(fixture/'cards.json');design=read_json(fixture/'design.json')
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'first',Path(d)/'second'
   for index,out in enumerate((a,b)):
    data=copy.deepcopy(cards)
    if index:data['cards'][0]['answer']+=' [updated answer]'
    write_json(out/'architect.json',bp);publish_cards(bp,data,design,out/'artifacts/anki');verify(out)
   col=Collection(str(Path(d)/'target.anki2'))
   try:
    def load(out):col.import_anki_package(ImportAnkiPackageRequest(package_path=str(out/'artifacts/anki/Anki_Karten.apkg'),options=ImportAnkiPackageOptions(merge_notetypes=True,update_notes=1,with_scheduling=False,with_deck_configs=False)))
    load(a)
    card=col.get_card(col.db.scalar('select id from cards order by id limit 1'));card.reps=4;card.ivl=11;col.update_card(card)
    col.db.execute('insert into revlog (id,cid,usn,ease,ivl,lastIvl,factor,time,type) values (?,?,?,?,?,?,?,?,?)',int(time.time()*1000),card.id,-1,3,11,4,2500,1200,1)
    before=col.db.all('select id,nid,reps,ivl from cards order by id');history=col.db.all('select * from revlog')
    load(b)
    self.assertEqual(col.note_count(),len(cards['cards']))
    self.assertEqual(col.db.all('select id,nid,reps,ivl from cards order by id'),before)
    self.assertEqual(col.db.all('select * from revlog'),history)
    notes=[col.get_note(n) for n in col.db.list('select id from notes')]
    self.assertTrue(any('[updated answer]' in n['Answer'] for n in notes))
    for note in notes:
     self.assertEqual(len(note.note_type()['flds']),5);self.assertEqual(len(note.note_type()['tmpls']),1)
   finally:col.close()
