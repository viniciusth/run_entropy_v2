import random

from ..entropy.case_gen import gen_tasks

PROCESSORS = [8, 16, 32]
TASKS_PER_BUCKET = 100

def gen_buckets(file_path = None):
    """
    Simulation Setup:
    """
    processor_buckets = []
    for p in PROCESSORS:
        print("Processing", p)
        buckets = {i: [] for i in range(10)}
        for am in range(1, TASKS_PER_BUCKET+1):
            if am % 10 == 0:
                print("Generated", am)
            task_amount = random.randint(p + 2, 3 * p)
            for i in range(10):
                success = False
                while not success:
                    util = random.uniform(i/10 * p, (i+1)/10 * p)
                    tasks = gen_tasks(task_amount, util)
                    u = sum(task["wcet"] / task["period"] for task in tasks)
                    assert i/10 * p <= u <= (i+1)/10 * p
                    success = decreasing_first_fit_succeeds(tasks, p)
                    if success:
                        buckets[i].append(tasks)
        processor_buckets.append(buckets)
    if file_path:
        with open(file_path, "w") as f:
            f.write(str(processor_buckets))
    return processor_buckets

def decreasing_first_fit_succeeds(tasks, p):
    t = sorted(tasks, key=lambda x: x["wcet"] / x["period"], reverse=True)
    cpus = [0 for _ in range(p)]

    for task in t:
        j = 0
        while cpus[j] * task["period"] + task["wcet"] > task["period"]:
            j += 1
            if j >= p:
                return False
        cpus[j] += task["wcet"] / task["period"]
    return True

