# Group 6: AI-Assisted Requirements-to-Test Traceability

Given an acceptance criterion and a project's tests + code, decide whether the criterion is
tested: `covered`, `partial`, `not_covered` or `needs_review`. Evaluated on SWE-bench issues
from `psf/requests` and `pallets/flask`. Python 3.10+, OpenAI API.

## Hard rules
- **Never read `data/labels.jsonl` or send it (or anything derived from it) to the model.** It is the answer key; only scoring code may open it.
- **Acceptance criteria are drafted from issue text only** (`problem_statement`). Never use tests, `test_patch`, `patch`, `FAIL_TO_PASS` or issue comments when drafting or reviewing them.
- **The acceptance criteria owner works only from `data/issue_text.jsonl`.** Never show them, or include in criteria-drafting prompts, any patch, test_patch, FAIL_TO_PASS or test file.
- **Never commit `.env`.** Keys live only in `.env` (copied from `.env.example`).
- Default model: **`gpt-6-luna`** (override with `OPENAI_MODEL` in `.env`). `gpt-6.1-sol` is for the one final run only. Never GPT-4o.
- Agent limits: **max 10 tool calls** per case, **read-only tools only** (`search_tests`, `grep`, `read_file`; no writes, no MCP, no coverage tracing), **max ~200 lines per file read**.

## Folder layout
| Path | Contents |
|---|---|
| `prompts/` | Plain-text prompts: `draft_criteria.txt`, `verdict_v1.txt` (bump version for changes) |
| `data/` | `issues.jsonl`, `issue_text.jsonl` (criteria drafting input), `cases.jsonl`, `labels.jsonl` |
| `src/` | Python scripts |
| `results/` | `results.jsonl`, score tables, charts |
| `workspace/` | Cloned requests/flask per case. Git-ignored, rebuilt by scripts |
| `docs/` | `decisions.md` (design decisions and why) |

## Running
```bash
pip install -r requirements.txt
cp .env.example .env        # then paste OPENAI_API_KEY
python src/load_swebench.py                     # -> data/issues.jsonl (requests + flask only)
python src/prepare_repo.py psf__requests-2317   # -> workspace/<id>/covered, workspace/<id>/not_covered
python src/export_issue_text.py                 # -> data/issue_text.jsonl (instance_id + problem_statement only)
```
`covered` = base commit + code fix + its tests; `not_covered` = base commit + code fix only.
Scripts are run from the repo root. Search index, verdict runner and scoring scripts are still to be added in `src/`.

## JSONL schemas (one JSON object per line)
These schemas are proposed: agree on them as a team before relying on them, and update this file when they change.

`data/cases.jsonl`: one row per (criterion, variant) to judge
```json
{"case_id": "psf__requests-2317__ac1__covered", "instance_id": "psf__requests-2317",
 "variant": "covered", "criterion": "Given ..., when ..., then ...",
 "workspace": "workspace/psf__requests-2317/covered"}
```

`data/labels.jsonl`: answer key, human-written, never shown to the model
```json
{"case_id": "psf__requests-2317__ac1__covered", "label": "covered",
 "labeler": "Xiaoning", "note": "test_x asserts the fixed behaviour"}
```
`label` is one of `covered | partial | not_covered`.

`results/results.jsonl`: one row per model run on a case
```json
{"case_id": "psf__requests-2317__ac1__covered", "verdict": "covered",
 "reason": "1-2 sentences", "tests_used": ["tests/test_requests.py::test_x"],
 "model": "gpt-6-luna", "prompt": "verdict_v1", "tool_calls": 4,
 "timestamp": "2026-10-15T12:00:00Z"}
```
`verdict` is one of `covered | partial | not_covered | needs_review`.

## Conventions
- Commit small and often with clear messages (e.g. "add verdict prompt v2").
- New prompt versions are new files (`verdict_v2.txt`); never edit a version already used in results.
