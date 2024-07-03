import math
from typing import List
from simso.generator.task_generator import StaffordRandFixedSum
import random

from src.entropy.analysis import HYPERPERIOD_LEN

from ..simso.model_builder import TaskParams

period_choices = [10, 20, 25, 50, 100]
assert math.lcm(*period_choices) == HYPERPERIOD_LEN, "LCM of periods is not as expected"


def gen_tasks(n: int, u: float) -> List[TaskParams]:
    sets = StaffordRandFixedSum(n, u, 1)
    assert sets is not None and len(sets) == 1, "StaffordRandFixedSum returned unexpected result"
    utilizations = sets[0]
    periods = random.choices(period_choices, k=n)
    tasks: List[TaskParams] = []
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
