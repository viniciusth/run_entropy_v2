import math
from simso.generator.task_generator import StaffordRandFixedSum
import random

from src.entropy.analysis import HYPERPERIOD_LEN

period_choices = [10, 20, 25, 50, 100]
def lcm(a, b):
    return a * b // math.gcd(a, b)

def lcmlist(args):
    ans = args[0]
    for i in range(1, len(args)):
        ans = lcm(ans, args[i])
    return ans

assert lcmlist(period_choices) == HYPERPERIOD_LEN, "LCM of periods is not as expected"


def gen_tasks(n: int, u: float):
    sets = StaffordRandFixedSum(n, u, 1)
    assert sets is not None and len(sets) == 1, "StaffordRandFixedSum returned unexpected result"
    utilizations = sets[0]
    periods = random.choices(period_choices, k=n)
    tasks = []
    for i in range(n):
        wcet = utilizations[i] * periods[i]
        tasks.append(
            {
                "period": periods[i],
                "deadline": periods[i],
                "activation_date": 0,
                "proportion": 0.5,
                "wcet": wcet,
            }
        )

    return tasks
