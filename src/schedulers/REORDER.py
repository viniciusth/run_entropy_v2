from simso.core import Scheduler


class REORDER(Scheduler):
    def init(self):
        print(self.task_list)
        pass

    def on_activate(self, job):
        pass

    def on_terminated(self, job):
        pass

    def schedule(self, cpu):
        pass
