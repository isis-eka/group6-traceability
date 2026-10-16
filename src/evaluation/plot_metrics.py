# generates charts 

import pandas as pd
import matplotlib.pyplot as plt

# load aggregated metrics csv and draw bar chart
# bar chart 1: verdict accuracy vs false alarm rate 
# Precision, Recall and F1 scores for retrieval 
# saves the images into results folder 
def plot_all(csv_path="../../results/aggregated_metrics.csv"):
    df = pd.read_csv(csv_path)
    plt.rcParams["figure.figsize"] = (10,6)

    # bar chart 1: accuracy and false alarm rate
    fig, ax = plt.subplots()
    x = df["version"]
    ax.bar(x, df["verdict_accuracy"], label="Verdict Accuracy")
    ax.bar(x, df["false_alarm_rate"], label="False Alarm Rate")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score (0 to 1)")
    ax.set_title("Verdict Accuracy and False Alarm Rate")
    ax.legend()
    plt.savefig("../../results/accuracy_false_alarm.png", dpi=300, bbox_inches="tight")
    plt.close()

    # bar chart 2: Precision, Recall, F1 scores 
    fig2, ax2 = plt.subplots()
    ax2.bar(x, df["avg_precision"], label="Precision")
    ax2.bar(x, df["avg_recall"], label="Recall")
    ax2.bar(x, df["avg_f1"], label="F1 Score")
    ax2.set_ylim(0,1.05)
    ax2.set_ylabel("Score (0 to 1)")
    ax2.set_title("Test Retrieval Precision / Recall / F1")
    ax2.legend()
    plt.savefig("../../results/prf_metrics.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Charts saved to results folder.")

# Run plotting when this file is executed
if __name__ == "__main__":
    plot_all()