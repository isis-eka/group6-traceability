# Group 6: AI-Assisted Requirements-to-Test Traceability

A tool that reads a requirement (acceptance criterion) and a project's tests and code, then says whether the requirement is properly tested: **covered**, **partial**, **not covered**, or **needs review**.

We test it on real GitHub issues from the **requests** and **flask** projects, taken from the SWE-bench dataset.

For how the scripts and files fit together, and who owns each step, see the diagrams in [`docs/architecture.md`](docs/architecture.md).

## Folders

| Folder | What goes here | Who mainly works here |
|---|---|---|
| `prompts/` | Instructions we send to the AI (plain text) | Sammi |
| `data/` | `issues.jsonl` (all 55 SWE-bench issues) and `issue_text.jsonl` (their text only): **not uploaded**, rebuilt by scripts. Version 1: `chosen_issues.json` (the 10 dev issues), `issue_text_v1.jsonl` (their text, for drafting criteria), `labels_v1.jsonl` (answer key: **not uploaded**, shared privately), `index_v1/` (test search index: **not uploaded**, rebuilt by `build_index.py`). Later: `cases.jsonl`, `labels.jsonl` | Isis Eka, Xiaoning |
| `src/` | Python scripts | Gabriel, Isis Eka |
| `results/` | `results.jsonl`, score tables, charts | Xiaoning |
| `workspace/` | Downloaded copies of requests/flask. **Not uploaded to GitHub** | (created by scripts) |
| `docs/` | `architecture.md` (pipeline and data model diagrams), `decisions.md` (design decisions and why) | Everyone |
| `ai-log/` | One AI use log per member (`isis-eka.md`, ...). Start from `your-name.md` | Everyone |

## One-time setup

1. Install Python 3.10 or newer.
2. In this folder, create a virtual environment (a private copy of Python for this project) and install the packages:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   On Windows, use `python` instead of `python3`, and `.venv\Scripts\activate` instead of the `source` line.

   **Each time you open a new terminal**, run `source .venv/bin/activate` again before any `python` command. If you see `python: command not found`, this is why.
3. Copy `.env.example` to a new file called `.env` and paste the OpenAI API key into it.
   **Never upload `.env` to GitHub.** It is already listed in `.gitignore`.
4. Turn on the AI disclosure check (Claude Code does this for you automatically):
   ```bash
   git config core.hooksPath .githooks
   ```

## Scripts

| Step | Command | What it does |
|---|---|---|
| 1 | `python src/load_swebench.py` | Downloads SWE-bench and saves the requests + flask issues to `data/issues.jsonl` |
| 2 | `python src/prepare_repo.py <instance_id>` | Builds the **covered** and **not covered** versions of the code for one issue in `workspace/` |
| 3 | `python src/export_issue_text.py` | Writes `data/issue_text.jsonl` with only `instance_id` and `problem_statement`, for all 55 issues. The acceptance criteria owner works only from issue-text files like this (for version 1: `issue_text_v1.jsonl`), never from `issues.jsonl` |
| 4 | `python src/build_index.py` | Splits each covered/not_covered copy's test files into one chunk per test function and embeds them into `data/index_v1/`. Run `--dry-run` first: it only writes the chunks to `workspace/_chunks/`, free. `--only <instance_id>` does one issue |
| 5 | `python src/search_tests.py <instance_id> <covered\|not_covered> "<query>"` | Prints the 3 test functions most similar to the query, with scores |
| 6 | `python src/run_v1.py` | Version 1: for each case in `data/cases.jsonl`, finds the 3 most similar tests and asks the AI once. Saves verdicts to `results/results.jsonl`. Add `--dry-run --limit 1` to see the prompt without calling the AI, or `--ollama` to test on a local Ollama model (qwen3:8b) instead of OpenAI |
| 7 | `python src/evaluation/evaluate.py results/<run>.jsonl` | Scores one run against the answer key (`data/labels_v1.jsonl`). Writes `results/<run>_summary.csv` (one row per case) and `results/<run>_metrics.csv` (accuracy, false alarm and false all-clear rates, test precision/recall) |
| 8 | `python src/evaluation/plot_metrics.py results/<run>_metrics.csv [...]` | Draws charts into `results/`. Give several `_metrics.csv` files to compare runs side by side |

Example: `python src/prepare_repo.py psf__requests-2317`

`run_v1.py` uses the embedding search from step 5 and the OpenAI model by default. Without an OpenAI key it falls back to keyword search (`src/search_bm25.py`) and a local Ollama model, and it uses keyword search for issues with no index yet. It prints a NOTE whenever it falls back, and each result records what was used. Use `--search search_bm25` or `--ollama` to choose these on purpose.

**Results file names:** `results/<version>_<run>_<search>.jsonl`, e.g. `v1_mock_embedding.jsonl` and `v1_mock_bm25.jsonl` (a trial run), later `v1_dev_embedding.jsonl` (the official dev-set run). Pass the name with `--out`:
`python src/run_v1.py --search search_bm25 --out results/v1_mock_bm25.jsonl`. Scores and charts are named after the run.

## Version 1 dev set

Version 1 runs on **10 dev issues**: 9 from `psf/requests` and 1 from `pallets/flask`, listed in `data/chosen_issues.json`. Each has a covered and a not_covered copy, so that's 20 cases. We tune prompts on these, then freeze them. The reported results come from a separate test set of new issues.

## Test IDs

Every file names a test the same way, as a pytest id copied exactly from SWE-bench's `FAIL_TO_PASS`: `file::Class::test_name`, or `file::test_name` for a test outside a class. Examples:
- `tests/test_requests.py::TestRequests::test_binary_put`
- `tests/test_packages.py::test_can_access_idna_attribute`

`data/labels_v1.jsonl`, the search index and `results.jsonl` all use this format, so labels and search results can be compared directly.

**Parametrized tests** keep their `[...]` part in the labels, e.g. `tests/test_requests.py::TestRequests::test_invalid_url[InvalidURL-http://.example.com]`. Search and scoring match at the **function level** and ignore the `[...]` part, because one search chunk is the whole test function, with all its inputs.

## Rules

- Draft acceptance criteria from the issue text only. Never look at the tests or the fix while writing or reviewing them.
- The answer key (`labels*.jsonl`) is never sent to the AI and never committed: git ignores it. It's shared privately with the answer key and scoring owners (Xiaoning, Gabriel), never with the acceptance criteria owner.
- Commit small and often, with a clear message (e.g. "add verdict prompt v2").

## AI use disclosure (SE201 policy)

Any commit with AI-assisted work (code, tests, docs, prompts, data) needs both:

1. A trailer line in the commit message: `Assisted-by: <tool> (<model>)`, e.g. `Assisted-by: ChatGPT (GPT-5)`. A tool's own `Co-Authored-By:` line also counts.
2. An entry in `ai-log/<your-name>.md`, committed with the same work. Copy `ai-log/your-name.md` to start. The key part is **How I checked it**. Agents leave it and **What I kept or changed** as `[to fill by <name>]`, and you write both yourself. `python tools/ai_disclosure.py summary` lists entries still to fill.

The git hook blocks commits that have the trailer but no log entry, and GitHub Actions re-checks every push.
`python tools/ai_disclosure.py check-logs` checks your log's format. `python tools/ai_disclosure.py summary` lists the tools used, for the team declaration.
