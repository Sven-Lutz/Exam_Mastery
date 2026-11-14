# Exam Mastery

One lecture folder in, source-grounded learning materials out: textbook chapters, workbook tasks, worked
solutions, a mock exam with points, an Anki deck, and HTML/PDF - each chapter with a quality dossier.

## Install (macOS/Linux, Python 3.12, Node.js)

```bash
tar -xzf exam-mastery-<version>.tar.gz && cd exam-mastery-<version>
./install.sh --library "<your skill library>"    # or just ./install.sh
```
This creates:
- its own Python environment in `~/.local/share/exam-mastery`;
- the command `~/.local/bin/exam-mastery`;
- the formula renderer (MathJax) and Chromium for PDF checks;
- the agent skill. With `--library`, it is copied once to `<library>/exam-mastery` and `~/.claude/skills/exam-mastery`
  becomes a link to it. Without `--library`, it is copied to `~/.claude/skills/exam-mastery`.

**Update:** unpack the newer package and run `./install.sh` again; the library is remembered.
- Replaced: the engine, the command and the skill files. A skill folder with local changes is first moved to `~/.local/share/exam-mastery-backups/`.
- Kept: config, outputs, runs, Anki state and lecture folders.

## Configure a provider once

You need one model access you already have. Nothing has to be bought.

| Provider | Needs | Setup |
|---|---|---|
| `agent` (recommended in Claude Code / Codex) | the agent session running the skill | `exam-mastery --setup --provider agent --accept-data-transfer` |
| Codex CLI | `codex login` with a ChatGPT account | `exam-mastery --setup --provider codex --model <model> --accept-data-transfer` |
| Gemini API (optional) | `GEMINI_API_KEY` (paid key recommended) | `exam-mastery --setup --provider gemini --model gemini-3.8-flash --accept-data-transfer --max-cost-usd 5` |

`bash ~/.claude/skills/exam-mastery/scripts/check_host.sh` shows what is ready and lists the Codex models
your account offers. The config is `~/.config/exam-mastery/config.json` (mode 0600). It holds the provider, the model,
your consent that course files are sent to that provider, and a per-run limit on requests, time and (Gemini) cost.
API keys are never stored there.

## Use

```bash
exam-mastery "/path/to/lecture folder"      # produce (or: cd into the folder and run exam-mastery)
exam-mastery status  ["/path/..."]          # what exists, did sources change (read-only)
exam-mastery update  ["/path/..."]          # offline: which chapters are CURRENT / STALE / NEW / SOURCE_REMOVED
exam-mastery update --produce               # regenerate only STALE and NEW chapters (provider calls)
exam-mastery visuals ["/path/..."]          # worklist of figure slides for the agent to read; then --import evidence.json
```
Claude Code: `/exam-mastery ...`; Codex: `$exam-mastery ...` (same skill, linked from `~/.agents/skills`).
In Claude Code: `/exam-mastery`, `/exam-mastery /path`, `/exam-mastery status`, `/exam-mastery update`.

Results go to `~/Exam_Mastery_Output/course-<id>/ch-<run>/` (change with `EXAM_MASTERY_OUTPUT`). Your lecture
folder is never written to; its files are hashed before and after each run.

Open `LERNMATERIAL/` in the run folder: one folder per chapter with `1_Lehrbuch.pdf`, `2_Arbeitsbuch.pdf`,
`3_Musterloesungen.pdf`, `4_Probeklausur.pdf`, `5_Quellenabbildungen_nicht_ausgewertet.pdf`, `kapitel.html`, the Anki
`.apkg` and `LIES_MICH.md` (what was checked, what was not). `sample_output/` shows synthetic examples (Mathematics,
Law, ML fixtures): they demonstrate layout and mechanics, not content quality.

## When the provider quota is used up
The run stops with exit 3 (`QUOTA_BLOCKED`) and nothing is lost. Start the same folder again after the reset time the
provider shows. No other provider is used automatically.

## Uninstall
`./uninstall.sh` (add `--all` to also remove the config). Outputs and lecture folders are never deleted.

## What is automatic, what is not

- Automatic: source inventory and fidelity checks, curriculum and exam analysis, chapter planning, writing,
  items, solutions, model review, one revision round, deterministic gates (anchors, source numbers, step
  arithmetic, formulas, figures), publishing and Anki checks.
- Competencies whose slide also carries a figure are taught from the slide text only and labelled so; content
  that exists only inside a chart or a scan is not produced and is listed as an open item.
- Asked of you only when the engine cannot settle it: chapter order or session conflicts, ineligible chapters.
- Never automatic: subject-matter approval. Model reviews are not independent verification; have a subject
  expert read the PDF before relying on it.

## Verify the installation

```bash
cd engine && ~/.local/share/exam-mastery/venv/bin/python -m unittest discover -s tests
```

See `RELEASE_NOTES.md` for known limitations.
