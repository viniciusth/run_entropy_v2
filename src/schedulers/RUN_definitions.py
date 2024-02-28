from fractions import Fraction

INFINITO = 9000000000000

class _Server(object):
    """
    Abstract class that represents a Server.
    """
    next_id = 1

    def __init__(self, is_dual, task=None):
        self.parent = None
        self.is_dual = is_dual
        self.utilization = Fraction(0, 1)
        self.task = task
        self.job = None
        self.deadlines = [0]
        self.periodicity = []
        self.budget = 0
        self.next_deadline = 0
        self.last_release = 0

        self.dummyServer = False
        self.identifier = _Server.next_id
        _Server.next_id += 1
        if task:
            if hasattr(task, 'utilization'):
                self.utilization += task.utilization
            else:
                self.utilization += Fraction(task.wcet) / Fraction(task.period)

    def add_deadline(self, current_instant, deadline):
        """
        Add a deadline to this server.
        """

        self.deadlines.append(deadline)

        # save periodicity of this server
        if current_instant == 0:
            self.periodicity.append(deadline)

        self.deadlines = [d for d in self.deadlines if d > current_instant]
        self.next_deadline = min(self.deadlines)

    def create_job(self, sim, current_instant):
        """
        Replenish the budget.
        """

        self.budget = int(self.utilization * (self.next_deadline - current_instant))

class TaskServer(_Server):
    """
    A Task Server is a Server that contains a real Task.
    """
    def __init__(self, task):
        super(TaskServer, self).__init__(False, task)
        self.last_cpu = None


class EDFServer(_Server):
    """
    An EDF Server is a Server with multiple children scheduled with EDF.
    """
    def __init__(self):
        super(EDFServer, self).__init__(False)
        self.children = []

    def add_child(self, server):
        """
        Add a child to this EDFServer (used by the packing function).
        """
        self.children.append(server)
        self.utilization += server.utilization
        server.parent = self

class DualServer(_Server):
    """
    A Dual server is the opposite of its child.
    """
    def __init__(self, child):
        super(DualServer, self).__init__(True)
        self.child = child
        child.parent = self
        self.utilization = 1 - child.utilization

        self.dummyServer = child.dummyServer

def add_job(sim, job, server):
    """
    Recursively update the deadlines of the parents of server.
    """
    server.job = job
    while server:
        server.add_deadline(sim.now(), job.absolute_deadline *
                            sim.cycles_per_ms)
        server.create_job(sim, sim.now())
        server.last_release = sim.now()
        server = server.parent


def omega_t(servers, old, t):

    if not servers:
        return 0

    beta = sum([budget(s, old, t) for  s in servers])
    servers.sort(key=lambda s: deadline(s, t), reverse=False)

    """for s in servers:
        self.sim.logger.log("id={}, release {}, next_deadline {}, budget = {}".format(s.identifier, release(self, s, t),deadline(self, s, t), budget(self, s, old, t)))"""

    return max(0, servers[0].next_deadline - t - beta)

def release(server, t):
    if not server.periodicity:
        return server.last_release

    r = 0
    for p in server.periodicity:
        aux = int(t/p)*p
        if aux > r:
            r = aux
    return r

def deadline(server, t):
    if not server.periodicity:
        return server.next_deadline

    d = []
    for p in server.periodicity:
        aux = (int(t/p)+1)*p
        d.append(aux)

    return min(d)

def budget(server, old, t):
    if old != t and release(server,t) == release(server, old):
        return server.budget
    
    if old == t:
        return server.budget

    return int(server.utilization * (deadline(server, t) - release(server,t)))

def get_child_tasks(server):
    """
    Get the tasks scheduled by this server.
    """
    if server.task:
        return [server]
    else:
        if server.is_dual:
            return get_child_tasks(server.child)
        else:
            tasks = []
            for child in server.children:
                tasks += get_child_tasks(child)
            return tasks

def select_jobs(self, server, virtual, execute=True):
    """
    Select the jobs that should run according to RUN. The virtual jobs are
    appended to the virtual list passed as argument.
    """
    jobs = []
    if execute:
        virtual.append(server)

    # Leaves
    if server.task:
        #self.sim.logger.log("server {}, budget {}, next_deadline {}".format(server.identifier, server.budget, server.next_deadline))
        if execute and server.budget > 0:

            # select a dummy job
            if server.job is None:
               jobs.append(server)
               #self.sim.logger.log("SELEECT dummy".format())
            #select a real job
            elif server.job.is_active():
                jobs.append(server)
                #self.sim.logger.log("SELEECT {}".format(server.identifier))
            
    else:
        # Rule 2
        if server.is_dual:
            #if execute:
            #self.sim.logger.log("DualServer{}: BUDGET = {}, deadline = {}".format(server.identifier, server.budget, server.next_deadline))
            jobs += select_jobs(self, server.child, virtual, not execute)
        # Rule 1
        else:
            active_servers = [s for s in server.children if s.budget > 0]
            if active_servers:
                min_server = min(active_servers, key=lambda s: s.next_deadline)

                if self.is_idle and server == self.root:
                    min_server = [s for s in active_servers if s.dummyServer][0]
                    
                #if min_server.dummyServer and server == self.root:
                #    self.is_idle = True
            else:
                min_server = None
            
            for child in server.children:
                jobs += select_jobs(self, child, virtual,
                                    execute and child is min_server)
    return jobs

def delta_t(u, servers, old, t):
    #self.sim.logger.log("delta_t".format())

    #servers = update_times(self, servers)

    #servers = [s for s in servers if s.utilization > 0]

    if not servers or u > 0.95:
        return 0


    servers.sort(key=lambda s: deadline(s, t), reverse=False)
    
    """for s in servers:
        self.sim.logger.log("id={}, release {}, next_deadline {}, budget = {}".format(s.identifier, release(self, s, t),deadline(self, s, t), budget(self, s, old, t)))
    """

    # get the biggest deadline
    delta = deadline(servers[len(servers)-1], t) - t
    #delta = servers[len(servers)-1].next_deadline  
    
    #self.sim.logger.log("start delta = {}".format(delta))

    for j in range(0, len(servers)):
        
        d = deadline(servers[j], t)
        c = 0
        #self.sim.logger.log("j = {}, dj = {}, t = {}".format(servers[j].identifier, d, t))
        #self.sim.logger.log("---------".format())
        for i in range(0, j+1):

            ri = deadline(servers[i], t) #D(self, servers[i], t)
            di = release(servers[i], d) #R(self, servers[i], d, t)
            #self.sim.logger.log("i = {}, dj = {}, ri = {}, di = {}".format(servers[i].identifier, d, ri, di))

            c = c + budget(servers[i], old, t) + float(di - ri)*servers[i].utilization
            #self.sim.logger.log("c = {}, ci = {}, eita = {}, u = {}".format(c, budget(self, servers[i], old, t), float(di - ri)*servers[i].utilization, servers[i].utilization))
            #self.sim.logger.log("---------".format())

        delta = min(delta, (d - t - c))
        #self.sim.logger.log("delta = {}, dj-t-c = {}".format(delta, (d - t - c)))
        if delta <= 0:
            return 0

    return int(delta)
