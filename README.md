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

## One-time setup

1. Install Python 3.10 or newer.
2. In this folder, run:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to a new file called `.env` and paste the OpenAI API key into it.
   **Never upload `.env` to GitHub.** It is already listed in `.gitignore`.

## Scripts

| Step | Command | What it does |
|---|---|---|
| 1 | `python src/load_swebench.py` | Downloads SWE-bench and saves the requests + flask issues to `data/issues.jsonl` |
| 2 | `python src/prepare_repo.py <instance_id>` | Builds the **covered** and **not covered** versions of the code for one issue in `workspace/` |
| 3 | `python src/export_issue_text.py` | Writes `data/issue_text.jsonl` with only `instance_id` and `problem_statement`. This is the only file the acceptance criteria owner works from |

Example: `python src/prepare_repo.py psf__requests-2317`

More scripts (search index, version 1, scoring) will be added in `src/`.

## Rules

- Draft acceptance criteria from the issue text only. Never look at the tests or the fix while writing or reviewing them.
- `labels.jsonl` (the answer key) is never sent to the AI.
- Commit small and often, with a clear message (e.g. "add verdict prompt v2").
