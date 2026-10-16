# actual evaluation by comparing model predictions against the ground truth
# outputs two files (evaluation_summary.csv, aggregated_metrics.csv)

import json
import pandas as pd
from collections import defaultdict

# read the file, return list of dictionaries
def load_jsonl(filepath: str):
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records

# calculate Precision, Recall F1 for retrieved test names
# true_set: real list of tests (ground truth)
# pred_set: tests found by your model 
# Precision: of all tests the model found, how many are correct 
# Recall: of all real testsm how many did the model successfully find 
# F1: balanced average of precision and recall 

def calc_prf(true_set: set, pred_set: set):
    tp = len(true_set & pred_set)       # true positive: correct tests found 
    fp = len(pred_set - true_set)       # false positive: wring tests found 
    fn = len(true_set - pred_set)       # false negative: real tests missed 
    precision = tp/(tp+fp) if (tp+fp) > 0 else 0.0
    recall = tp/(tp+fn) if (tp+fn) > 0 else 0.0
    f1 = 2*precision*recall/(precision+recall) if (precision+recall)>0 else 0.0
    return precision, recall, f1, tp, fp, fn

def main():
    LABELS_PATH = "../../data/labels_v1.jsonl"      # Ground truth
    RESULTS_PATH = "../../results/labels_v1.jsonl"  # Model output
    OUTPUT_CSV = "../../results/evaluation_summary.csv"
    AGG_CSV = "../../results/aggregated_metrics.csv"

    # load ground truth and model output 
    labels_raw = load_jsonl(LABELS_PATH)
    results_raw = load_jsonl(RESULTS_PATH)

    # conver ground truth list itno a dictionary: case_id to ground truth entry 
    gt_map = {r["case_id"]: r for r in labels_raw}

    # track aggregate metics for each model version
    rows = []
    per_version = defaultdict(lambda: {
        "total":0,
        "verdict_correct":0,
        "needs_review":0,
        "false_alarm":0,
        "sum_prec":0.0,
        "sum_rec":0.0,
        "sum_f1":0.0,
        "prf_count":0
    })

    # loop through every prediction made by the model 
    for res in results_raw:
        cid = res["case_id"]
        # skip any prediction where case_id is missing from ground truth
        if cid not in gt_map:
            print(f"WARNING: case {cid} missing from ground truth labels, skipping")
            continue
        gt = gt_map[cid]
        ver = res["version"]
        pred_v = res["verdict"]
        gt_v = gt["verdict"]

        # checkc if verdict matches ground truth (1 is correct, 0 is wrong)
        verdict_ok = 1 if pred_v == gt_v else 0
        # count cases where model output "needs_review"
        need_review = 1 if pred_v == "needs_review" else 0
        # false alarm: model says not covered, but grounf truth has tests 
        false_alarm = 1 if (pred_v == "not_covered" and len(gt["tests"])>0) else 0

        # compute test retrieval metrics 
        gt_tests = set(gt["tests"])
        pred_tests = set(res.get("tests_found", []))
        prec, rec, f1, _,_,_ = calc_prf(gt_tests, pred_tests)

        # save the case data for csv
        rows.append({
            "case_id":cid,
            "version":ver,
            "gt_verdict":gt_v,
            "pred_verdict":pred_v,
            "verdict_correct":verdict_ok,
            "needs_review":need_review,
            "false_alarm":false_alarm,
            "precision":prec,
            "recall":rec,
            "f1":f1,
            "gt_tests":";".join(gt["tests"]),
            "pred_tests":";".join(res.get("tests_found",[])),
            "reason":res.get("reason",""),
            "tool_calls":res.get("tool_calls",0),
            "tokens_in":res.get("tokens_in",0),
            "tokens_out":res.get("tokens_out",0)
        })

        # add the case metrics to aggregate totals 
        v = per_version[ver]
        v["total"] +=1
        v["verdict_correct"] += verdict_ok
        v["needs_review"] += need_review
        v["false_alarm"] += false_alarm
        v["sum_prec"] += prec
        v["sum_rec"] += rec
        v["sum_f1"] += f1
        v["prf_count"] += 1

    # write per-case data into csv
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Saved per-case details: {OUTPUT_CSV}")

    agg_rows = []
    print("\n==== AGGREGATED EVALUATION RESULTS ====")

    # calculate averages and print summary for each version
    for ver, data in per_version.items():
        total = data["total"]
        acc = data["verdict_correct"] / total               # verdict accuracy
        nr_rate = data["needs_review"] / total              # percentage of cases marked as "needs_review"
        fa_rate = data["false_alarm"] / total               # false alarm rate 
        avg_p = data["sum_prec"] / data["prf_count"]        # avg precision 
        avg_r = data["sum_rec"] / data["prf_count"]         # avg recall 
        avg_f = data["sum_f1"] / data["prf_count"]          # avg F1
        print(f"\nVersion {ver}")
        print(f"Total cases: {total}")
        print(f"Verdict Accuracy: {acc:.3f}")
        print(f"Needs Review Rate: {nr_rate:.3f}")
        print(f"False Alarm Rate: {fa_rate:.3f}")
        print(f"Avg Precision: {avg_p:.3f}, Recall: {avg_r:.3f}, F1: {avg_f:.3f}")
        agg_rows.append({
            "version":ver,
            "total_cases":total,
            "verdict_accuracy":acc,
            "needs_review_rate":nr_rate,
            "false_alarm_rate":fa_rate,
            "avg_precision":avg_p,
            "avg_recall":avg_r,
            "avg_f1":avg_f
        })
    # save summary metrics to csv
    agg_df = pd.DataFrame(agg_rows)
    agg_df.to_csv(AGG_CSV, index=False, encoding="utf-8")
    print(f"\nSaved aggregate metrics: {AGG_CSV}")

if __name__ == "__main__":
    main()