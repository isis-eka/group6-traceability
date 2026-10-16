# Group 6: AI-Assisted Requirements-to-Test Traceability

Given an acceptance criterion and a project's tests + code, decide whether the criterion is
tested: `covered`, `partial`, `not_covered` or `needs_review`. Evaluated on SWE-bench issues
from `psf/requests` and `pallets/flask`. Python 3.10+, OpenAI API.

## Hard rules
- **Never read `data/labels.jsonl` or `data/labels_v1.jsonl` or send them (or anything derived from them) to the model.** They are the answer key; only scoring code may open them. Never commit them (`data/labels*.jsonl` is git-ignored); they are shared privately.
- **Acceptance criteria are drafted from issue text only** (`problem_statement`). Never use tests, `test_patch`, `patch`, `FAIL_TO_PASS` or issue comments when drafting or reviewing them.
- **The acceptance criteria owner works only from issue-text files** (`data/issue_text.jsonl`; for version 1, `data/issue_text_v1.jsonl`). Never show them, or include in criteria-drafting prompts, any patch, test_patch, FAIL_TO_PASS or test file.
- **Never commit `.env`.** Keys live only in `.env` (copied from `.env.example`).
- Default model: **`gpt-6-luna`** (override with `OPENAI_MODEL` in `.env`). `gpt-6.1-sol` is for the one final run only. Never GPT-4o.
- Agent limits: **max 10 tool calls** per case, **read-only tools only** (`search_tests`, `grep`, `read_file`; no writes, no MCP, no coverage tracing), **max ~200 lines per file read**.

## AI use disclosure (SE201 policy, required on every commit with AI-assisted work)
- Add the trailer `Assisted-by: <tool> (<model>)` (e.g. `Assisted-by: Codex (gpt-6-luna)`). Your own `Co-Authored-By:` line also counts.
- In the **same commit**, append an entry to `ai-log/<member>.md` for the person you work for (e.g. `ai-log/isis-eka.md`). If there's no file, copy `ai-log/your-name.md`; ask their name if unsure. Use one entry per task in the template's format. Outcome is `Kept`, `Changed` or `Rejected`.
- Never write "How I checked it" or "What I kept or changed" yourself: they are the member's own check and judgment. Leave both as `[to fill by <member name>]` (e.g. `[to fill by Isis Eka]`) and remind them to fill them in. `python tools/ai_disclosure.py summary` lists unfinished entries: any line starting with `[to fill` counts.
- `.githooks/commit-msg` blocks AI commits without a log entry. If `git config core.hooksPath` is not `.githooks`, set it.

## Folder layout
| Path | Contents |
|---|---|
| `prompts/` | Plain-text prompts: `draft_criteria.txt`, `verdict_v1.txt` (bump version for changes) |
| `data/` | `issues.jsonl`, `issue_text.jsonl` (both git-ignored, rebuilt by scripts), `cases.jsonl`, `labels.jsonl`; version 1 (10 dev issues: 9 `psf/requests`, 1 `pallets/flask`): `chosen_issues.json` (issue ids and split only), `issue_text_v1.jsonl` (criteria drafting input), `labels_v1.jsonl` (answer key; git-ignored, shared privately), `index_v1/` (embedded test-function chunks, git-ignored, rebuilt by `build_index.py`) |
| `src/` | Python scripts |
| `results/` | `results.jsonl`, score tables, charts |
| `workspace/` | Cloned requests/flask per case. Git-ignored, rebuilt by scripts |
| `docs/` | `decisions.md` (design decisions and why) |
| `ai-log/` | AI use log per member; `tools/ai_disclosure.py` checks them |

## Running
```bash
pip install -r requirements.txt
cp .env.example .env        # then paste OPENAI_API_KEY
python src/load_swebench.py                     # -> data/issues.jsonl (requests + flask only)
python src/prepare_repo.py psf__requests-2317   # -> workspace/<id>/covered, workspace/<id>/not_covered
python src/export_issue_text.py                 # -> data/issue_text.jsonl (instance_id + problem_statement only)
python src/build_index.py --dry-run             # -> workspace/_chunks/ (chunks only, no API calls)
python src/build_index.py                       # -> data/index_v1/<id>__<variant>.jsonl (one embedded chunk per test function)
python src/search_tests.py psf__requests-1142 covered "<query>"   # top 3 test_ids + scores
python src/run_v1.py --dry-run --limit 1        # print one verdict prompt, no API call
python src/run_v1.py                            # data/cases.jsonl -> results/results.jsonl (version 1)
python src/run_v1.py --ollama                   # same, verdicts on local Ollama qwen3:8b (testing only)
```
`covered` = base commit + code fix + its tests; `not_covered` = base commit + code fix only.
Scripts are run from the repo root. `run_v1.py` defaults to the embedding search (`src/search_tests.py`)
and the OpenAI model from `.env`. Fallbacks, each printed as a NOTE: no OpenAI key or a missing index ->
keyword search (`src/search_bm25.py`, later the BM25 baseline); no OpenAI key -> local Ollama
(`qwen3:8b`). `--search search_bm25` and `--ollama [MODEL]` choose them explicitly. Each result row
records the search and model actually used; only OpenAI + embedding-search rows are reportable.
Scoring scripts are still to be added in `src/`.

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
