# Group 6: AI-Assisted Requirements-to-Test Traceability

A tool that reads a requirement (acceptance criterion) and a project's tests and code, then says whether the requirement is properly tested: **covered**, **partial**, **not covered**, or **needs review**.

We test it on real GitHub issues from the **requests** and **flask** projects, taken from the SWE-bench dataset.

## Folders

| Folder | What goes here | Who mainly works here |
|---|---|---|
| `prompts/` | Instructions we send to the AI (plain text) | Sammi |
| `data/` | `issues.jsonl` (SWE-bench issues), `issue_text.jsonl` (issue text only), `cases.jsonl`, `labels.jsonl` | Isis Eka, Xiaoning |
| `src/` | Python scripts | Gabriel, Isis Eka |
| `results/` | `results.jsonl`, score tables, charts | Xiaoning |
| `workspace/` | Downloaded copies of requests/flask. **Not uploaded to GitHub** | (created by scripts) |
| `ai-log/` | One AI use log per member (`isis-eka.md`, ...). Start from `your-name.md` | Everyone |

## One-time setup

1. Install Python 3.10 or newer.
2. In this folder, run:
   ```bash
   pip install -r requirements.txt
   ```
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
| 3 | `python src/export_issue_text.py` | Writes `data/issue_text.jsonl` with only `instance_id` and `problem_statement`. This is the only file the acceptance criteria owner works from |
| 4 | `python src/build_index.py` | Splits each covered/not_covered copy's test files into one chunk per test function and embeds them into `data/index_v1/`. Run `--dry-run` first: it only writes the chunks to `workspace/_chunks/`, free. `--only <instance_id>` does one issue |
| 5 | `python src/search_tests.py <instance_id> <covered\|not_covered> "<query>"` | Prints the 3 test functions most similar to the query, with scores |

Example: `python src/prepare_repo.py psf__requests-2317`

More scripts (version 1, scoring) will be added in `src/`.

## Test IDs

Every file names a test the same way, as a pytest id copied exactly from SWE-bench's `FAIL_TO_PASS`: `file::Class::test_name`, or `file::test_name` for a test outside a class. Examples:
- `tests/test_requests.py::TestRequests::test_binary_put`
- `tests/test_packages.py::test_can_access_idna_attribute`

`data/labels_v1.jsonl`, the search index and `results.jsonl` all use this format, so labels and search results can be compared directly.

**Parametrized tests** keep their `[...]` part in the labels, e.g. `tests/test_requests.py::TestRequests::test_invalid_url[InvalidURL-http://.example.com]`. Search and scoring match at the **function level** and ignore the `[...]` part, because one search chunk is the whole test function, with all its inputs.

## Rules

- Draft acceptance criteria from the issue text only. Never look at the tests or the fix while writing or reviewing them.
- `labels.jsonl` (the answer key) is never sent to the AI.
- Commit small and often, with a clear message (e.g. "add verdict prompt v2").

## AI use disclosure (SE201 policy)

Any commit with AI-assisted work (code, tests, docs, prompts, data) needs both:

1. A trailer line in the commit message: `Assisted-by: <tool> (<model>)`, e.g. `Assisted-by: ChatGPT (GPT-5)`. A tool's own `Co-Authored-By:` line also counts.
2. An entry in `ai-log/<your-name>.md`, committed with the same work. Copy `ai-log/your-name.md` to start. The key part is **How I checked it**. Agents leave it and **What I kept or changed** as `[to fill by <name>]`, and you write both yourself. `python tools/ai_disclosure.py summary` lists entries still to fill.

The git hook blocks commits that have the trailer but no log entry, and GitHub Actions re-checks every push.
`python tools/ai_disclosure.py check-logs` checks your log's format. `python tools/ai_disclosure.py summary` lists the tools used, for the team declaration.
