# AI Use Log: Isis Eka

## 2026-10-15 · Repository setup, agent guides and design decisions
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** CLAUDE.md, AGENTS.md, docs/decisions.md
- **Outcome:** Changed

### What I asked for
Create the GitHub repo from the project zip, then write CLAUDE.md and AGENTS.md (summary,
folder layout, how to run scripts, JSONL schemas, hard rules) and docs/decisions.md from our
list of six decisions, with the reason for each.

### How I checked it
I compared the Agents/claude & readme file contents with our revised proposal document that i generated with claude regarding the project's design and architecture 
for architectural design i reviewed the decisions.md and ensured it aligned with our team's goals 

### What I kept or changed
Kept the guides and decisions and suggested file structure. verified that we'll be using gpt 6 models & noted that gpt 4o will be discontinued soon by openai 

## 2026-10-15 · Role swap and issue-text-only export
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** README.md, AGENTS.md, CLAUDE.md, src/export_issue_text.py
- **Outcome:** Kept

### What I asked for
Update folder owners after the role swap, add a script that writes data/issue_text.jsonl
with only instance_id and problem_statement, and a rule that the criteria owner works only from that file.

### How I checked it
[to fill - have yet to verify JSON schema] 

### What I kept or changed
Kept written. 

## 2026-10-15 · Automated AI use disclosure checks
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** tools/ai_disclosure.py, .githooks/commit-msg, .github/workflows/ai-disclosure.yml, .claude/settings.json, ai-log/, AGENTS.md, CLAUDE.md, README.md
- **Outcome:** Kept

### What I asked for
Automate the SE201 AI use disclosure policy for team members who use coding agents: commit trailers, per-member ai-log files, and checks that catch missing entries.

### How I checked it
I tested the hook with an AI-trailer commit, read throught the logs and filled up the how i checked sections, realised that the agent is autofilling the how i checked AI output and adjusted the automated disclosure script to have it fill [ to fill] by default 

### What I kept or changed 
 needed to change which sections AI agents should be filling up 

## 2026-10-15 · Leave "How I checked it" for members to write
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** ai-log/isis-eka.md, ai-log/your-name.md, AGENTS.md, CLAUDE.md, README.md, tools/ai_disclosure.py
- **Outcome:** Kept

### What I asked for
Agents should not write "How I checked it". Leave it as [to fill by <member name>] by default.

### How I checked it
tested another agent commit and verified in the disclosure log 

### What I kept or changed
realised what i kept and changed should also be written by user and got claude to adjust the instuctions to agents verified the instructions exist in agents.md & claude/md : '- Never write "How I checked it": they are the member's own check and judgment. Leave both as `[to fill by <member name>]` (e.g. `[to fill by Isis Eka]`) and remind them to fill them in. `python tools/ai_disclosure.py summary` lists unfinished entries: any line starting with `[to fill` counts.'


## 2026-10-15 · Leave "What I kept or changed" for members to write
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** ai-log/isis-eka.md, ai-log/your-name.md, AGENTS.md, CLAUDE.md, README.md, tools/ai_disclosure.py
- **Outcome:** Kept

### What I asked for
"What I kept or changed" should also be written by the member. Agents leave it as [to fill by <member name>], and the summary flags it.

### How I checked it
Verified in agents.md and claude.md 

### What I kept or changed
kept changes 

## 2026-10-16 · Prepare 7 issues for version 1
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** .gitignore, data/chosen_issues.json, data/issue_text_v1.jsonl, data/labels_v1.jsonl
- **Outcome:** Kept

### What I asked for
Record the 7 chosen issues and their right-answer tests, check them against FAIL_TO_PASS, build covered and not_covered copies, write the issue text for Sammi and the draft answer key for Xiaoning.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Expand dev set to 10 issues and use full test ids
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** data/chosen_issues.json, data/issue_text_v1.jsonl, data/labels_v1.jsonl, README.md
- **Outcome:** Kept

