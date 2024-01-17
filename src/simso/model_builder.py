from typing import TypedDict
from typing_extensions import Unpack

from simso.configuration import Configuration
from simso.core import Model

class SchedulerParams(TypedDict):
  clas: str
  filename: str

class ModelBuilder:
  def __init__(self):
    self.config = Configuration()
    self.cur_task_id = 1
    self.cur_cpu_id = 1

  def add_task(self, period: int, activation_date: int, wcet: int, deadline: int):
    self.config.add_task(
      name=f"task_{self.cur_task_id}",
      identifier=self.cur_task_id,
      period=period,
      activation_date=activation_date,
      wcet=wcet,
      deadline=deadline
    )
    self.cur_task_id += 1

  def set_duration(self, duration: int):
    self.config.duration = duration * self.config.cycles_per_ms

  def add_cpu(self):
    self.config.add_processor(name=f"cpu_{self.cur_cpu_id}", identifier=self.cur_cpu_id)

  def set_scheduler(self, **kwargs: Unpack[SchedulerParams]):
    self.config.scheduler_info.clas = kwargs.get("clas")
    self.config.scheduler_info.filename = kwargs.get("filename")

  def build(self) -> Model:
    self.config.check_all()
    return Model(self.config)