"""Turn reviewed acceptance criteria into cases: one per (criterion, copy of the code).

Run:    python src/make_cases.py --criteria data/criteria_test_draft.jsonl --out data/cases_test.jsonl
Needs:  the criteria file (instance_id, ac_id, criterion, reviewed) and the copies from
        src/prepare_repo.py. Every copy that exists for an issue becomes a case: covered and
        not_covered always, partial once src/prepare_repo.py --partial has built it.
Output: one row per case, same fields as data/cases.jsonl. Criteria not marked reviewed are
        skipped with a NOTE. Never reads any answer key.
"""
import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path("workspace")
VARIANTS = ["covered", "not_covered", "partial"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--criteria", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    criteria = [json.loads(line) for line in open(args.criteria, encoding="utf-8") if line.strip()]
    cases, missing = [], []
    for c in criteria:
        if not c.get("reviewed"):
            print(f"NOTE: {c['instance_id']} {c['ac_id']} is not reviewed, skipped")
            continue
        variants = [v for v in VARIANTS if (WORKSPACE / c["instance_id"] / v).is_dir()]
        for v in ("covered", "not_covered"):
            if v not in variants:
                missing.append(f"workspace/{c['instance_id']}/{v}")
        for v in variants:
            cases.append({"case_id": f"{c['instance_id']}__{c['ac_id']}__{v}",
                          "instance_id": c["instance_id"], "variant": v, "criterion": c["criterion"],
                          "workspace": f"workspace/{c['instance_id']}/{v}", "reviewed": True})
    if missing:
        sys.exit("Missing copies (run src/prepare_repo.py first):\n  " + "\n  ".join(sorted(set(missing))))

    with open(args.out, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")
    counts = {v: sum(case["variant"] == v for case in cases) for v in VARIANTS}
    print(f"{len(cases)} cases -> {args.out} ({', '.join(f'{n} {v}' for v, n in counts.items())})")


if __name__ == "__main__":
    main()
