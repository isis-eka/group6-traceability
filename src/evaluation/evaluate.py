# actual evaluation by comparing model predictions against the ground truth
# outputs two files (evaluation_summary.csv, aggregated_metrics.csv)

import os
import json
import re
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

def normalize_test_name(test_name: str) -> str:
    """
    Fix: strip everything starting from '['
    e.g. "test_invalid_url[InvalidURL-http://.example.com]" → "test_invalid_url"
    """
    return test_name.split("[")[0]

# ensure that ac1 and ac2 (acN) can be distinguished 
# remove the label suffixes (covered, not_covered, partial) while preserving the acceptance criterion (ac1, ac2...)
# preserves __acN, which is important because we are labelling test coverage for each acceptance criterion, rather than only for each issue
def normalize_case_id(case_id):
    case_id = case_id.strip()

    case_id = re.sub(
        r"__(covered|not_covered|partial)$", "", case_id)

    return case_id

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
    LABELS_PATH = "data/labels_v1.jsonl"        # Ground truth
    RESULTS_PATH = "data/results.jsonl"         # Model output
    OUTPUT_CSV = "results/evaluation_summary.csv"
    AGG_CSV = "results/aggregated_metrics.csv"

    # load ground truth and model output 
    labels_raw = load_jsonl(LABELS_PATH)
    results_raw = load_jsonl(RESULTS_PATH)

    # convert ground truth list into a dictionary: case_id to ground truth entry 
    gt_map = {r["case_id"]: r for r in labels_raw}
    
    # track aggregate metics for each model version
    rows = []
    per_group = defaultdict(lambda: {
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
        raw_result_cid = res["case_id"]
        norm_cid = normalize_case_id(raw_result_cid)

        if norm_cid not in gt_map:
            print(f"WARNING: normalized case {norm_cid} (original={raw_result_cid}) missing from ground truth labels, skipping")
            continue

        gt = gt_map[norm_cid]
        ver = res["version"]
        search_strategy = res["search"]

        pred_v = res["verdict"]
        gt_v = gt["verdict"]

        # check if verdict matches ground truth (1 is correct, 0 is wrong)
        verdict_ok = 1 if pred_v == gt_v else 0
        # count cases where model output "needs_review"
        need_review = 1 if pred_v == "needs_review" else 0
        # model predicting not_covered when the ground truth says covered
        false_alarm = 1 if (pred_v == "not_covered" and gt_v == "covered") else 0
        false_all_clear = 1 if (pred_v == "covered" and gt_v == "not_covered") else 0

        # compute test retrieval metrics 
        gt_tests_raw = gt["tests"]
        pred_tests_raw = res.get("tests_found", [])
        gt_tests = set(normalize_test_name(t) for t in gt_tests_raw)
        pred_tests = set(normalize_test_name(t) for t in pred_tests_raw)

        if len(gt["tests"]) > 0:
            prec, rec, f1, _,_,_ = calc_prf(gt_tests, pred_tests)
        else:
            prec, rec, f1 = None, None, None

        # save the case data for csv
        rows.append({
            "case_id":raw_result_cid,
            "normalized_case_id":norm_cid,
            "search":search_strategy,
            "version":ver,
            "gt_verdict":gt_v,
            "pred_verdict":pred_v,
            "verdict_correct":verdict_ok,
            "needs_review":need_review,
            "false_alarm":false_alarm,
            "false_all_clear":false_all_clear,
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
        group_key = (ver, search_strategy)
        g = per_group[group_key]
        g["total"] +=1
        g["verdict_correct"] += verdict_ok
        g["needs_review"] += need_review
        g["false_alarm"] += false_alarm
        g["false_all_clear"] += false_all_clear

        if prec is not None:
            g["sum_prec"] += prec
            g["sum_rec"] += rec
            g["sum_f1"] += f1
            g["prf_count"] +=1


    # write per-case data into csv
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Saved per-case details: {OUTPUT_CSV}")

    agg_rows = []
    print("\n==== AGGREGATED EVALUATION RESULTS ====")

    # calculate averages and print summary for each version
    for (ver, search_strategy), data in per_group.items():
        total = data["total"]
        acc = data["verdict_correct"] / total               # verdict accuracy
        nr_rate = data["needs_review"] / total              # percentage of cases marked as "needs_review"
        fa_rate = data["false_alarm"] / total               # false alarm rate
        fac_rate = data["false_all_clear"] / total          # false all clear rate
        # prevents the evaluation from crashing when no cases have ground-truth tests
        # pandas will write missing averages as blank values in CSV
        if data["prf_count"] > 0:
            avg_p = data["sum_prec"] / data["prf_count"]
            avg_r = data["sum_rec"] / data["prf_count"]
            avg_f = data["sum_f1"] / data["prf_count"]
        else:
            avg_p = None
            avg_r = None
            avg_f = None
        print(f"\nVersion {ver}, Search Strategy: {search_strategy}")
        print(f"Total cases: {total}")
        print(f"Verdict Accuracy: {acc:.3f}")
        print(f"Needs Review Rate: {nr_rate:.3f}")
        print(f"False Alarm Rate: {fa_rate:.3f}")
        print(f"False All Clear Rate: {fac_rate:.3f}")
        if avg_p is not None:
            print(f"Avg Precision: {avg_p:.3f}, " f"Recall: {avg_r:.3f}, F1: {avg_f:.3f}")
        else:
            print("Avg Precision, Recall, F1: N/A")
        agg_rows.append({
            "version":ver,
            "search_strategy":search_strategy,
            "total_cases":total,
            "verdict_accuracy":acc,
            "needs_review_rate":nr_rate,
            "false_alarm_rate":fa_rate,
            "false_all_clear_rate":fac_rate,
            "avg_precision":avg_p,
            "avg_recall":avg_r,
            "avg_f1":avg_f,
            "num_covered_cases_for_prf":data["prf_count"]
        })

    # save summary metrics to csv 
    agg_df = pd.DataFrame(agg_rows)
    agg_df.to_csv(AGG_CSV, index=False, encoding="utf-8")
    print(f"\nSaved aggregate metrics: {AGG_CSV}")

if __name__ == "__main__":
    main()