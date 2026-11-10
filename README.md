# Group 6: AI-Assisted Requirements-to-Test Traceability

A tool that reads a requirement (acceptance criterion) and a project's tests and code, then says whether the requirement is properly tested: **covered**, **partial**, **not covered**, or **needs review**.

We test it on real GitHub issues from the **requests** and **flask** projects, taken from the SWE-bench dataset.

For how the scripts and files fit together, and who owns each step, see the diagrams in [`docs/architecture.md`](docs/architecture.md). Design decisions and why: [`docs/decisions.md`](docs/decisions.md).

## Results at a glance

Four versions, each showing the AI more: **baseline** (criterion only), **V1** (the 3 most similar tests), **V2** (V1 + the code those tests call) and **V3** (an agent that searches and reads the repo itself, read-only, at most 10 tool calls). Prompts were tuned on 10 dev issues with `gpt-6-luna`, frozen on 31 Oct, then run once on 18 unseen test issues with `gpt-6-luna` and with `gpt-6.1-sol` (never tuned on).

| Version | Dev accuracy (28 cases, luna) | Test accuracy (48 cases), luna → sol | Test false all-clear, luna → sol | Test partial right (of 15), luna → sol |
|---|---|---|---|---|
| Baseline | 0.21 | 0.35 → 0.38 | 27 → 21 of 48 | 0 → 0 |
| V1 | 0.50 | 0.63 → 0.60 | 3 → 3 of 48 | 4 → 1 |
| V2 | 0.61 | 0.67 → 0.62 | 3 → 4 of 48 | 4 → 1 |
| V3 agent | 0.75 | 0.58 → 0.60 | 2 → 4 of 48 | 0 → 0 |

- Showing real tests is what matters most: with none, the AI says "covered" almost every time (false all-clear 27 of 48).
- The agent's lead on dev did not hold on the test set, and "partial" (some parts tested, some not) is the weak spot.
- False alarms (saying "not covered" when it is) were rare: 0–3 per run.
- Test recall/precision in the score files are measured on the tests the **search returned** (`tests_found`), not on the tests the AI cited.

Score files: `results/<split>/<round>/*_aggregated_metrics.csv`. Folders `results/dev/*_verdict_v3` and `results/dev/v3_agent_v2` are experiments run **after** the test run (new prompts, dev only), not reported results.

## Try it in 5 minutes: the demo-shop example

