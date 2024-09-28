
import os
from typing import Tuple
from src.data.gen_buckets import PROCESSORS
from src.entropy.analysis import HYPERPERIOD_LEN, K, entropy
from src.simso.model_builder import ACETModelBuilder
from src.simso.sim_data import SimData


def gen_results(file_path: str):
    input, partial_result = setup(file_path)

    line_sep = "\n" + "-"*50
    name = file_path.split(".")[:-1][0]

    current_idx = 0
    tests_ran_without_saving = 0
    for c, p in enumerate(PROCESSORS):
        print(line_sep)
        print("Processing", p)
        for i in range(10):
            print(line_sep)
            print("Current percentage", i, "->", (i+1)*10)
            for test in input[c][i]:
                if current_idx < partial_result["idx"]:
                    current_idx += 1
                    continue
                print("Current idx", current_idx, end="\r")
                current_idx += 1

                fg_run, p_reorder = run_test(test, p)
                if fg_run is None:
                    partial_result["missed"] += 1
                    continue
                tests_ran_without_saving += 1
                partial_result["data"]["fg_run"][p][i].append(fg_run)
                partial_result["data"]["p_reorder"][p][i].append(p_reorder)

                if tests_ran_without_saving == 5:
                    partial_result["idx"] = current_idx
                    with open(f"{name}_partial.json", "w") as f:
                        f.write(str(partial_result))
                    print()
                    print("Saved partial results")
                    tests_ran_without_saving = 0

    with open(f"{name}_results.json", "w") as f:
        partial_result.pop("idx")
        f.write(str(partial_result))
    print("Saved final results")
    os.remove(f"{name}_partial.json")


def setup(file_path: str) -> Tuple[dict, dict]:
    file_name = file_path.split(".")[:-1][0]
    input = None
    with open(file_path, "r") as f:
        input = eval(f.read())
    assert input is not None, "Input is None"
    assert len(input) == len(PROCESSORS), "Input length is not as expected"

    partial_result = {
        "idx": 0,
        "missed": 0,
        "data": {
            "fg_run": {
                p: [[] for _ in range(10)] for p in PROCESSORS
            },
            "p_reorder": {
                p: [[] for _ in range(10)] for p in PROCESSORS
            },
        },
    }
    try:
        with open(f"{file_name}_partial.json", "r") as f:
            partial_result = eval(f.read())
    except FileNotFoundError:
        print("No partial results found, continuing from scratch")
        pass

    return input, partial_result


def run_test(test, processors):
    filename = os.path.join(os.getcwd(), "src", "schedulers", "P_REORDER.py")
    p_reorder, err = run_scheduler(test, processors, {"filename": filename})
    if err is not None:
        print("P_REORDER error:", err)
        return None, None

    filename = os.path.join(os.getcwd(), "src", "schedulers", "P_FG_RUN.py")
    fg_run, err = run_scheduler(test, processors, {"filename": filename})
    if err is not None:
        print("P_FG_RUN error:", err)
        return None, None

    return fg_run, p_reorder

def run_scheduler(test, processors, scheduler):
    builder = ACETModelBuilder()
    for _ in range(processors):
        builder.add_cpu()

    for task in test:
        builder.add_task(**task)
    builder.set_duration(HYPERPERIOD_LEN * K)

    builder.set_scheduler(**scheduler)  # type: ignore

    model = builder.build()
    try:
        model.run_model()
    except AssertionError as e:
        if "Packing failed" in str(e):
            return None, "Packing failed"

    if model.results.total_exceeded_count > 0: # type: ignore
        return None, f"Missed deadlines: {model.results.total_exceeded_count}"  # type: ignore

    data = SimData(model)
    hp = data.into_hyperperiods(HYPERPERIOD_LEN)
    if hp is None:
        return None, "No hyperperiods found"
    scheduler_entropy = entropy(hp, len(test), processors)
    return scheduler_entropy, None # type: ignore

