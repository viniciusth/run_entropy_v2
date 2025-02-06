"""
Implementation of the RUN scheduler as introduced in RUN: Optimal
Multiprocessor Real-Time Scheduling via Reduction to Uniprocessor
by Regnier et al.

RUN is a global multiprocessors scheduler for periodic-preemptive-independent
tasks with implicit deadlines.
"""

import random
from simso.core import Scheduler, Timer
from simso.schedulers.RUNServer import EDFServer, TaskServer, DualServer, \
    add_job, get_child_tasks
from simso.schedulers import scheduler

@scheduler("src.schedulers.RUN_RANDOM")
class RUN_RANDOM(Scheduler):
    """
    RUN scheduler. The offline part is done here but the online part is mainly
    done in the SubSystem objects. The RUN object is a proxy for the
    sub-systems.
    """

    def init(self):
        """
        Initialization of the scheduler. This function is called when the
        system is ready to run.
        """
        self.subsystems = []  # List of all the sub-systems.
        self.available_cpus = self.processors[:]  # Not yet affected cpus.
        self.task_to_subsystem = {}  # map: Task -> SubSystem

        # Create the Task Servers. Those are the leaves of the reduction tree.
        list_servers = [TaskServer(task) for task in self.task_list]

        # map: Task -> TaskServer. Used to quickly find the servers to update.
        self.servers = dict(zip(self.task_list, list_servers))

        assert (sum([s.utilization for s in list_servers])
                <= len(self.processors)), "Load exceeds 100%!"

        # Instantiate the reduction tree and the various sub-systems.
        self.reduce_iterations(list_servers)

    def add_idle_tasks(self, servers):
        """
        Create IdleTasks in order to reach 100% system utilization.
        """
        from collections import namedtuple
        # pylint: disable-msg=C0103
        IdleTask = namedtuple('IdleTask', ['utilization'])

        idle = len(self.processors) - sum([s.utilization for s in servers])
        for server in servers:
            if server.utilization < 1 and idle > 0:
                task = IdleTask(min(1 - server.utilization, idle))
                server.add_child(TaskServer(task))
                idle -= task.utilization
        while idle > 0:
            task = IdleTask(min(1, idle))
            server = EDFServer()
            server.add_child(TaskServer(task))
            idle -= task.utilization
            servers.append(server)

    def add_proper_subsystem(self, server):
        """
        Create a proper sub-system from a unit server.
        """
        tasks_servers = get_child_tasks(server)
        subsystem_utilization = sum([t.utilization for t in tasks_servers])
        cpus = []
        while subsystem_utilization > 0:
            cpus.append(self.available_cpus.pop())
            subsystem_utilization -= 1

        subsystem = ProperSubsystem(self.sim, server, cpus)
        for server in tasks_servers:
            self.task_to_subsystem[server.task] = subsystem
        self.subsystems.append(subsystem)

    def remove_unit_servers(self, servers):
        """
        Remove all the unit servers for a list and create a proper sub-system
        instead.
        """
        for server in servers:
            if server.utilization == 1:
                self.add_proper_subsystem(server)
        servers[:] = [s for s in servers if s.utilization < 1]

    def reduce_iterations(self, servers):
        """
        Offline part of the RUN Scheduler. Create the reduction tree.
        """
        servers = pack(servers)
        self.add_idle_tasks(servers)
        self.remove_unit_servers(servers)

        while servers:
            servers = pack(dual(servers))
            self.remove_unit_servers(servers)

    def on_activate(self, job):
        """
        Deal with a (real) task activation.
        """
        subsystem = self.task_to_subsystem[job.task]
        subsystem.update_budget()
        add_job(self.sim, job, self.servers[job.task])
        subsystem.resched(job.cpu)

    def on_terminated(self, job):
        """
        Deal with a (real) job termination.
        """
        subsystem = self.task_to_subsystem[job.task]
        self.task_to_subsystem[job.task].update_budget()
        subsystem.resched(job.cpu)

    def schedule(self, _):
        """
        This method is called by the simulator. The sub-systems that should be
        rescheduled are also scheduled.
        """
        decisions = []
        for subsystem in self.subsystems:
            if subsystem.to_reschedule:
                decisions += subsystem.schedule()

        return decisions


def pack(servers):
    """
    Create a list of EDF Servers by packing servers. Currently use a
    First-Fit but the original article states they used a Worst-Fit packing
    algorithm. According to the article, a First-Fit should also work.
    """
    packed_servers = []
    for server in servers:
        for p_server in packed_servers:
            if p_server.utilization + server.utilization <= 1:
                p_server.add_child(server)
                break
        else:
            p_server = EDFServer()
            p_server.add_child(server)
            packed_servers.append(p_server)

    return packed_servers


def dual(servers):
    """
    From a list of servers, returns a list of corresponding DualServers.
    """
    return [DualServer(s) for s in servers]


