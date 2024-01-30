import random

from ..entropy.case_gen import gen_tasks


def gen_buckets(file_path: str = None):
    """
    Simulation Setup: We used the parameters similar to
    that in earlier research [8], [24], [40], [41]. The tasksets
    were grouped into base-utilization buckets (e.g., total sum of
    the task utilizations) from [0.01 + 0.1 ⋅ i, 0.1 + 0.1 ⋅ i] where
    i ∈ Z ∧ 0 ≤ i < 9. Each base-utilization group contained
    250 tasksets and each of which had [3, 10] tasks. We only
    considered tasksets that were schedulable by EDF
    """

    def check(buckets):
        for i in range(9):
            if len(buckets[i]) < 250:
                return True
        return False

    buckets = {i: [] for i in range(9)}
    while check(buckets):
        task_amount = random.randint(3, 10)
        for i in range(9):
            tasks = gen_tasks(task_amount, 0.01 + 0.1 * i)
            u = sum(task["wcet"] / task["period"] for task in tasks)
            if 0.01 + 0.1 * i <= u <= 0.1 + 0.1 * i:
                buckets[i].append(tasks)

    if file_path:
        with open(file_path, "w") as f:
            f.write(str(buckets))
    return buckets
