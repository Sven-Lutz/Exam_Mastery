#!/usr/bin/env bash
# Release smoke test: checks exactly the shipped archive, never the development tree.
#   scripts/release_smoke_test.sh exam-mastery-<version>.tar.gz
# Everything runs under a temporary HOME. Your real config, skills, outputs and Anki data are not read or written.
# Downloads are reused from your caches (Chromium, pip, npm), so the test runs offline once those are filled.
# No model is called: production stops at the agent's first turn, which needs no provider process.
set -uo pipefail
tarball="$(cd "$(dirname "${1:?path to the release .tar.gz}")" && pwd)/$(basename "$1")"
real_home="$HOME"
T="$(mktemp -d "${TMPDIR:-/tmp}/em-smoke.XXXXXX")"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$real_home/Library/Caches/ms-playwright}"
[ -d "$PLAYWRIGHT_BROWSERS_PATH" ] || export PLAYWRIGHT_BROWSERS_PATH="$real_home/.cache/ms-playwright"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$real_home/Library/Caches/pip}" npm_config_cache="${npm_config_cache:-$real_home/.npm}"
export HOME="$T/home" PATH="$T/home/.local/bin:$PATH"
unset EXAM_MASTERY_HOME EXAM_MASTERY_PYTHON EXAM_MASTERY_CONFIG GEMINI_API_KEY GOOGLE_API_KEY
mkdir -p "$HOME"; cd "$T"   # never import the engine from the caller's working directory (e.g. the repo)
pass=0; fail=0; log="$T/smoke.log"
ok()  { echo "PASS  $1"; pass=$((pass+1)); }
bad() { echo "FAIL  $1"; fail=$((fail+1)); }
chk() { echo "== $1" >>"$log"; if eval "$2" >>"$log" 2>&1; then ok "$1"; else bad "$1"; tail -4 "$log" | sed 's/^/      /'; fi; }

# 1 install from the archive only
mkdir -p "$T/pkg" && tar xzf "$tarball" -C "$T/pkg"
pkg="$(ls -d "$T"/pkg/exam-mastery-*)"
chk "install from archive" "bash '$pkg/install.sh' --library '$HOME/lib'"
PY="$HOME/.local/share/exam-mastery/venv/bin/python"
engine_from_venv() { "$PY" -c 'import exam_mastery,sys,os; p=os.path.realpath(exam_mastery.__file__); h=os.path.realpath(sys.argv[1]); sys.exit(0 if p.startswith(h) and "site-packages" in p else 1)' "$HOME"; }
chk "engine imported from the installed venv, not the repo" engine_from_venv
# 2 CLI
chk "CLI help" "exam-mastery --help | grep -q 'exam-mastery status'"
chk "command ignores an exam_mastery folder in the working directory" "mkdir -p '$T/shadow/exam_mastery' && echo 'raise SystemExit(99)' > '$T/shadow/exam_mastery/__init__.py' && (cd '$T/shadow' && exam-mastery --help >/dev/null)"
# 3 skill discovery
chk "skill link for Claude Code" "[ \"\$(readlink '$HOME/.claude/skills/exam-mastery')\" = '$HOME/lib/exam-mastery' ]"
chk "skill link for Codex (~/.agents/skills)" "[ -L '$HOME/.agents/skills/exam-mastery' ]"
chk "SKILL.md frontmatter name" "head -3 '$HOME/.claude/skills/exam-mastery/SKILL.md' | grep -q '^name: exam-mastery'"
chk "skill version = package version" "cmp -s '$HOME/lib/exam-mastery/VERSION' '$pkg/VERSION'"
chk "host check without provider" "(cd '$HOME/lib/exam-mastery' && bash scripts/check_host.sh) | tail -1 | grep -q '^HOST_READY_NO_PROVIDER'"
# 4 read-only analysis of a course
course="$T/course"; cp -R "$pkg/engine/fixtures/synthetic_course" "$course"
before="$(find "$course" -type f -exec shasum {} + | sort | shasum)"
chk "status (read-only)" "exam-mastery status '$course' | '$PY' -c 'import json,sys; json.load(sys.stdin)'"
chk "update (offline, 0 provider calls)" "exam-mastery update '$course' | '$PY' -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d[\"provider_calls_made\"]==0 and d[\"to_produce\"] else 1)'"
chk "course folder unchanged" "[ \"\$(find '$course' -type f -exec shasum {} + | sort | shasum)\" = '$before' ]"
# 5-7 publishing with validated fixture data: typeset PDFs, Anki export and reimport, checks
chk "publish fixture book (PDF, Anki, checks)" "'$PY' -W ignore - '$pkg/engine/fixtures' '$T/pub' <<'PY'
import sys, json
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from b9_domain_books import BOOKS
from exam_mastery import typeset, anki_v2, didactic_rules, semantic_checks, numeric_checks
import pymupdf
out = Path(sys.argv[2])
for name, book in BOOKS.items():
    d = out / name
    assert not didactic_rules.blocking(didactic_rules.check_book(book)), name
    assert not [r for r in semantic_checks.check_book(book) if r['status'] == 'FAIL'], name
    assert not [r for r in numeric_checks.check_book_numbers(book) if r['status'] == 'FAIL'], name
    docs = typeset.publish_book(book, d)
    for k, v in docs.items():
        assert not v['toc_unresolved'], (name, k)
        doc = pymupdf.open(v['pdf']); text = ''.join(p.get_text() for p in doc)
        assert '\\\\(' not in text and '\\\\[' not in text, (name, k, 'raw TeX in PDF')
        fonts = {f[3] for p in doc for f in p.get_fonts()}
        assert any('SourceSerif' in f or 'SourceSans' in f for f in fonts), (name, k, fonts)
        if v['toc_entries']:
            assert len(doc.get_toc()) == v['toc_entries'] and v['internal_links'] >= v['toc_entries'], (name, k)
    rep = anki_v2.build_deck(book['cards'], f'EM::{name}', 'smoke', name, d, state_dir=d)
    ver = anki_v2.verify_package(rep['package'])
    assert ver.get('reimport') and ver.get('notes') == rep['notes'], ver