class ProperSubsystem(object):
    """
    Proper sub-system. A proper sub-system is the set of the tasks belonging to
    a unit server (server with utilization of 1) and a set of processors.
    """

    def __init__(self, sim, root, processors):
        self.sim = sim
        self.root = root
        self.processors = processors
        self.virtual = []
        self.last_update = 0
        self.to_reschedule = False
        self.timer = None
        self.random_jobs = {
            "idx": 0,
            "finished": False,
        }
        self.utilization = sum(
            [s.utilization for s in root.children]
        )
        # print("Utilization", self.utilization, "Root", root)
        # print("Children", root.children)
        # print("Processors", processors)
        # print("Virtual", self.virtual)

    def update_budget(self):
        """
        Update the budget of the servers.
        """
        time_since_last_update = self.sim.now() - self.last_update
        for server in self.virtual:
            server.budget -= time_since_last_update
        self.last_update = self.sim.now()

    def resched(self, cpu):
        """
        Plannify a scheduling decision on processor cpu. Ignore it if already
        planned.
        """
        if not self.to_reschedule:
            self.to_reschedule = True
            cpu.resched()

    def virtual_event(self, cpu):
        """
        Virtual scheduling event. Happens when a virtual job terminates.
        """
        self.update_budget()
        self.resched(cpu)

    def random_event(self, idx):
        """
        Random scheduling event. Happens when a timer for a set of randomized jobs fires.
        """
        if idx != self.random_jobs["idx"] or self.random_jobs["finished"]:
            return
        self.update_budget()
        self.resched(self.processors[0])
        self.random_jobs["finished"] = True

    def get_slack(self, now):
        servers = self.root.children
        beta = sum(s.budget for s in servers)
        # print([s.budget for s in servers])
        omega = max(0, self.root.next_deadline - now - beta)
        return omega

    def schedule(self):
        """
        Schedule this proper sub-system.
        """
        self.to_reschedule = False
        decision = []

        slack = self.get_slack(self.sim.now())
        # print("scheduling at", self.sim.now(), slack)

        self.virtual = []
        jobs = select_jobs(self.root, self.virtual, True, True, False, slack)

        wakeup_delay = min(self.virtual, key=lambda s: s.budget).budget
        if wakeup_delay > 0:
            self.timer = Timer(self.sim, ProperSubsystem.virtual_event,
                               (self, self.processors[0]), wakeup_delay,
                               cpu=self.processors[0], in_ms=False)
            self.timer.start()

        cpus = []
        for cpu in self.processors:
            if cpu.running in jobs:
                jobs.remove(cpu.running)
            else:
                cpus.append(cpu)

        random_jobs = []
        for cpu in cpus:
            if jobs:
                job, is_randomized = jobs.pop()
                if is_randomized:
                    random_jobs.append(job)
                decision.append((job, cpu))
            else:
                decision.append((None, cpu))

        if len(random_jobs) > 0:
            assert len(random_jobs) == 1
            # print("random_jobs", len(random_jobs), len(self.random_jobs), self.sim.now())
            # print("random_jobs", random_jobs[0] is None, self.random_jobs, slack, self.sim.now())
            idx = self.random_jobs["idx"] + 1
            # slack = max(int(slack * random.random()), 1)
            self.timer = Timer(self.sim, ProperSubsystem.random_event,
                               (self, idx), int(slack * 0.95), cpu=self.processors[0], in_ms=False)
            self.timer.start()
            self.random_jobs["idx"] += 1
            self.random_jobs["finished"] = False

        return decision

def select_jobs(server, virtual, execute, first, is_randomized, slack):
    """
    Select the jobs that should run according to RUN. The virtual jobs are
    appended to the virtual list passed as argument.
    """
    jobs = []
    if execute:
        virtual.append(server)

    if server.task:
        if execute and server.budget > 0 and server.job.is_active():
            jobs.append((server.job, is_randomized))
    else:
        if server.is_dual:
            jobs += select_jobs(server.child, virtual, not execute, False, is_randomized, slack)
        else:
            active_servers = [s for s in server.children if s.budget > 0]
            min_server = None
            is_randomized = False
            if active_servers:
                min_server = min(active_servers, key=lambda s: s.next_deadline)
                # jobs that are too small will just cause a lot of context switches for no reason
                # this should probably be sim.cycles_per_ms instead of static 10k
                if first and slack > 10000:
                    min_server = None
                    min_server_idx = random.randint(0, len(active_servers)) # able to choose len which means no job
                    if min_server_idx < len(active_servers):
                        min_server = active_servers[min_server_idx]
                    else:
                        jobs.append((None, True))
                    is_randomized = True

            for child in server.children:
                jobs += select_jobs(child, virtual,
                                    execute and child is min_server, False, is_randomized, slack)

    return jobs
