
import os
from typing import List, Tuple
from multiprocessing import Queue, Process
from src.data.gen_buckets import PROCESSORS
from src.entropy.analysis import HYPERPERIOD_LEN, K, entropy
from src.simso.model_builder import ACETModelBuilder
from src.simso.sim_data import SimData

# my cpu core count
THREAD_COUNT = 8

def gen_results(file_path: str):
    def process_job(task_queue: Queue, response_queue: Queue):
        while True:
            task = task_queue.get()
            if task is None:
                break
            test, p, i = task

            def inner(test, p, output):
                test_output = run_test(test, p)
                output.put((test_output, test))

            output = Queue(1)
            inner_p = Process(target=inner, args=(test, p, output))
            inner_p.start()
            inner_p.join(300)
            if inner_p.is_alive():
                print("Inner process timed out")
                print("test index:", i)
                inner_p.kill()
                response_queue.put(((None, test), p, i))
                continue
            test_output = output.get()
            response_queue.put((test_output, p, i))


    def save_partial_results(partial_result, name):
        with open(f"{name}_partial.json", "w") as f:
            f.write(str(partial_result))
            print()
            print("Saved partial results")

    input, partial_result = setup(file_path)

    line_sep = "\n" + "-"*50
    name = file_path.split(".")[:-1][0]

    current_idx = 0
    tests_ran_without_saving = 0
    tasks_processing = 0
    task_queue = Queue(20)
    response_queue = Queue(20)

    processes = []
    for _ in range(THREAD_COUNT):
        p = Process(target=process_job, args=(task_queue, response_queue))
        p.start()
        processes.append(p)

    for c, p in enumerate(PROCESSORS):
        print(line_sep)
        print("Processing", p)
        for i in range(10):
            print(line_sep)
            print("Current percentage", i*10, "->", (i+1)*10)
            for test in input[c][i]:
                if current_idx <= partial_result["idx"]:
                    current_idx += 1
                    continue
                print("Current idx", current_idx, end="\r")

                if task_queue.full():
                    if tests_ran_without_saving >= THREAD_COUNT * 5:
                        partial_result["idx"] = current_idx
                        tests_ran_without_saving = 0
                        # wait for all tasks so current_idx is correct.
                        while tasks_processing > 0:
                            test_output, x, y = response_queue.get()
                            handle_result(test_output, partial_result, x, y)
                            tasks_processing -= 1
                        save_partial_results(partial_result, name)
                    else:
                        test_output, x, y = response_queue.get()
                        handle_result(test_output, partial_result, x, y)
                        tasks_processing -= 1

                current_idx += 1
                tests_ran_without_saving += 1
                tasks_processing += 1
                task_queue.put([test, p, i])

    while tasks_processing > 0:
        test_output, p, i = response_queue.get()
        handle_result(test_output, partial_result, p, i)
        tasks_processing -= 1

    print("Finished all tests, shutting down processes")
    for _ in range(THREAD_COUNT):
        task_queue.put(None)

    for p in processes:
        p.join()

    print("All processes shut down, saving final results")

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

    partial_result = default_partial_result()
    try:
        with open(f"{file_name}_partial.json", "r") as f:
            partial_result = eval(f.read())
    except FileNotFoundError:
        print("No partial results found, continuing from scratch")
        pass

    return input, partial_result

def schedulers():
    return [
            {"clas": "simso.schedulers.P_EDF"},
            {"clas": "simso.schedulers.RUN"},
            {"filename": os.path.join(os.getcwd(), "src", "schedulers", "P_REORDER.py")},
            {"filename": os.path.join(os.getcwd(), "src", "schedulers", "RUN_RANDOM.py")},
    ]

def scheduler_name(s):
    if "clas" in s:
        return s["clas"].split(".")[-1]
    return s["filename"].split("/")[-1].split(".")[0]

def scheduler_names() -> List[str]:
    s = schedulers()
    ans = []
    for sched in s:
        ans.append(scheduler_name(sched))
    return ans

def run_test(test, processors):
    results = []
    for scheduler in schedulers():
        entropy, _, error = run_scheduler(test, processors, scheduler)
        if error is not None:
            name = scheduler_name(scheduler)
            print(name, "failed with error:", error)
            return {"failed": name, "entropy": None}
        results.append(entropy)

    return {"entropy": results, "failed": None}

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
            return None, None, "Packing failed"
        else:
            raise e

    if model.results.total_exceeded_count > 0: # type: ignore
        return None, None, f"Missed deadlines: {model.results.total_exceeded_count}"  # type: ignore

    data = SimData(model)
    hp = data.into_hyperperiods(HYPERPERIOD_LEN)
    if hp is None:
        return None, None, "No hyperperiods found"
    scheduler_entropy = entropy(hp, len(test), processors)
    return scheduler_entropy, model, None # type: ignore

def default_partial_result():
    return {
        "idx": 0,
        "timeouts": [],
        "missed": {
            name: 0 for name in scheduler_names()
        },
        "data": {
            name: {p: [[] for _ in range(10)] for p in PROCESSORS} for name in scheduler_names()
        },
    }

def handle_result(test_output, partial_result, p, i):
    output, test = test_output
    if output is None:
        partial_result["timeouts"].append((p, i, test))
        return
    if output["failed"] is not None:
        partial_result["missed"][output["failed"]] += 1
        return

    s = scheduler_names()
    for j, entropy in enumerate(output["entropy"]):
        partial_result["data"][s[j]][p][i].append({
            "entropy": entropy,
            "test": test,
        })