[`demo-shop`](https://github.com/isis-eka/demo-shop) is a tiny shopping cart (add items, discount codes, checkout with 9% GST) with 3 user stories, 7 acceptance criteria and 13 passing tests. The code meets every criterion; only the tests differ, so some criteria are fully tested, one partly, and some not at all (including a test that runs but asserts nothing, and one whose name matches but checks something else).

After the [one-time setup](#one-time-setup), clone it **next to** this folder and run the tool on it:

```bash
cd ..
git clone https://github.com/isis-eka/demo-shop.git
cd group6-traceability
python src/trace.py --repo ../demo-shop --criteria ../demo-shop/criteria.txt
```

The report is written to `reports/demo-shop.md` (an existing report is never replaced: the next run gets `_2`, `_3`, ...). The first run embeds demo-shop's 13 test functions (one small embedding call) and caches them in `workspace/_trace/demo-shop__local.index.jsonl`; delete that file after editing demo-shop's tests. To check one criterion only:

```bash
python src/trace.py --repo ../demo-shop --criterion "Given a cart with items, when the shopper checks out, then the receipt total is the subtotal plus 9% GST."
```

### Demo video and sample reports

**Demo video:** [youtu.be/DDAHtk_iD8k](https://youtu.be/DDAHtk_iD8k) shows the tool run on demo-shop and on a real flask issue.

Reports from the runs in the video (all `gpt-6-luna`, prompt `agent_v1`):

| Report | What was checked | Result |
|---|---|---|
| [`reports/demo-shop.md`](reports/demo-shop.md) | demo-shop, all 7 criteria | 3 covered, 1 partial, 3 not covered |
| [`reports/demo-shop_2.md`](reports/demo-shop_2.md) | demo-shop, same criteria, test_add_item() commented out (AC1) | 2 covered, 2 partial, 3 not covered |
| [`reports/pallets__flask__5014.md`](reports/pallets__flask__5014.md) | flask issue 5014 (blueprints need a non-empty name), criterion drafted from the issue text | 1 of 1 covered |

For the second demo-shop run, `test_add_item` was commented out to show the tool reacting to a removed test. Only AC1 changed: with its direct test gone, the tool cited `test_subtotal` (it adds 2 apples but asserts the subtotal, not the quantity) and downgraded AC1 from covered to partial.

## Use the tool on any repo

After the one-time setup below, give it a GitHub repo (or a local folder) and an issue:

```bash
python src/trace.py --repo https://github.com/pallets/flask --issue https://github.com/pallets/flask/issues/5014
python src/trace.py --repo https://github.com/pallets/flask --issue 5014                 # issue number in that repo
python src/trace.py --repo ../myproject --issue story.txt                               # local folder, issue as text
python src/trace.py --repo ../myproject --criterion "Given ..., when ..., then ..."     # your own criteria (repeatable)
```

It drafts acceptance criteria from the issue text (unless you give them), lets the agent check
each one against the repo's tests and code (read-only, at most 10 tool calls each), and writes a
traceability report to `reports/<repo>__<issue>.md` (never replaced: a rerun saves
`..._2.md`, `..._3.md`, ...). It uses the agent prompt `prompts/agent_v1.txt`, the one evaluated (`--prompt` picks
another). The report gives each criterion's verdict, the tests cited
and why, a summary such as "2 of 3 covered, 1 partial", and a fixed next-step line for each
verdict. GitHub repos are cloned into `workspace/_trace/`. If the issue is too vague to draft a
testable criterion, it stops and asks for `--criterion` instead of guessing. Other options:
`--criteria <file>` (one criterion per line), `--ref <branch or tag>`, `--out <file>`, `--ollama`
(local model, no OpenAI key). The verdicts are the AI's judgment: check them before acting.

## Folders

| Folder | What goes here | Who mainly works here |
|---|---|---|
| `prompts/` | Instructions we send to the AI (plain text) | Sammi |
| `data/` | `issues.jsonl` (all 55 SWE-bench issues) and `issue_text.jsonl` (their text only): **not uploaded**, rebuilt by scripts. `chosen_issues.json` (every issue we use, each marked `"split": "dev"` (10) or `"test"` (18)), `issue_text_v1.jsonl` / `issue_text_test.jsonl` (issue text only, for drafting criteria), `criteria_test_draft.jsonl` (the 22 reviewed test-set criteria), `cases.jsonl` (dev: 12 criteria → 28 cases) and `cases_test.jsonl` (test: 22 criteria → 48 cases), one row per criterion and code copy. **Not uploaded**, shared privately: the answer keys `labels_dev.jsonl` and `labels_test.jsonl`, and `partial_drops.jsonl` (which checks each partial copy removes). `index_v1/` (test search index: **not uploaded**, rebuilt by `build_index.py`) | Isis Eka, Xiaoning |
| `src/` | Python scripts | Gabriel, Isis Eka |
| `results/` | One folder per round of runs: `dev/<round>/` (tuning on the dev issues) and `test/<round>/` (the reported results; `_sol` = `gpt-6.1-sol`). Each holds the AI's answers per search and their scores | Xiaoning, Gabriel |
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
| 2 | `python src/prepare_repo.py <instance_id>` | Builds the **covered** and **not covered** versions of the code for one issue in `workspace/`, with no git history (it holds the real fix). `--all` does every dev issue, `--test` every test-set issue (by `split` in `chosen_issues.json`), `--partial` the **partial** copies (covered minus the checks in `data/partial_drops.jsonl`) |
| 2b | `python src/make_cases.py --criteria data/criteria_test_draft.jsonl --out data/cases_test.jsonl` | Turns reviewed criteria into cases: one row per criterion and code copy that exists. Never reads an answer key |
| 3 | `python src/export_issue_text.py` | Writes `data/issue_text.jsonl` with only `instance_id` and `problem_statement`, for all 55 issues. The acceptance criteria owner works only from issue-text files like this (for version 1: `issue_text_v1.jsonl`; for the test set: `issue_text_test.jsonl`, made with `--split test --out data/issue_text_test.jsonl`), never from `issues.jsonl` |
| 4 | `python src/build_index.py` | Splits each covered/not_covered copy's test files into one chunk per test function and embeds them into `data/index_v1/`. Run `--dry-run` first: it only writes the chunks to `workspace/_chunks/`, free. `--only <instance_id>` does one issue, `--test` the test set |
| 5 | `python src/search_tests.py <instance_id> <covered\|not_covered> "<query>"` | Prints the 3 test functions most similar to the query, with scores |
| 6 | `python src/run_v1.py` | Version 1: for each case in `data/cases.jsonl`, finds the 3 most similar tests and asks the AI once. Saves verdicts to `results/results.jsonl`. Add `--dry-run --limit 1` to see the prompt without calling the AI, or `--ollama` to test on a local Ollama model (qwen3:8b) instead of OpenAI |
| 6b | `python src/run_v2.py` | Version 2: the same as step 6, plus the code the 3 tests call. It finds the functions and classes each test calls in the project's own source (not tests, docs or vendored copies), one level deep, and adds them under the tests in the prompt (at most 250 lines). Takes the same options as `run_v1.py`; each result row also lists `code_added` |
| 6c | `python src/run_agent.py` | Version 3, the agent: instead of a fixed 3 tests, the AI uses three read-only tools (`search_tests`, `grep`, `read_file`) to look where it chooses, at most 10 calls per case, never outside the case's folder or inside `.git`. Same options as `run_v1.py`, plus `--verbose` to print each tool call; each result row also lists its `steps` |
| 6d | `python src/run_v1.py --search none --prompt no_retrieval_v1` | No-retrieval baseline: the AI sees only the criterion, no tests or code, and must guess. Checks that versions 1-3 gain from what they are shown, and whether the model has memorised these projects |
| 7 | `python src/evaluation/evaluate.py results/dev/v1/embedding.jsonl` | Scores one run against the answer key (`data/labels_dev.jsonl`; `--labels data/labels_test.jsonl` for the test set). Writes `embedding_evaluation_summary.csv` (one row per case; git-ignored, it lists the answer key) and `embedding_aggregated_metrics.csv` (accuracy, false alarm and false all-clear rates, and recall/precision of the tests the search returned) next to it |
| 8 | `python src/evaluation/plot_metrics.py results/dev/v1/embedding_aggregated_metrics.csv results/dev/v1/bm25_aggregated_metrics.csv` | Draws `accuracy.png` and `prf.png` into the same folder, with the runs side by side |

Example: `python src/prepare_repo.py psf__requests-2317`

`run_v1.py` uses the embedding search from step 5 and the OpenAI model by default. Without an OpenAI key it falls back to keyword search (`src/search_bm25.py`) and a local Ollama model, and it uses keyword search for issues with no index yet. It prints a NOTE whenever it falls back, and each result records what was used. Use `--search search_bm25` or `--ollama` to choose these on purpose.

**Where results go:** `results/<split>/<round>/<search>.jsonl`. The split is `dev` (the issues we tune on) or `test` (one final run, the reported results). The round is named after the version (`v1`, `v2`, `v3`, `no_retrieval`), with a short suffix for a variation (`v1_k5` = top 5 tests, `_sol` = `gpt-6.1-sol`). The file is named after the search (`embedding`, `bm25`, `none`); `partial_<search>.jsonl` holds the runs on the partial copies. Pass it with `--out`:
`python src/run_v1.py --search search_bm25 --out results/dev/v1/bm25.jsonl`. Scores are saved in the same folder.

**Models:** `gpt-6-luna` for all development and tuning (set `OPENAI_MODEL` in `.env` to change it), `gpt-6.1-sol` for the one final test-set run only, `text-embedding-3-small` for the test search, and `qwen3:8b` on Ollama as an offline fallback (testing only, not evaluated).

## Dev set

The dev (development) set is the practice round: the issues we used to build and tune the tool. It has **10 issues** (9 from `psf/requests`, 1 from `pallets/flask`), listed in `data/chosen_issues.json` as `"split": "dev"`. Each criterion is judged on a covered and a not_covered copy, and four also on a hand-built partial copy: 12 criteria, so 28 cases. We tried prompts and settings on these (for example embedding search vs BM25, 3 vs 5 tests), then froze the prompts on 31 Oct. Because we tuned on them, dev scores run high; the reported results come from the test set below.

## Test set

`python src/pick_test_set.py` adds the test set to `data/chosen_issues.json` as `"split": "test"` rows: every issue not in the dev set that passes the same check the dev issues did (every test in SWE-bench's `FAIL_TO_PASS` list appears in the fix's test patch). That is **18 issues**: 10 from `pallets/flask`, 8 from `psf/requests`. The other 27 list unrelated tests that fail for environment reasons, which would put wrong tests in the answer key. Nobody tunes on these issues, and their results are only looked at in the final runs.

## Test IDs

Every file names a test the same way, as a pytest id copied exactly from SWE-bench's `FAIL_TO_PASS`: `file::Class::test_name`, or `file::test_name` for a test outside a class. Examples:
- `tests/test_requests.py::TestRequests::test_binary_put`
- `tests/test_packages.py::test_can_access_idna_attribute`

The answer keys, the search index and the results files all use this format, so labels and search results can be compared directly.

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
