from typing import List
import math


K = 100
HYPERPERIOD_LEN = 100
m = 35  # int(HYPERPERIOD_LEN * 0.35)
pi = 10  # HYPERPERIOD_LEN * 0.1


# REORDER entropy calculation, way heavier, not sure if worth it
def entropy2(data: List[List[List[int]]], _) -> float:
    """
    Calculates the entropy of the schedule.
    data: Processor -> Hyperperiod -> Execution (start, end, task)
    """

    def n(t: int) -> float:
        ans = 0.0
        for k in range(1, K + 1):
            ans += math.log2(C(k, t))
        return -ans / K

    def C(k: int, t: int) -> float:
        ans = 0
        for kl in range(1, K + 1):
            ans += 1 if hamming(data[0][k], data[0][kl], t) <= pi else 0
        return ans / K

    ans = 0.0
    for t in range(HYPERPERIOD_LEN):
        ans += n(t)
    return ans / m


def hamming(a: List[int], b: List[int], offset: int) -> int:
    ans = 0
    for i in range(m):
        if a[(i + offset) % HYPERPERIOD_LEN] != b[(i + offset) % HYPERPERIOD_LEN]:
            ans += 1
    return ans


def entropy(data: List[List[List[int]]], task_amount: int, processor_amount: int = 1, hyperperiod_amount = K, hyperperiod_len = HYPERPERIOD_LEN) -> float:
    """
    Calculates the entropy of the schedule.
    data: Processor -> Hyperperiod -> Execution (start, end, task)
    """

    def n(t: int) -> float:
        ans = 0.0
        tasks_freq = [0] * (task_amount + 1)
        processors_used = set()
        for pi in range(processor_amount):
            assert len(data[pi]) == hyperperiod_amount, f"Expected {hyperperiod_amount} hyperperiods, got {len(data[pi])}"
            for hyperperiod in range(hyperperiod_amount):
                assert len(data[pi][hyperperiod]) == hyperperiod_len, f"Expected {hyperperiod_len} executions, got {len(data[pi][hyperperiod])}"
                tasks_freq[data[pi][hyperperiod][t]] += 1
                if data[pi][hyperperiod][t] != 0:
                    processors_used.add(pi)

        for task in range(1, task_amount + 1):
            if tasks_freq[task] == 0:
                continue
            p = tasks_freq[task] / (hyperperiod_amount * len(processors_used))
            ans -= p * math.log2(p)

        return ans

    ans = 0.0
    for t in range(hyperperiod_len):
        ans += n(t)
    return ans
