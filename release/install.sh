#!/usr/bin/env bash
# Exam Mastery installer and updater: engine into its own venv, `exam-mastery` command, math runtime, agent skill.
#
#   ./install.sh [--library DIR] [--skills-dir DIR]
#
# --library DIR   canonical skill location (e.g. your skill library). The skill is copied to DIR/exam-mastery and the
#                 agent host gets a symbolic link to it, so there is exactly one maintained copy. Remembered for updates.
# --skills-dir    the agent host's skill folder (default ~/.claude/skills).
# With --library, ~/.agents/skills/exam-mastery (read by Codex as $exam-mastery) is linked too; --no-agents-link skips it.
#
# Re-running it with a newer package is the update path. It replaces only the engine, the command and the skill files.
# Kept: your config (~/.config/exam-mastery), all outputs and runs (~/Exam_Mastery_Output), Anki state files in the
# output folders, your Anki collections and every lecture folder. A skill folder that differs from the new one is moved
# to ~/.local/share/exam-mastery-backups/ before it is replaced (never into a skill folder).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
home="${EXAM_MASTERY_HOME:-$HOME/.local/share/exam-mastery}"
skills_dir="$HOME/.claude/skills"; library=""; extra_links="$HOME/.agents/skills"
[ -f "$home/install.env" ] && . "$home/install.env"          # remembered library / skills dir of an earlier install
while [ $# -gt 0 ]; do case "$1" in
  --skills-dir) skills_dir="$2"; shift 2;;
  --library) library="$2"; shift 2;;
  --no-agents-link) extra_links=""; shift;;
  *) echo "unknown option $1"; exit 2;;
esac; done
version="$(cat "$here/VERSION" 2>/dev/null || echo unknown)"
node_env="$HOME/.cache/exam-mastery-v05-node"
pybin="${EXAM_MASTERY_PYTHON_BUILD:-python3.12}"
command -v "$pybin" >/dev/null || { echo "needs $pybin (tested runtime); set EXAM_MASTERY_PYTHON_BUILD to another python>=3.10 at your own risk"; exit 2; }
command -v npm >/dev/null || { echo "needs Node.js/npm for formula rendering (MathJax)"; exit 2; }
stamp="$(date +%Y%m%d-%H%M%S)"

# ---- engine (replaced in place; config and outputs live elsewhere and are not touched)
[ -x "$home/venv/bin/python" ] || "$pybin" -m venv "$home/venv"
"$home/venv/bin/pip" install --quiet --no-compile -r "$here/engine/requirements-math-tested.txt" -r "$here/engine/requirements-gemini-tested.txt"
"$home/venv/bin/pip" install --quiet --no-compile --no-deps --force-reinstall "$here/engine"
npm install --silent --prefix "$node_env" --save-exact mathjax-full@3.2.2 @fontsource/source-serif-4@5.1.0 @fontsource/source-sans-3@5.1.0 @fontsource/jetbrains-mono@5.1.0
"$home/venv/bin/python" -m playwright install chromium
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/exam-mastery" <<W
#!/bin/sh
export EXAM_MASTERY_PYTHON="$home/venv/bin/python"
exec "$home/venv/bin/python" -P -m exam_mastery.onepath "\$@"
W
chmod 755 "$HOME/.local/bin/exam-mastery"

# ---- skill: one canonical copy; the host folder links to it
backups="$HOME/.local/share/exam-mastery-backups"   # outside every skill folder: a backup must never load as a second skill
backup() {  # move $1 aside if it differs from the new skill
  if [ -e "$1" ] && ! [ -L "$1" ] && ! diff -rq "$1" "$here/skill/exam-mastery" >/dev/null 2>&1; then
    mkdir -p "$backups"; mv "$1" "$backups/skill-$stamp-$(basename "$(dirname "$1")")"; echo "backed up differing skill: $backups/skill-$stamp-$(basename "$(dirname "$1")")"
  else rm -rf "$1"; fi
}
mkdir -p "$skills_dir"
if [ -n "$library" ]; then
  mkdir -p "$library"; target="$library/exam-mastery"
  backup "$target"; cp -R "$here/skill/exam-mastery" "$target"
  if [ -L "$skills_dir/exam-mastery" ]; then rm "$skills_dir/exam-mastery"; else backup "$skills_dir/exam-mastery"; fi
  ln -s "$target" "$skills_dir/exam-mastery"
  # other agent hosts that read ~/.agents/skills (e.g. Codex: $exam-mastery) get a link to the same canonical copy
  for extra in $extra_links; do
    mkdir -p "$extra"
    if [ -L "$extra/exam-mastery" ]; then rm "$extra/exam-mastery"; else backup "$extra/exam-mastery"; fi
    ln -s "$target" "$extra/exam-mastery"
  done
else
  if [ -L "$skills_dir/exam-mastery" ]; then rm "$skills_dir/exam-mastery"; else backup "$skills_dir/exam-mastery"; fi
  cp -R "$here/skill/exam-mastery" "$skills_dir/exam-mastery"; target="$skills_dir/exam-mastery"
fi
printf 'library=%q\nskills_dir=%q\nextra_links=%q\n' "$library" "$skills_dir" "$extra_links" > "$home/install.env"
printf '{"version": "%s", "installed": "%s", "skill": "%s", "host_link": "%s"}\n' "$version" "$stamp" "$target" "$skills_dir/exam-mastery" > "$home/INSTALLED.json"
echo "Installed $version. Skill: $target  (host: $skills_dir/exam-mastery)  Command: ~/.local/bin/exam-mastery"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) echo "Add to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\"";; esac
(cd "$target" && bash scripts/check_host.sh) || true
