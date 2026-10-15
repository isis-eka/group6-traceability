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
Claude scanned the files for API keys before the first push and found none. Comparing the
guides with our proposal doc showed the JSONL schemas Claude proposed do not match the doc's
"Shared files" section, and the partial variant is missing. The decision reasons were
drafted by Claude and still need team review.

### What I kept or changed
Kept the guides and decisions. Added the final-run model (gpt-6.1-sol), no GPT-4o, and the
three agent tools to the hard rules. Schemas still to be aligned with the proposal doc.

## 2026-10-15 · Role swap and issue-text-only export
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** README.md, AGENTS.md, CLAUDE.md, src/export_issue_text.py
- **Outcome:** Kept

### What I asked for
Update folder owners after the role swap, add a script that writes data/issue_text.jsonl
with only instance_id and problem_statement, and a rule that the criteria owner works only
from that file.

### How I checked it
Claude ran the script on a sample issue containing patch, test_patch and FAIL_TO_PASS; the
output had only instance_id and problem_statement. Not yet run on the real issues.jsonl.

### What I kept or changed
Kept as written. Claude also changed the labels.jsonl example labeler from Sammi to Xiaoning,
since the criteria owner must not see tests.

## 2026-10-15 · Automated AI use disclosure checks
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** tools/ai_disclosure.py, .githooks/commit-msg, .github/workflows/ai-disclosure.yml, .claude/settings.json, ai-log/, AGENTS.md, CLAUDE.md, README.md
- **Outcome:** Kept

### What I asked for
Automate the SE201 AI use disclosure policy for team members who use coding agents: commit
trailers, per-member ai-log files, and checks that catch missing entries.

### How I checked it
Claude tested the hook with an AI-trailer commit and no log (blocked), a bad Assisted-by
trailer (blocked), a malformed log entry (blocked) and a correct commit (accepted), and ran
check-logs and check-range on this repo.

### What I kept or changed
Kept as written.
