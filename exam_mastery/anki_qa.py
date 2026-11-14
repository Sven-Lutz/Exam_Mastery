"""Real Anki CSV import + updated import in disposable collection; no user collection."""
from pathlib import Path
import csv,io,tempfile,hashlib,json,time,fcntl
from .common import write_json

def verify(run):
    from anki.collection import Collection,ImportCsvRequest,ExportAnkiPackageOptions,ImportAnkiPackageRequest,ImportAnkiPackageOptions
    from anki.import_export_pb2 import CsvMetadata
    blueprint=json.loads((run/'architect.json').read_text())
    course_id=blueprint.get('course_id','course')
    root=run/'artifacts/anki';tsv=root/'anki_import.tsv'
    rows=list(csv.reader(io.StringIO('\n'.join(x for x in tsv.read_text().splitlines() if not x.startswith('#'))),delimiter='\t'))
    registry=run.parent/('.anki-state-'+course_id+'.json')
    with registry.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        previous=json.loads(registry.read_text()) if registry.exists() else {}
        export_timestamp=max(int(time.time()),int(previous.get('last_export_timestamp',0))+1)
        note_hashes={row[0]:hashlib.sha256(json.dumps(row[1:],ensure_ascii=False).encode()).hexdigest() for row in rows}
        old_hashes=previous.get('note_hashes',{})
        seen=set(previous.get('seen_note_ids',[]))|set(old_hashes)
        write_json(root/'anki-update-report.json',{'new':sorted(set(note_hashes)-seen),'changed':[key for key in note_hashes if key in old_hashes and old_hashes[key]!=note_hashes[key]],'unchanged':[key for key in note_hashes if old_hashes.get(key)==note_hashes[key]],'retirement_candidates':sorted(seen-set(note_hashes)),'automatic_deletion':False,'scope':'Previously exported preview IDs, not evidence of user import; review retirement manually'})
        write_json(registry,{'schema':'em-anki-export-state-v1','course_id':course_id,'last_export_timestamp':export_timestamp,'note_hashes':note_hashes,'seen_note_ids':sorted(seen|set(note_hashes))})
        fcntl.flock(lock,fcntl.LOCK_UN)
    if not rows:return {'cards':0,'reason':'No cards justified by architect; retirement candidates are in anki-update-report.json'}
    with tempfile.TemporaryDirectory(prefix='em-anki-') as d:
        col=Collection(str(Path(d)/'collection.anki2'))
        try:
            import shutil
            for media in (root/'media').glob('*'):
                if media.is_file() and media.suffix in ('.png','.svg'):shutil.copy2(media,Path(col.media.dir())/media.name)
            def schema_id(key):return int.from_bytes(hashlib.sha256((course_id+':basic-v1:'+key).encode()).digest()[:8],'big',signed=True)
            model=col.models.new('Exam Mastery Basic v1 '+course_id)
            deck_id=col.decks.id('Exam Mastery::'+blueprint['title'].replace('::',' — '))
            # Anki's native default importer does not merge distinct notetype IDs.
            # Rebuilds must preserve the notetype as well as fields/templates/GUIDs.
            # 48 bits remain exactly representable in the native JS interface.
            model['id']=int.from_bytes(hashlib.sha256((course_id+':basic-v1:notetype').encode()).digest()[:6],'big') or 1
            for name in ('ID','Question','Answer','Explanation','Source'):
                field=col.models.new_field(name);field['id']=schema_id('field:'+name);col.models.add_field(model,field)
            template=col.models.new_template('Recall')
            template['id']=schema_id('template:Recall')
            template['qfmt']=(root/'anki_front.html').read_text();template['afmt']=(root/'anki_back.html').read_text()
            col.models.add_template(model,template);model['css']=(root/'anki_style.css').read_text();col.models.update(model,preserve_usn=True)
            def do_import(path):
                meta=col.get_csv_metadata(str(path),None)
                meta.global_notetype.id=model['id'];meta.global_notetype.field_columns[:]=[1,2,3,4,5]
                meta.tags_column=0;meta.is_html=True;meta.deck_id=deck_id
                return col.import_csv(ImportCsvRequest(path=str(path),metadata=meta))
            do_import(tsv)
            count=col.note_count()
            if count!=len(rows):raise ValueError(f'Native importer count {count} != {len(rows)}')
            from anki.utils import base91
            for note_id in col.db.list('select id from notes'):
                note=col.get_note(note_id)
                note.guid=base91(int.from_bytes(hashlib.sha256(note['ID'].encode()).digest()[:8],'big'))
                col.update_note(note)
            col.db.execute('update notes set mod=?',export_timestamp)
            model['mod']=export_timestamp;col.models.update(model,preserve_usn=True)
            package=root/'Anki_Karten.apkg'  
            col.export_anki_package(out_path=str(package),options=ExportAnkiPackageOptions(with_scheduling=False,with_deck_configs=False,with_media=True,legacy=True),limit=None)
            target=Collection(str(Path(d)/'package-check.anki2'))
            try:
                target.import_anki_package(ImportAnkiPackageRequest(package_path=str(package),options=ImportAnkiPackageOptions(merge_notetypes=False,with_scheduling=False,with_deck_configs=False)))
                if target.note_count()!=count:raise ValueError('APKG import count mismatch')
                target_before=target.db.all('select id,nid from cards order by id')
                # A new package build must update matching GUIDs without duplicating cards.
                source_note=col.get_note(col.db.scalar('select id from notes order by id limit 1'))
                old_answer=source_note['Answer'];source_note['Answer']+=' [package update probe]';col.update_note(source_note)
                col.db.execute('update notes set mod=mod+2 where id=?',source_note.id)
                updated=Path(d)/'update.apkg'
                col.export_anki_package(out_path=str(updated),options=ExportAnkiPackageOptions(with_scheduling=False,with_deck_configs=False,with_media=True,legacy=True),limit=None)
                target.import_anki_package(ImportAnkiPackageRequest(package_path=str(updated),options=ImportAnkiPackageOptions(merge_notetypes=False,with_scheduling=False,with_deck_configs=False)))
                if target.note_count()!=count or target.db.all('select id,nid from cards order by id')!=target_before:raise ValueError('APKG update duplicated or replaced identities')
                if not any('[package update probe]' in target.get_note(n)['Answer'] for n in target.db.list('select id from notes')):raise ValueError('APKG update content unchanged')
                source_note=col.get_note(source_note.id);source_note['Answer']=old_answer;col.update_note(source_note)
            finally:target.close()
            nid=col.db.scalar('select id from notes order by id limit 1');note=col.get_note(nid);original_id=note['ID']
            card=note.cards()[0];card.reps=3;card.ivl=7;col.update_card(card)
            before=col.db.all('select id,nid,reps,ivl from cards order by id');logs=col.db.all('select * from revlog')
            changed=Path(d)/'update.tsv';changed_rows=[r[:] for r in rows]
            for row in changed_rows:
                if row[0]==original_id:row[2]+=' [isolated update test]'
            with changed.open('w',newline='') as f:
                f.write('#separator:Tab\n#html:true\n');csv.writer(f,delimiter='\t',lineterminator='\n').writerows(changed_rows)
            do_import(changed)
            if col.note_count()!=count or col.db.all('select id,nid,reps,ivl from cards order by id')!=before or col.db.all('select * from revlog')!=logs:raise ValueError('Reimport changed identity, count or scheduling')
            if '[isolated update test]' not in col.get_note(nid)['Answer']:raise ValueError('Reimport failed to update content')
            return {'export_timestamp':export_timestamp,'notes':count,'importer':'Anki 26.9.3 Python/Rust backend','package':'Anki_Karten.apkg exported, imported and updated with stable GUIDs; no scheduling exported','reimport':'IDs, count, changed text, reps, interval, revlog preserved','limits':'Basic only; independent rebuilds use stable notetype IDs and default no-merge import; GUI/mobile/FSRS long-term separately tested'}
        finally:col.close()
