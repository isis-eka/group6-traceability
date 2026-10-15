"""Save the issue text only, for drafting acceptance criteria.

Run:    python src/export_issue_text.py
Needs:  data/issues.jsonl (run src/load_swebench.py first)
Output: data/issue_text.jsonl  (instance_id + problem_statement, one issue per line)

This is the only file the acceptance criteria owner works from. It must never
contain patch, test_patch, FAIL_TO_PASS or hints: they give the answer away.
"""
import json
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
OUT = Path("data/issue_text.jsonl")

# Allow-list, not a block-list: any new column added to issues.jsonl stays out.
KEEP = ["instance_id", "problem_statement"]


def main():
    count = 0
    with ISSUES.open(encoding="utf-8") as f, OUT.open("w", encoding="utf-8") as out:
        for line in f:
            issue = json.loads(line)
            out.write(json.dumps({key: issue[key] for key in KEEP}) + "\n")
            count += 1
    print(f"Saved {count} issues to {OUT}")


if __name__ == "__main__":
    main()
