from simso.schedulers import scheduler
from simso.utils import PartitionedScheduler
from simso.core.Scheduler import SchedulerInfo
from simso.utils.PartitionedScheduler import decreasing_first_fit


@scheduler("src.schedulers.P_REORDER")
class P_REORDER(PartitionedScheduler):
    def init(self): # type: ignore
        PartitionedScheduler.init(
            self, SchedulerInfo("src.schedulers.REORDER"), decreasing_first_fit
        )
