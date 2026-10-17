# to make sure that there are no mistakes before running the evaluation scrpit 
# checks for missing keys, rule validation and any duplicattions 

import json
from collections import Counter 

# read the file, converts each line into dictionary 
def load_jsonl(path):
    recs = []
    with open(path, "r", encoding = "utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            recs.append(json.loads(line))
    return recs

# validation for ground truth labels
# checks: every entry has required keys (case_id, verdict, tests), verdict and tests are logically consistent, no duplicate case_ids
def sanity_check_labels(labels_path):
    labels = load_jsonl(labels_path)
    case_ids = []
    errors = []
    verdict_counter = Counter()

# loop through every ground truth entry to run checks 
    for idx, item in enumerate(labels):
        # Check required keys
        for required_key in ["case_id", "verdict", "tests"]:
            if required_key not in item:
                errors.append(f"Line {idx}: missing key '{required_key}'")

        cid = item["case_id"]
        case_ids.append(cid)
        v = item["verdict"]
        verdict_counter[v] += 1
        tests = item["tests"]

        # Validate verdict and tests consistency
        if v == "covered" and len(tests) == 0:
            errors.append(f"{cid}: verdict=covered but tests list is empty!")
        if v == "not_covered" and len(tests) > 0:
            errors.append(f"{cid}: verdict=not_covered but tests are present!")

    # Check duplicate case_id
    dupes = [cid for cid, count in Counter(case_ids).items() if count > 1]
    if dupes:
        errors.append(f"Duplicate case_ids found: {dupes}")

    #print report
    print("=== LABEL SANITY CHECK REPORT ===")
    print(f"Total label entries: {len(labels)}")
    print(f"Verdict counts: {dict(verdict_counter)}")
    if errors:
        print("\n❌ ERRORS FOUND:")
        for err in errors:
            print("-", err)
    else:
        print("\n✅ No errors found in labels_v1.jsonl")

# to run this check every time the file is executed 
if __name__ == "__main__":
    sanity_check_labels("data/labels_v1.jsonl")