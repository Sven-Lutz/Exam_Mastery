#!/bin/zsh
set -eu
engine_dir="${0:A:h:h}"
python_env="${EXAM_MASTERY_PYTHON_ENV:-$HOME/.local/share/exam-mastery/dev-venv}"
node_env="$HOME/.cache/exam-mastery-v05-node"
"${EXAM_MASTERY_PYTHON_BUILD:-python3.12}" -m venv "$python_env"   # the tested runtime is Python 3.12
"$python_env/bin/pip" install --no-compile -r "$engine_dir/requirements-math-tested.txt"
"$python_env/bin/pip" install --no-compile -r "$engine_dir/requirements-gemini-tested.txt"
npm install --prefix "$node_env" --save-exact mathjax-full@3.2.2
"$python_env/bin/python" -m playwright install chromium
