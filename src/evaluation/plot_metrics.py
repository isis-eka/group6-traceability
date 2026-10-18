# generates charts
# usage: python src/evaluation/plot_metrics.py results/dev/v1/embedding_metrics.csv results/dev/v1/bm25_metrics.csv
# several files are drawn side by side in one chart, to compare runs (e.g. embedding vs bm25)
# charts are saved next to the first file (accuracy.png, prf.png)

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# load aggregated metrics csv and draw bar chart
# bar chart 1: verdict accuracy vs false alarm rate 
# Precision, Recall and F1 scores for retrieval 
# saves the images into results folder 
def plot_all(csv_paths):
    df = pd.concat([pd.read_csv(p) for p in csv_paths], ignore_index=True)
    out_dir = Path(csv_paths[0]).parent
    plt.rcParams["figure.figsize"] = (12,6)

    # Combine version + search strategy for readable x-axis labels
    df["group_label"] = df["version"] + "\n" + df["search_strategy"]
    x_labels = df["group_label"]
    x = list(range(len(x_labels)))
    bar_width = 0.25  

    # bar chart 1: verdict aaccuracy, false alarm, all false clear
    fig1, ax = plt.subplots()
    ax.bar([i - bar_width for i in x], df["verdict_accuracy"], width=bar_width, label="Verdict Accuracy")
    ax.bar(x, df["false_alarm_rate"], width=bar_width, label="False Alarm Rate")
    ax.bar([i + bar_width for i in x], df["false_all_clear_rate"], width=bar_width, label="False All-Clear Rate")

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score (0 to 1)")
    ax.set_title("Verdict Accuracy, False Alarm & False All-Clear Rate")
    ax.legend()
    plt.savefig(out_dir / "accuracy.png", dpi=300, bbox_inches="tight")
    plt.close()

    # bar chart 2: Precision, Recall and F1 scores for retrieval
    fig2, ax2 = plt.subplots()
    ax2.bar([i - bar_width for i in x], df["avg_precision"], width=bar_width, label="Precision")
    ax2.bar(x, df["avg_recall"], width=bar_width, label="Recall")
    ax2.bar([i + bar_width for i in x], df["avg_f1"], width=bar_width, label="F1 Score")

    ax2.set_xticks(x)
    ax2.set_xticklabels(x_labels)
    ax2.set_ylim(0,1.05)
    ax2.set_ylabel("Score (0 to 1)")
    ax2.set_title("Test Retrieval Precision / Recall / F1")
    ax2.legend()
    plt.savefig(out_dir / "prf.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Side-by-side charts saved to {out_dir}/")

# Run plotting when this file is executed
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python src/evaluation/plot_metrics.py results/<split>/<round>/<search>_metrics.csv [...]")
    plot_all(sys.argv[1:])