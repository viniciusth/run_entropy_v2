from collections import defaultdict, namedtuple
from typing import Dict, List
from simso.core import Scheduler

from simso.core.Task import PTask, TaskInfo
from simso.core.Job import Job
from simso.core.Processor import Processor

LastJob = namedtuple("LastJob", ["task", "start", "end"])


class REORDER(Scheduler):
    def init(self):
        utilization = sum(task.wcet / task.period for task in self.task_list)
        assert utilization <= 1, "Utilization must be <= 1"

        # Worst-case response time
        self.wcrt = compute_wcrt(self.task_list)
        # Remaining inversion budget, updated at each activation
        self.rib: Dict[PTask, float] = {}
        # last job that ran, used to update the remaining inversion budget on schedule
        self.last_job = LastJob(None, -1, -1)

        print(self.task_list, self.wcrt)
        pass

    def on_activate(self, job: Job):
        self.rib[job.task] = self.wcrt[job.task.identifier]
        pass

    def on_terminated(self, job: Job):
        if job.task == self.last_job.task:
            self.last_job.end = self.sim.now_ms()
        pass

    def schedule(self, cpu: Processor):
        if self.last_job.start != -1:
            if self.last_job.end == -1:
                self.last_job.end = self.sim.now_ms()
            self.update_rib()
        pass

    def update_rib(self):
        assert (
            self.last_job.start != -1
            and self.last_job.end != -1
            and self.last_job.task != None
        ), "update_rib: last_job not initialized"
        for task_i in self.rib.keys():
            if (
                task_i == self.last_job.task
                or task_i.deadline > self.last_job.task.deadline
            ):
                continue
            self.rib[task_i] -= self.last_job.end - self.last_job.start

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
