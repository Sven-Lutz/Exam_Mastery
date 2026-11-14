#!/usr/bin/env bash
# Removes what install.sh created: engine venv, command, the host's skill link. The canonical skill copy in your
# library is kept unless you pass --all. Config (~/.config/exam-mastery) is removed only with --all; outputs
# (~/Exam_Mastery_Output), lecture folders and Anki collections are never touched.
set -euo pipefail
home="${EXAM_MASTERY_HOME:-$HOME/.local/share/exam-mastery}"
skills_dir="$HOME/.claude/skills"; library=""; extra_links=""; all=0
[ -f "$home/install.env" ] && . "$home/install.env"
while [ $# -gt 0 ]; do case "$1" in --skills-dir) skills_dir="$2"; shift 2;; --all) all=1; shift;; *) echo "unknown option $1"; exit 2;; esac; done
if [ -L "$skills_dir/exam-mastery" ]; then rm "$skills_dir/exam-mastery"; else rm -rf "$skills_dir/exam-mastery"; fi
for extra in ${extra_links:-}; do [ -L "$extra/exam-mastery" ] && rm "$extra/exam-mastery"; done
rm -rf "$home"; rm -f "$HOME/.local/bin/exam-mastery"
if [ $all = 1 ]; then
  rm -rf "$HOME/.config/exam-mastery"
  [ -n "$library" ] && rm -rf "$library/exam-mastery"
  echo "config and library skill removed; outputs in ~/Exam_Mastery_Output kept (delete them yourself if wanted)"
elif [ -n "$library" ]; then echo "library skill kept: $library/exam-mastery"; fi
echo "Exam Mastery uninstalled. The MathJax/Chromium caches (~/.cache/exam-mastery-v05-node, Playwright) are shared and kept."
