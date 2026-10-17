# Decisions

Design decisions for the project and why we made them. Add new ones at the bottom; if one
changes, edit it and say what replaced it rather than deleting it.

## 1. SWE-bench only (requests + flask), no demo repo
We evaluate only on real SWE-bench issues from `psf/requests` and `pallets/flask`. Each issue
comes with a real fix and real tests, which gives us ground truth for free; a hand-made demo
repo would be easy to bias toward our own tool and would not be credible as evidence.

## 2. Three versions compared against the same answer key
We build three versions of the tool and score all of them against one shared `labels.jsonl`.
Using a single fixed answer key means differences in scores come from the versions
themselves, not from changes in labelling.

## 3. Agent uses 3 generic tools: `search_tests`, `grep`, `read_file`
The agent gets the same kind of tools a developer would use, not tools written for these
repos. Custom tools could encode knowledge of the answer and would not carry over to other
projects; generic tools keep the result about the model's reasoning, not our tooling.

## 4. No MCP, no coverage tracing
Tools are plain Python functions called directly, and we do not run tests to collect coverage.
This keeps setup small and reproducible for the whole team, and coverage only shows code was
*executed*, not that the requirement's expected result was *checked*, which is what we judge.

## 5. gpt-6-luna for development, one final run on gpt-6.1-sol, no GPT-4o
All development and tuning runs use `gpt-6-luna` to keep cost and time low. The reported
results come from a single final run on `gpt-6.1-sol`, so we don't tune prompts on the
final model; GPT-4o is excluded because it is outdated next to these models.

## 6. Acceptance criteria are AI-drafted from issue text only, then human-reviewed
`prompts/draft_criteria.txt` drafts criteria from the issue's `problem_statement`, and a team
member reviews each one. Using issue text only stops tests or the fix from leaking into the
criteria (which would make "covered" trivially true); human review catches vague or wrong drafts.

## 7. Version 1 uses OpenAI embeddings stored locally, not hosted vector stores
Version 1 uses OpenAI embeddings stored locally instead of hosted vector stores, so each test function stays one chunk and covered/not_covered share embeddings where the test text is identical.

## 8. A 10-issue dev set, then a separate test set
Version 1 is tuned on 10 dev issues (9 `psf/requests`, 1 `pallets/flask`) listed in
`data/chosen_issues.json`. Prompts are frozen after tuning, and reported results come from a
separate test set of new issues, so scores aren't inflated by tuning on the same issues.

## 9. The answer key stays off GitHub
`labels*.jsonl` is git-ignored and shared privately with the answer key and scoring owners,
never with the acceptance criteria owner. If it were in the repo, the criteria owner or an AI
tool working in the repo could see which tests are the right answer, and results would no
longer be a fair test.

## 10. Version 1 judges each criterion on a covered and a not_covered copy
Up to the midpoint checkpoint, every criterion runs on two copies of the code: with the fix's
tests (right answer: `covered`) and without them (right answer: `not_covered`). This checks the
tool can say "not covered", not just find tests. `partial` cases are added after the
checkpoint. Tests are matched by pytest id at function level, ignoring parametrize `[...]`
parts, because one search chunk is a whole test function.
