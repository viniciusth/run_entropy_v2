from typing import List
from simso.generator.task_generator import UUniFastDiscard
import random

from ..simso.model_builder import TaskParams

period_choices = [10, 20, 25, 50, 100]


def gen_tasks(n: int, u: float) -> List[TaskParams]:
    while True:
        utilizations = UUniFastDiscard(n, u, 1)[0]
        periods = random.choices(period_choices, k=n)
        tasks: List[TaskParams] = []
        util = 0
        for i in range(n):
            # wcet = max(1, round(utilizations[i] * periods[i]))
            wcet = utilizations[i] * periods[i]
            util += wcet / periods[i]
            tasks.append(
                {
                    "period": periods[i],
                    "deadline": periods[i],
                    "activation_date": 0,
                    "proportion": 0.5,
                    "wcet": wcet,
                }
            )
        if util < 1:
            break

    return tasks
