from simso.configuration import Configuration
from simso.core import Model

class ACETModelBuilder:
    def __init__(self):
        self.config = Configuration()
        self.config.etm = "pacet"
        self.cur_task_id = 1
        self.cur_cpu_id = 1

    def add_task(self, **kwargs):
        self.config.add_task(
            name=f"task_{self.cur_task_id}",
            identifier=self.cur_task_id,
            period=kwargs.get("period"),
            activation_date=kwargs.get("activation_date"),
            wcet=kwargs.get("wcet"),
            deadline=kwargs.get("deadline"),
            et_stddev=kwargs.get("proportion"),  # type: ignore
        )
        self.cur_task_id += 1

    def set_duration(self, duration: int):
        self.config.duration = duration * self.config.cycles_per_ms

    def add_cpu(self):
        self.config.add_processor(
            name=f"cpu_{self.cur_cpu_id}", identifier=self.cur_cpu_id
        )
        self.cur_cpu_id += 1

    def set_scheduler(self, **kwargs):
        self.config.scheduler_info.clas = kwargs.get("clas")  # type: ignore
        self.config.scheduler_info.filename = kwargs.get("filename")  # type: ignore

    def build(self) -> Model:
        self.config.check_all()
        return Model(self.config)
