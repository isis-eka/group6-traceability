"""Save the issue text only, for drafting acceptance criteria.

Run:    python src/export_issue_text.py
        python src/export_issue_text.py --split test --out data/issue_text_test.jsonl
Needs:  data/issues.jsonl (run src/load_swebench.py first)
Output: data/issue_text.jsonl  (instance_id + problem_statement, one issue per line)
        --split keeps only that split's issues from data/chosen_issues.json, in its order

This is the only file the acceptance criteria owner works from. It must never
contain patch, test_patch, FAIL_TO_PASS or hints: they give the answer away.
"""
import argparse
import json
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
CHOSEN = Path("data/chosen_issues.json")
OUT = Path("data/issue_text.jsonl")

# Allow-list, not a block-list: any new column added to issues.jsonl stays out.
KEEP = ["instance_id", "problem_statement"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["dev", "test"], help="export only this split of data/chosen_issues.json")
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()

    with ISSUES.open(encoding="utf-8") as f:
        rows = [{key: issue[key] for key in KEEP} for issue in map(json.loads, f)]
    if args.split:
        chosen = json.loads(CHOSEN.read_text(encoding="utf-8"))
        wanted = [r["instance_id"] for r in chosen if r["split"] == args.split]
        by_id = {r["instance_id"]: r for r in rows}
        missing = [i for i in wanted if i not in by_id]
        if missing:
            raise SystemExit(f"Not in {ISSUES}: {', '.join(missing)}")
        rows = [by_id[i] for i in wanted]
    with args.out.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row) + "\n")
    print(f"Saved {len(rows)} issues to {args.out}")


if __name__ == "__main__":
    main()
