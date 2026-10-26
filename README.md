# Group 6: AI-Assisted Requirements-to-Test Traceability

A tool that reads a requirement (acceptance criterion) and a project's tests and code, then says whether the requirement is properly tested: **covered**, **partial**, **not covered**, or **needs review**.

We test it on real GitHub issues from the **requests** and **flask** projects, taken from the SWE-bench dataset.

For how the scripts and files fit together, and who owns each step, see the diagrams in [`docs/architecture.md`](docs/architecture.md).

## Folders

| Folder | What goes here | Who mainly works here |
|---|---|---|
| `prompts/` | Instructions we send to the AI (plain text) | Sammi |
| `data/` | `issues.jsonl` (all 55 SWE-bench issues) and `issue_text.jsonl` (their text only): **not uploaded**, rebuilt by scripts. `chosen_issues.json` (every issue we use, each marked `"split": "dev"` (10) or `"test"` (18)), `issue_text_v1.jsonl` (their text, for drafting criteria), `labels_v1.jsonl` (answer key: **not uploaded**, shared privately), `index_v1/` (test search index: **not uploaded**, rebuilt by `build_index.py`). Test set: `issue_text_test.jsonl` (their text, for drafting criteria). Later: `cases.jsonl`, `labels.jsonl` | Isis Eka, Xiaoning |
| `src/` | Python scripts | Gabriel, Isis Eka |
| `results/` | One folder per round of runs: `dev/<round>/` (tuning on the dev issues) and later `test/final/` (the reported results). Each holds the AI's answers per search, scores, charts and a `README.md` write-up | Xiaoning, Gabriel |
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
| 2 | `python src/prepare_repo.py <instance_id>` | Builds the **covered** and **not covered** versions of the code for one issue in `workspace/`. `--all` does every dev issue, `--test` every test-set issue (by `split` in `chosen_issues.json`) |
| 3 | `python src/export_issue_text.py` | Writes `data/issue_text.jsonl` with only `instance_id` and `problem_statement`, for all 55 issues. The acceptance criteria owner works only from issue-text files like this (for version 1: `issue_text_v1.jsonl`; for the test set: `issue_text_test.jsonl`, made with `--split test --out data/issue_text_test.jsonl`), never from `issues.jsonl` |
| 4 | `python src/build_index.py` | Splits each covered/not_covered copy's test files into one chunk per test function and embeds them into `data/index_v1/`. Run `--dry-run` first: it only writes the chunks to `workspace/_chunks/`, free. `--only <instance_id>` does one issue, `--test` the test set |
| 5 | `python src/search_tests.py <instance_id> <covered\|not_covered> "<query>"` | Prints the 3 test functions most similar to the query, with scores |
| 6 | `python src/run_v1.py` | Version 1: for each case in `data/cases.jsonl`, finds the 3 most similar tests and asks the AI once. Saves verdicts to `results/results.jsonl`. Add `--dry-run --limit 1` to see the prompt without calling the AI, or `--ollama` to test on a local Ollama model (qwen3:8b) instead of OpenAI |
| 6b | `python src/run_v2.py` | Version 2: the same as step 6, plus the code the 3 tests call. It finds the functions and classes each test calls in the project's own source (not tests, docs or vendored copies), one level deep, and adds them under the tests in the prompt (at most 250 lines). Takes the same options as `run_v1.py`; each result row also lists `code_added` |
| 7 | `python src/evaluation/evaluate.py results/dev/v1/embedding.jsonl` | Scores one run against the answer key (`data/labels_v1.jsonl`). Writes `embedding_summary.csv` (one row per case; git-ignored, it lists the answer key tests) and `embedding_metrics.csv` (accuracy, false alarm and false all-clear rates, test precision/recall) next to it |
| 8 | `python src/evaluation/plot_metrics.py results/dev/v1/embedding_metrics.csv results/dev/v1/bm25_metrics.csv` | Draws `accuracy.png` and `prf.png` into the same folder, with the runs side by side |

Example: `python src/prepare_repo.py psf__requests-2317`

`run_v1.py` uses the embedding search from step 5 and the OpenAI model by default. Without an OpenAI key it falls back to keyword search (`src/search_bm25.py`) and a local Ollama model, and it uses keyword search for issues with no index yet. It prints a NOTE whenever it falls back, and each result records what was used. Use `--search search_bm25` or `--ollama` to choose these on purpose.

**Where results go:** `results/<split>/<round>/<search>.jsonl`. The split is `dev` (the issues we tune on) or `test` (one final run, the reported results). The round is named after the prompt version (`v1`, `v2`), with a short suffix for a variation (`v1_partial`). The file is named after the search (`embedding`, `bm25`). Pass it with `--out`:
`python src/run_v1.py --search search_bm25 --out results/dev/v1/bm25.jsonl`. Scores and charts are saved in the same folder, and each round gets a `README.md` saying what was run, the results, failures and next steps (written by hand).

## Demo: version 1 on one requirement

`src/demo.py` runs version 1 on one case and shows each step, waiting for Enter between them:

1. the acceptance criterion
2. the 3 tests the search finds, with their similarity score and code
3. the AI's verdict, its reason and the tests it relied on (one real call, a fraction of a US cent)
4. the right answer from the answer key, and whether the AI got it right

It uses `run_v1.py`'s own search, prompt and model, so it gives the same answers as a real run. It saves nothing. The answer key is opened only in step 4, after the AI has answered.

After the one-time setup:
```bash
source .venv/bin/activate
python src/load_swebench.py                          # once: downloads the issues
python src/prepare_repo.py psf__requests-5414          # the code copies for this issue
python src/build_index.py --only psf__requests-5414    # its search index
python src/demo.py psf__requests-5414__ac1__not_covered
```
- `python src/demo.py --list` shows every case id. Each criterion has a `covered` case (its tests are in the code) and a `not_covered` case (they were removed).
- `--no-pause` prints all 4 steps at once.
- Step 4 needs `data/labels_v1.jsonl`, which is shared privately, not on GitHub. Without it, steps 1–3 still run and step 4 says so.
- Good cases to try: `psf__requests-5414__ac1__not_covered` (a look-alike test exists, but the AI correctly says not covered) and the `psf__requests-1142__ac1__covered` / `__not_covered` pair (same requirement, with and without its test).

## Version 1 dev set

Version 1 runs on **10 dev issues**: 9 from `psf/requests` and 1 from `pallets/flask`, listed in `data/chosen_issues.json`. Each criterion is judged on a covered and a not_covered copy: 12 criteria, so 24 cases. We tune prompts on these, then freeze them. The reported results come from a separate test set of new issues.

## Test set

`python src/pick_test_set.py` adds the test set to `data/chosen_issues.json` as `"split": "test"` rows: every issue not in the dev set that passes the same check the dev issues did (every test in SWE-bench's `FAIL_TO_PASS` list appears in the fix's test patch). That is **18 issues**: 10 from `pallets/flask`, 8 from `psf/requests`. The other 27 list unrelated tests that fail for environment reasons, which would put wrong tests in the answer key. Nobody tunes on these issues, and their results are only looked at in the final runs.

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
