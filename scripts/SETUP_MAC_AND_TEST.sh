#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[qa]'
python -m playwright install chromium
python -m exam_mastery.cli preflight
python -m unittest discover -s tests -v
python -m exam_mastery.cli verify-freeze
printf '\nReady for a blind run if both Claude and Gemini CLIs are authenticated.\n'
printf 'Use README.md instructions; do not reveal holdout material before freeze.\n'
