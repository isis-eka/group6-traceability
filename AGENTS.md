# Group 6: AI-Assisted Requirements-to-Test Traceability

Given an acceptance criterion and a project's tests + code, decide whether the criterion is
tested: `covered`, `partial`, `not_covered` or `needs_review`. Evaluated on SWE-bench issues
from `psf/requests` and `pallets/flask`. Python 3.10+, OpenAI API.

## Hard rules
- **Never read any answer key (`data/labels*.jsonl`, e.g. `labels_dev.jsonl`, or the labeller's notes in `answer_keys/`) or send it (or anything derived from it) to the model.** Only scoring code may open them. Never commit them (both are git-ignored); they are shared privately.
- **Acceptance criteria are drafted from issue text only** (`problem_statement`). Never use tests, `test_patch`, `patch`, `FAIL_TO_PASS` or issue comments when drafting or reviewing them.
- **The acceptance criteria owner works only from issue-text files** (`data/issue_text.jsonl`; for version 1, `data/issue_text_v1.jsonl`; for the test set, `data/issue_text_test.jsonl`). Never show them, or include in criteria-drafting prompts, any patch, test_patch, FAIL_TO_PASS or test file.
- **Never commit `.env`.** Keys live only in `.env` (copied from `.env.example`).
- Default model: **`gpt-6-luna`** (override with `OPENAI_MODEL` in `.env`). `gpt-6.1-sol` is for the one final run only. Never GPT-4o.
- Agent limits: **max 10 tool calls** per case, **read-only tools only** (`search_tests`, `grep`, `read_file`; no writes, no MCP, no coverage tracing), **max ~200 lines per file read**.
- **Agent tools may only read inside the current case's workspace folder** (`workspace/<instance_id>/<variant>/`): never `.git`, `workspace/_source/`, another case's folder or anything outside `workspace/`. The copies have no git history (`prepare_repo.py` deletes it) because it contains the real fix and its tests.

## AI use disclosure (SE201 policy, required on every commit with AI-assisted work)
- Add the trailer `Assisted-by: <tool> (<model>)` (e.g. `Assisted-by: Codex (gpt-6-luna)`). Your own `Co-Authored-By:` line also counts.
- In the **same commit**, append an entry to `ai-log/<member>.md` for the person you work for (e.g. `ai-log/isis-eka.md`). If there's no file, copy `ai-log/your-name.md`; ask their name if unsure. Use one entry per task in the template's format. Outcome is `Kept`, `Changed` or `Rejected`.
- Never write "How I checked it" or "What I kept or changed" yourself: they are the member's own check and judgment. Leave both as `[to fill by <member name>]` (e.g. `[to fill by Isis Eka]`) and remind them to fill them in. `python tools/ai_disclosure.py summary` lists unfinished entries: any line starting with `[to fill` counts.
- `.githooks/commit-msg` blocks AI commits without a log entry. If `git config core.hooksPath` is not `.githooks`, set it.

## Folder layout
| Path | Contents |
|---|---|
| `prompts/` | Plain-text prompts: `draft_criteria.txt`, `verdict_v1.txt`, `verdict_v2.txt`, `agent_v1.txt`, `no_retrieval_v1.txt` (bump version for changes; frozen since 31 Oct) |
| `data/` | `issues.jsonl`, `issue_text.jsonl` (both git-ignored, rebuilt by scripts), `cases.jsonl`, `labels_dev.jsonl` (dev answer key, one row per case; git-ignored, shared privately); version 1 (10 dev issues: 9 `psf/requests`, 1 `pallets/flask`): `chosen_issues.json` (issue ids and split only: 10 `dev`, 18 `test`), `issue_text_v1.jsonl` (criteria drafting input), `labels_v1.jsonl` (first answer key, one row per issue and copy, replaced by `labels_dev.jsonl`; git-ignored), `index_v1/` (embedded test-function chunks, git-ignored, rebuilt by `build_index.py`); test set (18 issues, added to `chosen_issues.json` by `src/pick_test_set.py`): `issue_text_test.jsonl` (criteria drafting input) |
| `src/` | Python scripts; `src/evaluation/` holds the scoring scripts (`sanity_check_labels.py`, `evaluate.py`, `plot_metrics.py`; first drafts, still under review). Only scoring code may open the label files |
| `results/` | One folder per round: `results/<split>/<round>/<search>.jsonl` (e.g. `results/dev/v3/embedding.jsonl`), score tables, charts |
| `workspace/` | Cloned requests/flask per case. Git-ignored, rebuilt by scripts |
| `docs/` | `decisions.md` (design decisions and why), `architecture.md` (Mermaid diagrams: pipeline and data model) |
| `ai-log/` | AI use log per member; `tools/ai_disclosure.py` checks them |

## Running
```bash
pip install -r requirements.txt
cp .env.example .env        # then paste OPENAI_API_KEY
python src/load_swebench.py                     # -> data/issues.jsonl (requests + flask only)
python src/prepare_repo.py psf__requests-2317   # -> workspace/<id>/covered, workspace/<id>/not_covered (--all: dev set, --test: test set)
python src/export_issue_text.py                 # -> data/issue_text.jsonl (instance_id + problem_statement only)
python src/build_index.py --dry-run             # -> workspace/_chunks/ (chunks only, no API calls)
python src/build_index.py                       # -> data/index_v1/<id>__<variant>.jsonl (one embedded chunk per test function)
python src/search_tests.py psf__requests-1142 covered "<query>"   # top 3 test_ids + scores
python src/run_v1.py --dry-run --limit 1        # print one verdict prompt, no API call
python src/run_v1.py                            # data/cases.jsonl -> results/results.jsonl (version 1)
python src/run_v1.py --ollama                   # same, verdicts on local Ollama qwen3:8b (testing only)
python src/run_v2.py --dry-run --limit 1        # version 2: v1 + the code the found tests call (same options as run_v1)
python src/run_agent.py --case <case_id> --verbose  # version 3: agent with search_tests/grep/read_file, max 10 calls (same options)
python src/run_v1.py --search none --prompt no_retrieval_v1   # no-retrieval baseline: criterion only, no tests
python src/trace.py --repo <github link or folder> --issue <issue link, number or file>   # the end-user tool: report in reports/
```
`covered` = base commit + code fix + its tests; `not_covered` = base commit + code fix only.
Scripts are run from the repo root. `run_v1.py` defaults to the embedding search (`src/search_tests.py`)
and the OpenAI model from `.env`. Fallbacks, each printed as a NOTE: no OpenAI key or a missing index ->
keyword search (`src/search_bm25.py`, later the BM25 baseline); no OpenAI key -> local Ollama
(`qwen3:8b`). `--search search_bm25` and `--ollama [MODEL]` choose them explicitly. Each result row
records the search and model actually used; only OpenAI + embedding-search rows are reportable.
Scoring scripts live in `src/evaluation/` (first drafts; run them from the repo root like the other scripts; they need `pandas` + `matplotlib`, now in `requirements.txt`):
`sanity_check_labels.py` validates `data/labels_dev.jsonl`; `python src/evaluation/evaluate.py results/dev/v3/embedding.jsonl` compares one results file with `data/labels_dev.jsonl` (`--labels` for another key) and writes `<file name>_evaluation_summary.csv` + `<file name>_aggregated_metrics.csv` next to the results file (e.g. `results/dev/v3/`); `plot_metrics.py <aggregate csv>...` draws charts into `results/`.

## JSONL schemas (one JSON object per line)
These schemas are proposed: agree on them as a team before relying on them, and update this file when they change.

`data/cases.jsonl`: one row per (criterion, variant) to judge
```json
{"case_id": "psf__requests-2317__ac1__covered", "instance_id": "psf__requests-2317",
 "variant": "covered", "criterion": "Given ..., when ..., then ...",
 "workspace": "workspace/psf__requests-2317/covered"}
```

`data/labels_dev.jsonl`: answer key, human-written, never shown to the model; one row per case in
`cases.jsonl` (so both copies of every criterion), the fields `evaluate.py` and `sanity_check_labels.py` read
```json
{"case_id": "psf__requests-2317__ac1__covered", "verdict": "covered",
 "tests": ["tests/test_requests.py::test_x"], "note": "test_x asserts the fixed behaviour"}
```
`verdict` is one of `covered | partial | not_covered`; `tests` is `[]` for `not_covered`.

`results/<split>/<round>/<search>.jsonl`: one row per model run on a case
```json
{"case_id": "psf__requests-2317__ac1__covered", "verdict": "covered",
 "reason": "1-2 sentences", "tests_found": ["tests/test_requests.py::test_x"],
 "tests_used": ["tests/test_requests.py::test_x"], "version": "v1", "search": "search_tests",
 "model": "gpt-6-luna", "prompt": "verdict_v1", "tool_calls": 0,
 "tokens_in": 570, "tokens_out": 80, "timestamp": "2026-10-15T12:00:00Z"}
```
`verdict` is one of `covered | partial | not_covered | needs_review`. `tests_found` is what the search
returned (scored for precision/recall); version 2 adds `code_added`, version 3 adds `steps`.

## Conventions
- Commit small and often with clear messages (e.g. "add verdict prompt v2").
- New prompt versions are new files (`verdict_v2.txt`); never edit a version already used in results.
