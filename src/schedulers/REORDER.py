from collections import defaultdict
from typing import List
from simso.core import Scheduler

from simso.core.Task import PTask


class REORDER(Scheduler):
    def init(self):
        utilization = sum(task.wcet / task.period for task in self.task_list)
        assert utilization <= 1, "Utilization must be <= 1"
        self.wcrt = compute_wcrt(self.task_list)
        print(self.task_list, self.wcrt)
        pass

    def on_activate(self, job):
        pass

    def on_terminated(self, job):
        pass

    def schedule(self, cpu):
        pass


def intceil(x: int, y: int):
    return (x + y - 1) // y


def compute_wcrt(task_list: List[PTask]):
    wcrt = defaultdict(int)
    r_hat = compute_r_hat(task_list)
    for a in range(0, r_hat):
        for task in task_list:
            interference = 0
            for task_j in task_list:
                if (
                    task.identifier == task_j.identifier
                    or task_j.deadline > a + task.deadline
                ):
                    continue
                interference += (
                    min(
                        intceil(task.deadline, task_j.period) + 1,
                        1 + (a + task.deadline - task_j.deadline) // task_j.period + 1,
                    )
                    * task_j.wcet
                )

            if a >= r_hat - task.wcet:
                continue
            wcrt[task.identifier] = max(
                wcrt[task.identifier],
                task.wcet,
                workload(task, a) - a + interference,
            )
    return wcrt


def compute_r_hat(task_list: List[PTask]):
    r0 = sum(task.wcet for task in task_list)
    iterations = 0
    while True:
        r1 = sum(intceil(r0, task.period) * task.wcet for task in task_list)
        iterations += 1
        if r0 == r1:
            return r0
        r0 = r1
        assert iterations < 1000, "compute_r_hat: too many iterations"


def workload(task: PTask, a: int):
    return (a // task.period + 1) * task.wcet
