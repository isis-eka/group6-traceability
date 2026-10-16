# AI Use Log: Sammi Chua

## 2026-10-16 · Review and complete version 1 acceptance criteria
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** data/cases.jsonl
- **Outcome:** Kept

### What I asked for
Work through my version 1 tasks step by step from issue text only (data/issue_text_v1.jsonl):
check the 8 existing criteria in data/cases.jsonl against their issues (kept all unchanged to
avoid invalidating existing labels), draft one criterion each for the 4 issues without one
(psf__requests-3718, psf__requests-4106, psf__requests-5087, pallets__flask-5014) as covered
and not_covered rows, mark all 24 rows reviewed, and review prompts/verdict_v1.txt (no v2
until version 1 results show what to fix).

### How I checked it
For each of the 10 issues, I read the issue, then its criterion, then checked if what Ai output made sense. Made the ai tell me wat happened and I will decide whether it should proceed or do over. 

### What I kept or changed
For 1537, I kept ac2 (int) instead of switching to the AI’s datetime criterion because the criterion isn't wrong, just a weaker test of the bug. Datetime can still be added later as a new ac3. 
For 5414, I kept my original wording over the AI’s rewrite because Xiaoning had already written answer-key labels for those exact criteria. Changing the text could make those labels wrong. 
For the 4 new criteria (3718, 4106, 5087, flask-5014), I accepted the AI’s drafts as written. 4106 and 5087 already have “Expected Result” sections and flask-5014 is a 2-line request, so the drafts repeated them almost word for word and there was little to reword. 3718 is vague, but the traceback shows one clear fact (the crash comes from self.raw.read when raw is None), so a narrow, testable criterion was possible. I also didn’t mark it UNCLEAR because that would drop the issue and leave 9 for the demo, and keeping it shows how the tool handles a vague issue
