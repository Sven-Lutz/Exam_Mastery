#!/usr/bin/env bash
# Read-only host check for the exam-mastery skill. Prints no secrets and changes nothing.
set -u
PY="${EXAM_MASTERY_PYTHON:-$HOME/.local/share/exam-mastery/venv/bin/python}"
CFG="${EXAM_MASTERY_CONFIG:-$HOME/.config/exam-mastery/config.json}"
ok=1; cfg_ok=1
say() { printf '%-22s %s\n' "$1" "$2"; }
if [ -x "$PY" ] && "$PY" -c 'import exam_mastery' 2>/dev/null; then say engine OK; else say engine "MISSING - run install.sh from the release package"; ok=0; fi
if command -v exam-mastery >/dev/null 2>&1; then say command "OK ($(command -v exam-mastery))"; else say command "MISSING - add ~/.local/bin to PATH or rerun install.sh"; ok=0; fi
if [ -d "$HOME/.cache/exam-mastery-v05-node/node_modules/mathjax-full" ]; then say math_runtime OK; else say math_runtime "MISSING - formulas cannot be rendered; rerun install.sh"; ok=0; fi
if [ -d "$HOME/.cache/exam-mastery-v05-node/node_modules/@fontsource/source-serif-4" ]; then say fonts OK; else say fonts "MISSING - documents fall back to system fonts; rerun install.sh"; fi
if [ -x "$PY" ] && "$PY" -c 'from playwright.sync_api import sync_playwright as s
with s() as p: p.chromium.launch().close()' >/dev/null 2>&1; then say chromium OK; else say chromium "MISSING - run: $PY -m playwright install chromium"; ok=0; fi
provider=""
if [ -f "$CFG" ]; then
  provider=$("$PY" -c 'import json,sys;c=json.load(open(sys.argv[1]));print(c["provider"],c["model"])' "$CFG" 2>/dev/null)
  say config "OK ($provider)"
else
  say config "NOT_CONFIGURED - production needs the one-time setup (SKILL.md step 2); status, update and visuals work without it"; cfg_ok=0
fi
if command -v codex >/dev/null 2>&1; then
  if codex login status >/dev/null 2>&1; then say codex "logged in"; else say codex "installed, not logged in (run: codex login)"; fi
  [ -x "$PY" ] && say codex_models "$("$PY" -c 'from exam_mastery.providers import codex_model_catalog as c;print(" ".join(sorted(c())))' 2>/dev/null || echo unknown)"
else
  say codex "not installed (optional)"
fi
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then say gemini_key "present (value not shown)"; else say gemini_key "not set (optional)"; fi
case "$provider" in
  codex*) command -v codex >/dev/null 2>&1 && codex login status >/dev/null 2>&1 || { say provider_ready "NO - configured codex is not logged in"; ok=0; } ;;
  gemini*) [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ] || "$PY" -c 'import json,sys;sys.exit(0 if json.load(open(sys.argv[1])).get("key_file") else 1)' "$CFG" || { say provider_ready "NO - configured gemini has no key"; ok=0; } ;;
esac
if [ $ok = 0 ]; then echo "HOST_NOT_READY"
elif [ $cfg_ok = 0 ]; then echo "HOST_READY_NO_PROVIDER  (status, update, visuals: ready; production: run the one-time setup first)"
else echo "HOST_READY"; fi
