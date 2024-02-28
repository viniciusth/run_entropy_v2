"""
Implementation of the RUN scheduler as introduced in RUN: Optimal
Multiprocessor Real-Time Scheduling via Reduction to Uniprocessor
by Regnier et al.

RUN is a global multiprocessors scheduler for periodic-preemptive-independent
tasks with implicit deadlines.
"""

from simso.core import Scheduler, Timer
import random
from src.schedulers.RUN_definitions import TaskServer, DualServer, delta_t, omega_t, EDFServer, get_child_tasks, select_jobs, add_job

INFINITO = int(1e30) 

class FG_RUN(Scheduler):
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
        self.Tdummy = []

        # Create the Task Servers. Those are the leaves of the reduction tree.
        list_servers = [TaskServer(task) for task in self.task_list]

        # map: Task -> TaskServer. Used to quickly find the servers to update.
        self.servers = dict(zip(self.task_list, list_servers))

        assert sum([s.utilization for s in list_servers]) <= len(
            self.processors
        ), "Load exceeds 100%!"

        # Instantiate the reduction tree and the various sub-systems.
        self.reduce_iterations(list_servers)

    def fill(self, servers, dummy):
        """
        Create IdleTasks in order to reach 100% system utilization.
        """
        from collections import namedtuple

        # pylint: disable-msg=C0103
        IdleTask = namedtuple("IdleTask", ["utilization", "deadline", "name"])

        idle = len(self.processors) - sum([s.utilization for s in servers])
        for server in servers:
            if server.utilization < 1 and idle > 0:
                task = IdleTask(min(1 - server.utilization, idle), 0, "IdleTask")
                t = TaskServer(task)
                self.Tdummy.append(t)
                t.dummyServer = True
                dummy.append(t)
                server.add_child(t)
                idle -= task.utilization
        while idle > 0:
            task = IdleTask(min(1, idle), 0, "IdleTask")
            t = TaskServer(task)
            server = EDFServer()
            server.add_child(TaskServer(task))
            idle -= task.utilization
            servers.append(server)

    def add_subsystem(self, server, level):
        """
        Create a proper sub-system from a unit server.
        """
        tasks_servers = get_child_tasks(server)
        subsystem_utilization = sum([t.utilization for t in tasks_servers])

        cpus = []

        while subsystem_utilization > 0:
            cpus.append(self.available_cpus.pop())
            subsystem_utilization -= 1

        subsystem = ProperSubsystem(self.sim, server, cpus, level)
        for server in tasks_servers:
            self.task_to_subsystem[server.task] = subsystem
        self.subsystems.append(subsystem)

    def remove_unit_servers(self, servers, level):
        """
        Remove all the unit servers for a list and create a proper sub-system
        instead.
        """
        for server in servers:
            if server.utilization == 1:
                self.add_subsystem(server, level)
        servers[:] = [s for s in servers if s.utilization < 1]

    def reduce_iterations(self, servers):
        """
        Offline part of the RUN Scheduler. Create the reduction tree.
        """
        dummy = []

        servers = pack_BFD(servers)

        self.fill(servers, dummy)

        level = 1
        self.remove_unit_servers(servers, level)

        while servers:
            s = dual(servers)
            servers = pack_BFD(s)
            level += 1
            self.remove_unit_servers(servers, level)

        self.sim.logger.log("Levels = {}".format(level))

        for d in dummy:
            d.next_deadline = INFINITO
            d.budget = INFINITO
            d.dummyServer = True

    def on_activate(self, job):
        """
        Deal with a (real) task activation.
        """
        subsystem = self.task_to_subsystem[job.task]
        subsystem.update_budget()
        add_job(self.sim, job, self.servers[job.task])
        subsystem.resched(self.processors[0])

    def on_terminated(self, job):
        """
        Deal with a (real) job termination.
        """
        subsystem = self.task_to_subsystem[job.task]
        self.task_to_subsystem[job.task].update_budget()
        subsystem.resched(self.processors[0])

    def schedule(self, _): # type: ignore
        """
        This method is called by the simulator. The sub-systems that should be
        rescheduled are also scheduled.
        """
        decisions = []

        for subsystem in self.subsystems:
            if subsystem.to_reschedule:
                decisions += subsystem.schedule()

        return decisions


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

    def __init__(self, sim, root, processors, level):
        self.sim = sim
        self.root = root
        self.processors = processors
        self.level = level
        self.virtual = []
        self.last_update = 0
        self.to_reschedule = False
        self.timer = None

        self.utilization = sum(
            [s.utilization for s in root.children if s.dummyServer is False]
        )

        self.dummy_timer = None

        self.is_idle = True
        self.keep = True

        self.idleBegin = 0
        self.idleEnd = 0

        self.busyBegin = 0
        self.busyEnd = 0

    def update_budget(self):
        """
        Update the budget of the servers.
        """

        time_since_last_update = self.sim.now() - self.last_update
        for server in self.virtual:
            server.budget -= time_since_last_update
        self.last_update = self.sim.now()

    def bug(self, subsystem):
        for cpu in subsystem.processors:
            if any(x[0] == 2 or x[0] == 3 for x in cpu._evts) and self.sim.now() > 0:
                return True
        return False

    def resched(self, cpu):
        """
        Plannify a scheduling decision on processor cpu. Ignore it if already
        planned.
        """

        if not self.bug(self):
            self.to_reschedule = True
            cpu.resched()

    def virtual_event(self, cpu):
        """
        Virtual scheduling event. Happens when a virtual job terminates.
        """

        self.update_budget()
        self.resched(cpu)

    def end_dummy(self, cpu):
        self.update_budget()
        self.to_reschedule = True
        self.resched(cpu)

    def add_timer(self, wakeup_delay, CPU):
        if self.dummy_timer:
            self.dummy_timer.stop()

        self.dummy_timer = Timer(
            self.sim,
            ProperSubsystem.end_dummy,
            (self, CPU),
            wakeup_delay,
            cpu=CPU,
            in_ms=False,
        )
        self.dummy_timer.start()

    # cumulative slack computation
    def CSC(self, t):

        active_servers = [
            s for s in self.root.children if (s.dummyServer is False) and s.budget > 0
        ]
        servers = [s for s in self.root.children if s.dummyServer is False]
        beta = beta = sum(s.budget for s in servers)
        omega = max(0, self.root.next_deadline - t - beta)

        if self.is_idle is True:
            # delta = omega
            delta = delta_t(self.utilization, servers, t, t)

            if delta > 0:
                self.idleEnd = t + delta
                self.busyBegin = self.idleEnd
                self.busyEnd = self.idleBegin + (self.idleEnd - self.idleBegin) / float(
                    1 - self.utilization
                )
            else:
                self.idleEnd = t
                self.busyBegin = self.idleEnd
                self.busyEnd = max(beta, self.busyEnd)
        else:
            if active_servers:
                self.busyEnd = max(t + beta, self.busyEnd)
            else:
                # v = omega_t(servers, t, self.root.next_deadline)
                v = delta_t(self.utilization, servers, t, self.root.next_deadline)

                self.idleBegin = t
                self.idleEnd = self.root.next_deadline + v
                self.busyBegin = self.idleEnd
                self.busyEnd = self.root.next_deadline + (
                    v / float(1 - self.utilization)
                )

    def schedule(self):
        """
        Schedule this proper sub-system.
        """

        self.to_reschedule = False
        self.virtual = []
        decision = []
        processors = []
        processors = self.processors

        self.CSC(self.sim.now())

        t = self.sim.now()

        if t >= self.idleBegin and t < self.idleEnd and not self.is_idle:
            self.is_idle = True
            sleep_for = (self.idleEnd - t) * random.random()
            self.add_timer(int(sleep_for), self.processors[0])
        else:
            self.is_idle = False

        selected = select_jobs(self, self.root, self.virtual)

        idle = [s for s in selected if s.task.name == "IdleTask"]
        jobs = [
            s.job
            for s in selected
            if s.task.name != "IdleTask" and s.task.name != "wcet"
        ]

        if idle:
            processors = self.processors[1:]  # Refresh available processors list
            decision.append((None, self.processors[0]))  # Set dummy to first processor

        wakeup_delay = min([s.budget for s in self.virtual if s.budget > 0])

        if wakeup_delay > 0:
            self.timer = Timer(
                self.sim,
                ProperSubsystem.virtual_event,
                (self, self.processors[0]),
                wakeup_delay,
                cpu=self.processors[0],
                in_ms=False,
            )
            self.timer.start()

        cpus = []

        # first, leave already executing tasks on their current processors;
        for cpu in processors:
            if cpu.running in jobs:
                jobs.remove(cpu.running)  # remove job and cpu
            else:
                cpus.append(cpu)

        # second, assign remaining tasks to free processors arbitrarily
        for cpu in cpus:
            if jobs:
                decision.append((jobs.pop(), cpu))
            else:
                decision.append((None, cpu))

        return decision

def pack_BFD(servers):
    """
    Best-Fit with servers inversely sorted by their utilization.
    """
    return pack_BF(sorted(servers, key=lambda x: x.utilization, reverse=True))

def pack_BF(servers):
    """
    Create a list of EDF Servers by packing servers. Best-Fit 
    packing algorithm.
    """

    # Find packed servers if there is one (EDFServer)
    packed_servers = []#[s for s in servers if s is EDFServer()]
    for server in servers:
        #Try to place the item in the fullest bin that will accommodate it, i.e., the one that will leave the least space remaining
        packed_servers.sort(key=lambda x: x.utilization, reverse=True)
        for p_server in packed_servers:
            if p_server.utilization + server.utilization <= 1:
                p_server.add_child(server)
                break
        else:
            p_server = EDFServer()
            p_server.add_child(server)
            packed_servers.append(p_server)

    return packed_servers
