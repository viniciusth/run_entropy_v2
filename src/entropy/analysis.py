from typing import List
import math


K = 100
HYPERPERIOD_LEN = 100
m = 35  # int(HYPERPERIOD_LEN * 0.35)
pi = 10  # HYPERPERIOD_LEN * 0.1


def entropy(data: List[List[List[int]]]) -> float:
    """
    Calculates the entropy of the schedule.
    data: Processor -> Hyperperiod -> Execution (start, end, task)
    """

    def n(t: int) -> float:
        ans = 0.0
        for k in range(1, K + 1):
            ans += math.log2(C(k, t))
        return -ans / k

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