### What I asked for
Add psf__requests-4106, psf__requests-5087 and pallets__flask-5014 to the dev set, mark all issues as split "dev", prepare and check their repos, regenerate the issue text, add their labels, and convert every test name to the full pytest id from FAIL_TO_PASS. Note in the README how parametrized tests are matched.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Make AGENTS.md the single instructions file
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** AGENTS.md, CLAUDE.md
- **Outcome:** Kept

### What I asked for
Update the version 1 description to 10 dev issues (9 requests, 1 flask). Move all instructions into AGENTS.md and make CLAUDE.md a single line, @AGENTS.md, so there is only one file to keep updated.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Keep answer keys out of git
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** .gitignore, AGENTS.md, data/labels_v1.jsonl (untracked)
- **Outcome:** Kept

### What I asked for
Stop tracking data/labels_v1.jsonl (keep the local copy), gitignore data/labels*.jsonl, and suggest how the team should share the answer key instead.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Remove right-answer tests from chosen_issues.json
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** data/chosen_issues.json, README.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Keep only instance_id and split in data/chosen_issues.json, so the right-answer tests live only in the git-ignored labels_v1.jsonl.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Build the test search index for version 1
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/build_index.py, src/search_tests.py, README.md, AGENTS.md, docs/decisions.md, .gitignore
- **Outcome:** Kept

### What I asked for
Write build_index.py (one chunk per test function via ast, decorators included, test_id in the README format, embedded locally with text-embedding-3-small, cached by text hash, --dry-run and --only) and search_tests.py (top-k cosine search, command-line use). Dry-run all 10 issues and check the right-answer tests appear only in covered. Document both scripts and add decision 7. Then remove line numbers from the chunk header text so identical tests share one embedding.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-16 · Make the embedding search fit run_v1.py
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/search_tests.py, AGENTS.md, README.md
- **Outcome:** Kept

### What I asked for
Change search_tests.py to Gabriel's interface, search_tests(workspace, criterion, k=3) returning "code", so run_v1.py --search search_tests works. Test it and commit.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-17 · Add architecture diagrams and decisions 8–10
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** docs/architecture.md, docs/decisions.md, README.md
- **Outcome:** Kept

### What I asked for
Add decisions 8–10 (10-issue dev set then a separate test set, answer key kept off GitHub, covered/not_covered copies for version 1 up to the midpoint checkpoint with partial added after). Add a pipeline diagram and a data model diagram in Mermaid to docs/architecture.md, check they render, and link them from the README.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-17 · Fix Xiaoning's evaluation scripts
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/evaluation/evaluate.py, src/evaluation/sanity_check_labels.py, requirements.txt
- **Outcome:** Changed

### What I asked for
Review Xiaoning's latest evaluation scripts and make the remaining fixes for her: add the missing false_all_clear counter (evaluate.py crashed with a KeyError), read results from results/results.jsonl, run the label check from the repo root, remove an unused import, and add pandas and matplotlib to requirements.txt. Tested all three scripts on a small fake answer key and fake results.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-18 · Mock runs of version 1 and results file naming
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/evaluation/evaluate.py, src/evaluation/plot_metrics.py, README.md, .gitignore, results/v1_mock_embedding.jsonl, results/v1_mock_bm25.jsonl, results/*_metrics.csv, results/comparison_*.png
- **Outcome:** Changed

### What I asked for
Run version 1 once on all 24 cases with gpt-6-luna as a mock run (embedding search), then again with keyword search (BM25), and score both with Xiaoning's scripts. Name results files <version>_<run>_<search>.jsonl, let evaluate.py and plot_metrics.py take the run file so scores and charts are named after it, and document the naming in the README. Keep the per-case _summary.csv files out of git because they list the answer key tests.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]

## 2026-10-18 · Write up the version 1 mock run results
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** docs/results/results_v1_mock.md
- **Outcome:** Kept

### What I asked for
Write up the two mock runs in docs/results/results_v1_mock.md: what we ran, the scores for both searches, how to read them, the failures observed and next steps. Note at the top that it is a mock run to test the pipeline end to end, because the answer key has no partial cases yet.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
[to fill by Isis Eka]
