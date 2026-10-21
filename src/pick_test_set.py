"""Pick the test-set issues: every issue not in the dev set that passes the dev set's check.

Run:    python src/pick_test_set.py
Needs:  data/issues.jsonl (run src/load_swebench.py first), data/chosen_issues.json (the dev set)
Output: data/chosen_issues.json, with the test issues added as {"instance_id", "split": "test"}
        after the dev rows (earlier test rows are replaced, dev rows are kept as they are)

The check: every test in SWE-bench's FAIL_TO_PASS list must appear in the fix's test patch.
Older requests issues often also list unrelated tests that fail for environment reasons, which
would put wrong tests in the answer key. Every issue that passes is kept, so there is no
random pick. It reads FAIL_TO_PASS and test_patch only to check them, and writes ids only.
"""
import json
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
CHOSEN = Path("data/chosen_issues.json")


def function_name(test_id):
    """tests/test_requests.py::TestRequests::test_x[param] -> test_x"""
    return test_id.split("::")[-1].split("[")[0]


def fix_tests_only(issue):
    tests = issue["FAIL_TO_PASS"]
    if isinstance(tests, str):
        tests = json.loads(tests)
    return all(function_name(t) in issue["test_patch"] for t in tests)


def main():
    dev_rows = [r for r in json.loads(CHOSEN.read_text(encoding="utf-8")) if r["split"] == "dev"]
    dev = {r["instance_id"] for r in dev_rows}
    picked, skipped = [], 0
    with ISSUES.open(encoding="utf-8") as f:
        for line in f:
            issue = json.loads(line)
            if issue["instance_id"] in dev:
                continue
            if fix_tests_only(issue):
                picked.append(issue["instance_id"])
            else:
                skipped += 1
    rows = dev_rows + [{"instance_id": i, "split": "test"} for i in sorted(picked)]
    CHOSEN.write_text("[\n" + ",\n".join("  " + json.dumps(r) for r in rows) + "\n]\n", encoding="utf-8")
    print(f"Saved {len(picked)} test-set issues to {CHOSEN} ({skipped} skipped: unrelated tests in FAIL_TO_PASS)")


if __name__ == "__main__":
    main()
