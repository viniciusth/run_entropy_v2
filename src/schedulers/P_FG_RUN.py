from simso.schedulers import scheduler
from simso.utils import PartitionedScheduler
from simso.core.Scheduler import SchedulerInfo
from simso.utils.PartitionedScheduler import decreasing_first_fit


@scheduler("src.schedulers.P_FG_RUN")
class P_FG_RUN(PartitionedScheduler):
    def init(self): # type: ignore
        PartitionedScheduler.init(
            self, SchedulerInfo("src.schedulers.FG_RUN"), decreasing_first_fit
        )
