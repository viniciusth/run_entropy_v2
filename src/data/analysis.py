from collections import defaultdict
from typing import Any

from matplotlib.figure import Axes
from src.data.gen_buckets import PROCESSORS, TASKS_PER_BUCKET
from src.data.gen_results import scheduler_names
import matplotlib.pyplot as plt
import numpy as np

def run_analysis(file: str):
    data = None
    with open(file, "r") as f:
        data = eval(f.read())
    assert data is not None, "Data is None"

    print(data["missed"])
    for k, v in data["missed"].items():
        print(f"{k} missed {v} out of {TASKS_PER_BUCKET * 10 * len(PROCESSORS)} tests")
    total_cnt = 0
    scheds = scheduler_names()

    for p in PROCESSORS:
        print("-"*50)
        print(p, "processors")
        for i in range(10):
            print(f"{i*10}% -> {(i+1)*10}%")
            cnts = [0 for _ in range(len(scheds))]
            for s in range(len(scheds)):
                cnt = len(data["data"][scheds[s]][p][i])
                cnts[s] = cnt
            cnt = cnts[0]
            total_cnt += cnt
            for c in cnts:
                assert c == cnt, "Lengths don't match"

            if cnt == 0:
                print("No data")
                continue

            output = f"Count {cnt}"
            for s in scheds:
                entropy = 0
                entropymax = 0
                entropymin = int(1e9)
                for test in data["data"][s][p][i]:
                    entropy += test["entropy"]
                    entropymax = max(entropymax, test["entropy"])
                    entropymin = min(entropymin, test["entropy"])
                output += f" | {s} {entropy/cnt} ({entropymin}, {entropymax})"

            print(f"{i*10}% -> {(i+1)*10}%")
            print(output)
    print("-"*50)
    print(total_cnt, "total tests")
    print("generating plots...")
    boxplot_avg_entropy_by_utilization_bucket(data)
    # scatter_entropy_by_utilization(data)
    print("done")

def boxplot_avg_entropy_by_utilization_bucket(data):
    """
    Creates a boxplot of the entropy by utilization bucket with all schedulers having boxes together for each bucket
    Saves the result in results/avg_entropy_by_utilization_bucket_{processor_count}.png
    """
    scheds = scheduler_names()
    for p in PROCESSORS:
        gdata = {}
        for i in range(10):
            key = f"[0.{i}, {(i+1)//10}.{(i+1)%10}]"
            entropy_reorder = []
            entropy_edf = []
            entropy_randrun = []
            for s in scheds:
                for test in data["data"][s][p][i]:
                    if s == "P_REORDER":
                        entropy_reorder.append(test["entropy"])
                    elif s == "simso":
                        entropy_edf.append(test["entropy"])
                    elif s == "RUN_RANDOM":
                        entropy_randrun.append(test["entropy"])
            gdata[key] = [entropy_reorder, entropy_edf, entropy_randrun]

        # Categories
        categories = list(gdata.keys())
        methods = ["REORDER", "EDF", "RANDRUN"]

        # Data Preparation
        x = np.arange(len(categories))  # X-axis positions
        width = 0.2  # Width of each bar

        # Plotting
        _, ax = plt.subplots(figsize=(10, 6))
        ax: Any

        # Create a box for each method
        for i, method in enumerate(methods):
            boxdata = [gdata[key][i] for key in categories]
            bx = ax.boxplot(boxdata, positions=x + i * width, widths=width, showfliers=False, patch_artist=True, boxprops=dict(facecolor=f"C{i}"), medianprops=dict(color='black'))
            # add legend
            bx["boxes"][0].set_label(method)


        # Labeling
        ax.set_xlabel("Utilizations")
        ax.set_ylabel("Schedule Entropy")
        ax.set_title("Schedule Entropy vs Utilizations")
        ax.set_xticks(x + width)
        ax.set_xticklabels(categories, rotation=45)
        ax.legend()

        # Show grid and plot
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"results/entropy_by_utilization_bucket_{p}.png")

def scatter_entropy_by_utilization(data):
    """
    Creates a scatter plot of the entropy by utilization, a separate plot for each scheduler.
    The lowest amount of tasks is a small circle at 100% opacity, the bigger the amount of tasks the lower the opacity
    Saves the result in results/entropy_by_utilization_{scheduler}_{processor_count}.png
    """
    scheds = scheduler_names()
    for p in PROCESSORS:
        task_count_min = int(1e9)
        task_count_max = 0
        entropy_max = 0
        entropy_min = int(1e9)
        gdata = defaultdict(list)
        for s in scheds:
            for i in range(10):
                for test in data["data"][s][p][i]:
                    task_count_min = min(task_count_min, len(test["test"]))
                    task_count_max = max(task_count_max, len(test["test"]))
                    u = sum(task["wcet"] / task["period"] for task in test["test"])
                    sz = len(test["test"])
                    gdata[sz].append((u, test["entropy"]))
                    entropy_max = max(entropy_max, test["entropy"])
                    entropy_min = min(entropy_min, test["entropy"])

        norm = plt.Normalize(vmin=task_count_min, vmax=task_count_max)
        entropyNorm = plt.Normalize(vmin=0.9*entropy_min, vmax=1.1*entropy_max)
        cmap = plt.get_cmap("Greys")
        _, ax = plt.subplots(figsize=(10, 6))
        ax: Any
        marker_by_sched = {
            "P_REORDER": "o",
            "simso": "s",
            "RUN_RANDOM": "^"
        }
        for s in scheds:
            x = []
            y = []
            c = []
            for key, values in gdata.items():
                nx = [v[0] for v in values]
                ny = [entropyNorm(v[1]) for v in values]
                nc = [cmap(norm(key)) for _ in range(len(nx))]
                x.extend(nx)
                y.extend(ny)
                c.extend(nc)
            ax.scatter(x, y, alpha=0.4, c=c, s=10, marker=marker_by_sched[s], label=s)
        ax.set_xlabel("Utilization")
        ax.set_ylabel("Entropy")
        ax.set_title(f"Entropy vs Utilization")
        ax.legend()
        plt.tight_layout()
        plt.savefig(f"results/entropy_by_utilization_{p}.png")

