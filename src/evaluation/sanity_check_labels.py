
import json
from collections import Counter

# Read the JSONL file
def load_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return records


# Check the ground-truth labels
def sanity_check_labels(labels_path):
    labels = load_jsonl(labels_path)

    case_ids = []
    errors = []
    verdict_counter = Counter()

    for idx, item in enumerate(labels):

        # Check required keys first
        required_keys = ["case_id", "verdict", "tests"]

        missing_keys = []

        for key in required_keys:
            if key not in item:
                missing_keys.append(key)

        if missing_keys:
            errors.append(
                f"Line {idx + 1}: missing keys {missing_keys}"
            )
            continue

        cid = item["case_id"]
        verdict = item["verdict"]
        tests = item["tests"]

        # Check data types
        if not isinstance(cid, str) or not isinstance(verdict, str):
            errors.append(f"Line {idx + 1}: case_id and verdict must be strings")
            continue

        if not isinstance(tests, list):
            errors.append(f"{cid}: tests must be a list")
            continue

        case_ids.append(cid)
        verdict_counter[verdict] += 1

        # Check valid verdicts
        if verdict not in ["covered", "not_covered", "partial"]:
            errors.append(f"{cid}: invalid verdict '{verdict}'")
            continue

        # Check verdict and tests consistency
        if verdict == "covered" and len(tests) == 0:
            errors.append(f"{cid}: covered but no tests are listed")

        if verdict == "not_covered" and len(tests) > 0:
            errors.append(f"{cid}: not_covered but tests are listed")

        if verdict == "partial" and len(tests) == 0:
            errors.append(f"{cid}: partial but no relevant tests are listed")

    # Check duplicate case IDs
    duplicates = [
        cid for cid, count in Counter(case_ids).items()
        if count > 1
    ]

    if duplicates:
        errors.append(f"Duplicate case_ids found: {duplicates}")

    # Print report
    print("=== LABEL SANITY CHECK REPORT ===")
    print(f"Total label entries: {len(labels)}")
    print(f"Verdict counts: {dict(verdict_counter)}")

    if errors:
        print("\nERRORS FOUND:")

        for error in errors:
            print("-", error)

    else:
        print("\nNo errors found in the ground-truth labels!")


if __name__ == "__main__":
    sanity_check_labels("data/labels_dev.jsonl")
