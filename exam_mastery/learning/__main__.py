"""CLI: python -m exam_mastery.learning <command>
  build <out_dir> [--lab-dir REL] [--fonts REL]  write the three track pages (+ JSON) into <out_dir>/lernstrecken
  validate                                       re-diagnose every expected answer and bug value of all tracks
  tutor-brief <context.json>                     print a Markdown brief for the Claude Code tutor (no model call)
  anki <out_dir>                                 write the review deck (stable identities, see anki_bridge.py)
  forms                                          print the parallel test forms of the evaluation protocol
"""
import json
import sys
import time
from pathlib import Path

from . import anki_bridge, evaluation, render, tracks, tutor


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    cmd, rest = argv[0], argv[1:]
    t0 = time.perf_counter()
    if cmd == 'validate':
        for t in tracks.all_tracks():
            tracks.validate(t)
        print(json.dumps({'tracks': 3, 'valid': True, 'model_calls': 0})); return 0
    if cmd == 'build':
        out = Path(rest[0]) / 'lernstrecken'
        lab_dir = rest[rest.index('--lab-dir') + 1] if '--lab-dir' in rest else '../labs'
        fonts = rest[rest.index('--fonts') + 1] if '--fonts' in rest else None
        ent = None
        if '--ent-lab' in rest:
            m = json.loads(Path(rest[rest.index('--ent-lab') + 1]).read_text(encoding='utf-8'))['model']
            ent = {k: m[k] for k in ('orders', 'delay', 'cost', 'invest')}
        pages = [str(render.write(t, out, lab_href=f'{lab_dir}/{t["lab"].replace("/", "__")}.html', fonts=fonts))
                 for t in tracks.all_tracks(ent)]
        print(json.dumps({'pages': pages, 'seconds': round(time.perf_counter() - t0, 3), 'model_calls': 0}, ensure_ascii=False)); return 0
    if cmd == 'tutor-brief':
        print(tutor.brief(tutor.load(rest[0]))); return 0
    if cmd == 'anki':
        rep = anki_bridge.build(rest[0])
        print(json.dumps({k: rep[k] for k in ('package', 'notes', 'cards', 'update_delta')}, ensure_ascii=False)); return 0
    if cmd == 'forms':
        print(json.dumps({'forms': evaluation.forms(), 'plan': evaluation.PLAN}, ensure_ascii=False, indent=1)); return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
