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
Kept as written. Claude also changed the labels.jsonl example labeler from Sammi to Xiaoning,
since the criteria owner must not see tests.

## 2026-10-15 · Automated AI use disclosure checks
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** tools/ai_disclosure.py, .githooks/commit-msg, .github/workflows/ai-disclosure.yml, .claude/settings.json, ai-log/, AGENTS.md, CLAUDE.md, README.md
- **Outcome:** Kept

### What I asked for
Automate the SE201 AI use disclosure policy for team members who use coding agents: commit trailers, per-member ai-log files, and checks that catch missing entries.

### How I checked it
I tested the hook with an AI-trailer commit, read throught the logs and filled up the how i checked sections, realised that the agent is autofilling the how i checked AI output and adjusted the automated disclosure script to have it fill [ to fill] by default 

### What I kept or changed
Kept as written. 

## 2026-10-15 · Leave "How I checked it" for members to write
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** ai-log/isis-eka.md, ai-log/your-name.md, AGENTS.md, CLAUDE.md, README.md, tools/ai_disclosure.py
- **Outcome:** Kept

### What I asked for
Agents should not write "How I checked it". Leave it as [to fill by <member name>] by default.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
Kept as written. The summary command now lists entries still to fill.

## 2026-10-15 · Sync AGENTS.md with CLAUDE.md placeholder rule
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** AGENTS.md
- **Outcome:** Kept

### What I asked for
Commit my latest edits. Claude copied my new CLAUDE.md line about the summary command into AGENTS.md so both guides match.

### How I checked it
[to fill by Isis Eka]

### What I kept or changed
Kept as written.