print('ok')
PY"
chk "interactive labs built and valid (cash flow, network, risk matrix)" "'$PY' -W ignore - '$T/labs' <<'PY'
import sys
from exam_mastery.labs import build as B, models as M
o=[0,100,180,190,210,230,250,270]; c=[50+g+x+2 for g,x in zip([10,30,50,40,140,60,70,80],[40,40,70,60,50,40,40,40])]
assert M.cashflow(o,5,c,[200,500,300,140])['financing_need']==2144
for s in (B.cashflow_spec('t/cf','CF',['k'],['s'],o,5,c,[200,500,300,140]),B.mlp_spec(),B.risk_spec('t/r','R',['k'],['s'])):
    h=B.render(s,sys.argv[1]).read_text(); assert \"default-src 'none'\" in h and 'https://' not in h
print('ok')
PY"
chk "learning environment built from a book (offline page, CSP, embedded lab, no ids)" "'$PY' -W ignore - '$T/learn' <<'PY'
import sys, re
from pathlib import Path
from exam_mastery import learn_app
from exam_mastery.labs import build as B
d=Path(sys.argv[1]); o=[0,100,180,190,210,230,250,270]; c=[50+g+x+2 for g,x in zip([10,30,50,40,140,60,70,80],[40,40,70,60,50,40,40,40])]
B.render(B.cashflow_spec('t/cf','CF',['kc-a'],['s'],o,5,c,[200,500,300,140]), d/'Lernumgebung'/'labs')
bk={'meta':{'title':'T','course':'K','chapter_no':1},'kc_labels':{'kc-a':'Finanzbedarf bestimmen'},'sections':[{'title':'A','blocks':[{'type':'text','md':'x','kc_ids':['kc-a']}]}],'stages':[],'cards':[],'figures':{}}
p=learn_app.build(bk, d/'Lernumgebung', labs=[{'file':'Lernumgebung/labs/t__cf.html','title':'CF','kc_ids':['kc-a']}]); h=p.read_text()
assert \"default-src 'none'\" in h and 'https://' not in h and 't__cf.html' in h
print('ok')
PY"
chk "mathematical scenes valid (network, chord lift, cash flow)" "'$PY' -W ignore - <<'PY'
from exam_mastery.labs import build as B
for s in (B.mlp_spec(), B.chord_spec(), B.cashflow_spec('t/cf','CF',['k'],['s'],[0,100,180,190,210,230,250,270],5,[102,122,172,152,242,152,162,172],[200,500,300,140])):
    assert B.validate(s) and s['scene']['expect']['values']
print('ok')
PY"
# 8 agent integration (no model call): one-time setup, then production stops at the agent's first turn
chk "setup provider agent" "exam-mastery --setup --provider agent --accept-data-transfer | grep -q CONFIGURED"
chk "host check with provider" "(cd '$HOME/lib/exam-mastery' && bash scripts/check_host.sh) | tail -1 | grep -qx 'HOST_READY'"
chk "agent turn handed over (exit 4, NEXT.json, prompt file)" "cd '$course' && exam-mastery > '$T/agent.out'; rc=\$?; [ \$rc = 4 ] && '$PY' - '$T/agent.out' <<'PY'
import json, sys, re
from pathlib import Path
t = Path(sys.argv[1]).read_text()
nxt = [json.loads(m) for m in re.findall(r'\{[^{}]*AGENT_TURN_REQUIRED[^{}]*\}', t)][-1]['next']
n = json.loads(Path(nxt).read_text())
assert Path(n['prompt_file']).stat().st_size > 1000 and 'answer_file' in n, n
PY"
chk "status lists the run" "exam-mastery status '$course' | grep -q AGENT_TURN_REQUIRED"
# 9 uninstall keeps config, outputs and the library skill
mkdir -p "$HOME/Exam_Mastery_Output/keep" && echo state > "$HOME/Exam_Mastery_Output/keep/anki_state.json"
cfg="$HOME/.config/exam-mastery/config.json"; cfg_sum="$(shasum "$cfg")"
chk "uninstall" "bash '$pkg/uninstall.sh'"
chk "command and venv removed" "! [ -e '$HOME/.local/bin/exam-mastery' ] && ! [ -e '$HOME/.local/share/exam-mastery' ]"
chk "config, outputs, library skill kept" "[ \"\$(shasum '$cfg')\" = '$cfg_sum' ] && [ -f '$HOME/Exam_Mastery_Output/keep/anki_state.json' ] && [ -f '$HOME/lib/exam-mastery/SKILL.md' ]"
# 10 reinstall without losing configuration or learning state
chk "reinstall" "bash '$pkg/install.sh' --library '$HOME/lib'"
chk "config and outputs unchanged after reinstall" "[ \"\$(shasum '$cfg')\" = '$cfg_sum' ] && grep -q state '$HOME/Exam_Mastery_Output/keep/anki_state.json'"
chk "earlier run still visible after reinstall" "exam-mastery status '$course' | grep -q AGENT_TURN_REQUIRED"

echo "RESULT pass=$pass fail=$fail (log: $log)"
[ $fail = 0 ] && { rm -rf "$T"; echo RELEASE_SMOKE_PASS; } || { echo "RELEASE_SMOKE_FAIL - kept $T for inspection"; exit 1; }
