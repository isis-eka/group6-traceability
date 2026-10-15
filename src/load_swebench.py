"""Download SWE-bench and save the requests and flask issues we use.

Run:    python src/load_swebench.py
Output: data/issues.jsonl  (one issue per line)
"""
import json
from pathlib import Path

from datasets import load_dataset

REPOS = {"psf/requests", "pallets/flask"}

# Columns we keep. hints_text (issue comments) is left out on purpose:
# it can discuss the fix or the tests and give the answer away.
KEEP = [
    "instance_id",
    "repo",
    "base_commit",
    "problem_statement",
    "patch",
    "test_patch",
    "FAIL_TO_PASS",
]


def main():
    data = load_dataset("princeton-nlp/SWE-bench", split="test")
    rows = [row for row in data if row["repo"] in REPOS]

    out = Path("data/issues.jsonl")
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            record = {key: row[key] for key in KEEP}
            # FAIL_TO_PASS is stored as a JSON string; turn it into a real list
            record["FAIL_TO_PASS"] = json.loads(row["FAIL_TO_PASS"])
            f.write(json.dumps(record) + "\n")

    by_repo = {}
    for row in rows:
        by_repo[row["repo"]] = by_repo.get(row["repo"], 0) + 1
    print(f"Saved {len(rows)} issues to {out}: {by_repo}")


if __name__ == "__main__":
    main()
