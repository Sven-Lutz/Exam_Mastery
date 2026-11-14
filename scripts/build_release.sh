#!/usr/bin/env bash
# Builds the distributable Exam Mastery package from the committed engine (git HEAD) and runs the release checks.
# Usage: scripts/build_release.sh <version-label> [out-dir]
# Nothing private is copied: only an allow-list of tracked paths, then a scan that fails the build on any hit.
set -euo pipefail
engine="$(cd "$(dirname "$0")/.." && pwd)"
label="${1:?version label, e.g. v1.0.0-rc1}"
out="${2:-$engine/../../release_candidates}/exam-mastery-$label"
py="${EXAM_MASTERY_PYTHON:-$HOME/.local/share/exam-mastery/dev-venv/bin/python}"
cd "$engine"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean; commit first"; exit 2; }
rm -rf "$out"; mkdir -p "$out/engine"
include=(exam_mastery tests fixtures pyproject.toml requirements-math-tested.txt requirements-gemini-tested.txt start
         scripts/gemini_smoke_test.py scripts/pdf_smoke.py scripts/build_release.sh scripts/release_smoke_test.sh
         scripts/build_reference_scenes.py docs/learning_design_evidence_matrix.json docs/LEARNING_ENGINE.md docs/EVALUATION_PROTOCOL.md docs/DESIGN_v0_19.md)
exclude=(fixtures/didactic_review_patch.json)
git archive HEAD "${include[@]}" | tar -x -C "$out/engine"
for x in "${exclude[@]}"; do rm -f "$out/engine/$x"; done
cp -R release/skill "$out/skill"
cp release/install.sh release/uninstall.sh release/README.md release/RELEASE_NOTES.md release/VERSION "$out/"
[ -n "${SAMPLES:-}" ] && [ -d "$SAMPLES" ] && cp -R "$SAMPLES" "$out/sample_output" || true
if [ -f LICENSE ]; then cp LICENSE "$out/LICENSE"; else echo "NOTE: no LICENSE file - the owner must choose one before any public distribution"; fi

# ---- security scan: private paths, course names, keys, binary course material, run data
fail=0
hits=$(grep -rIlE -e '(^|[^A-Za-z0-9._-])/Users/' -e '01_Studium' "$out" | grep -v '/scripts/build_release.sh$' || true)
runs=$(find "$out" -type d \( -name 'runs_*' -o -name 'course-*' -o -name 'provider_evidence' \) || true)
[ -n "$runs" ] && { echo "RUN DATA in: $runs"; fail=1; }
[ -n "$hits" ] && { echo "PRIVATE PATH in: $hits"; fail=1; }
keys=$(grep -rIEn -e 'AIza[0-9A-Za-z_-]{30,}' -e 'sk-[A-Za-z0-9_-]{20,}' -e 'ya29\.[0-9A-Za-z_-]{20,}' "$out" | grep -v 'AIzaTEST' || true)
[ -n "$keys" ] && { echo "POSSIBLE KEY: $keys"; fail=1; }
bins=$(find "$out" -type f \( -iname '*.pdf' -o -iname '*.pptx' -o -iname '*.apkg' -o -iname '*.anki2' -o -iname '*.key' -o -name '.env' \) \
       ! -path '*/sample_output/*' ! -path '*/fixtures/*' || true)
[ -n "$bins" ] && { echo "UNEXPECTED BINARY/SECRET FILE: $bins"; fail=1; }
[ $fail = 0 ] || { echo "SECURITY_SCAN FAIL"; exit 1; }
echo "SECURITY_SCAN PASS"

# ---- dependency licence audit (installed versions of the pinned requirements)
"$py" - "$out" <<'PY'
import sys, re
from importlib import metadata
from pathlib import Path
out = Path(sys.argv[1]); rows = []
for req in ['requirements-math-tested.txt', 'requirements-gemini-tested.txt']:
    for line in (out / 'engine' / req).read_text().split('\n'):
        name = re.split(r'[=<>\[ ]', line.strip())[0]
        if not name or name.startswith('#'):
            continue
        try:
            m = metadata.metadata(name)
            lic = m.get('License-Expression') or next((c.split('::')[-1].strip() for c in m.get_all('Classifier') or [] if c.startswith('License ::')), None) or (m.get('License') or 'UNKNOWN').split('\n')[0][:60]
        except metadata.PackageNotFoundError:
            lic = 'NOT_INSTALLED_HERE'
        rows.append((name, lic))
rows = sorted(set(rows))
flag = [r for r in rows if re.search(r'\bA?GPL|Affero|UNKNOWN|NOT_INSTALLED', r[1], re.I)]
(out / 'THIRD_PARTY_LICENSES.md').write_text('# Third-party licences (pinned runtime)\n\n| Package | Licence |\n|---|---|\n' +
    ''.join(f'| {n} | {l} |\n' for n, l in rows) + '\nNeeds attention: ' + (', '.join(f'{n} ({l})' for n, l in flag) or 'none') + '\n'
    '\nMathJax (npm mathjax-full 3.2.2): Apache-2.0. Chromium via Playwright: BSD-style, downloaded at install time.\n')
print('LICENCE_AUDIT', 'REVIEW' if flag else 'PASS', [f'{n} ({l})' for n, l in flag])
PY
(cd "$(dirname "$out")" && tar -czf "$(basename "$out").tar.gz" "$(basename "$out")")
echo "BUILT $out"
