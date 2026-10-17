# generates charts 

import pandas as pd
import matplotlib.pyplot as plt

# load aggregated metrics csv and draw bar chart
# bar chart 1: verdict accuracy vs false alarm rate 
# Precision, Recall and F1 scores for retrieval 
# saves the images into results folder 
def plot_all(csv_path="results/aggregated_metrics.csv"):
    df = pd.read_csv(csv_path)
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
    plt.savefig("results/accuracy_false_error_rates.png", dpi=300, bbox_inches="tight")
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
    plt.savefig("results/prf_metrics.png", dpi=300, bbox_inches="tight")
    plt.close()

    print("✅ Side-by-side charts saved to results folder.")

# Run plotting when this file is executed
if __name__ == "__main__":
    plot_all()