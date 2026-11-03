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

## 2026-10-29 · Draft verdict prompt version 2
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** prompts/verdict_v2.txt
- **Outcome:** Kept

### What I asked for
Find what went wrong in version 1 from the AI's own reasons in results/dev/v1/embedding.jsonl
(not the answer key): 14 of 24 answers were partial, (A) related tests called partial on
not_covered copies and (B) the right test found but not checking every word of the criterion.
Write prompts/verdict_v2.txt as a new file (verdict_v1.txt unchanged) that fixes A: decide in
order (find a test that sets up the "Given" and does the "when"; if none, not_covered even when
related tests exist; then covered or partial from what it asserts about the "then"), treat
"e.g." examples as illustrations, and ask for full test ids in tests_used. B is left to
criteria review, not loosened in the prompt, to avoid false all-clears. Compare v1 and v2
section by section before creating the file.

### How I checked it
Read the v1 vs v2 comparison properly. Read all of verdict_v2.txt before approving.

### What I kept or changed
Kept the draft unchanged, because I wasn't sure what to change. Left problem B out of the prompt, as the AI proposed. I'm not sure yet whether that's right. I want to see v2's real results first.

## 2026-10-30 · Refine verdict prompt version 2
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** prompts/verdict_v2.txt
- **Outcome:** Kept

### What I asked for
Explain why v1 gave mostly partial and not_covered, and how to improve a verdict prompt. Predict
on paper, without running anything, how v2 would answer each of the 24 v1 cases, then fix the
gaps that showed: step 3 now says a test that asserts nothing about the "then" is not_covered
(1142 not_covered), and step 1 says a test doing only part of the "when" (e.g. prepares but does
not send) is partial at most (stops 1142 and 2931 covered becoming false alarms). Left out of
the prompt on purpose: 1635 ac1 (search never finds the test), 1537 ac2 (float vs integer,
criteria/answer-key question for Xiaoning) and 4106 (a fix would overfit one dev case).

### How I checked it
Read and understood the two new lines before approving them. Applied v2 by hand to 4 cases, using only the AI's v1 reasons, not the test files. This was after the fixes were made.
Matched the AI's prediction on 1142 and 1635 ac2.
Differed on 3718 (me partial, AI not_covered) and 4106 (me not_covered, AI partial). Read the 24-case table, and the rest looked fine. 

### What I kept or changed
Accepted both fixes, because the 1142 and 2931 examples convinced me.

## 2026-11-03 · Stop evaluate.py runs overwriting each other
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/evaluation/evaluate.py, AGENTS.md
- **Outcome:** Kept

### What I asked for
Fix the evaluate.py bugs Gabriel reported (match on the full case id, take the results file as an
argument). Xiaoning's commit 182fc88 had already fixed those and the missing `false_all_clear`.
What was left: every round's results file is called `embedding.jsonl`, so v1, v1_k5 and v3 all
wrote `results/embedding_*.csv` and overwrote each other. The CSVs now go next to the results
file, and `--labels` lets the script be tested on a made-up key without opening the real one.

### How I checked it
Read the AI's explanation of the problem and its test result (perfect answers scored 1.0). Did not run it myself.

### What I kept or changed
Kept it as is, because without it the scores from different runs overwrite each other.

## 2026-11-03 · Draft test-set acceptance criteria
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** data/criteria_test_draft.jsonl
- **Outcome:** Changed

### What I asked for
Draft acceptance criteria for the 18 test-set issues from issue text only
(data/issue_text_test.jsonl), following prompts/draft_criteria.txt: Given/when/then, 1-2 per
issue, no invented details. 21 drafts, reviewed one by one as multiple-choice questions in chat;
final file: 22 criteria for 18 issues, all "reviewed": true. Flagged as weakest: 3738 (the issue
is a policy discussion), 6028 (only says "407 on Python 3.8.12"), 2873 (the issue doesn't say
what body should be sent).

### How I checked it
Read each issue summary and its criterion and decided whether to keep or drop the issue. 

### What I kept or changed

Kept all 18, added an ac2 for 1327 because  it's the general rule behind ac1, and the issue suggests it directly 
