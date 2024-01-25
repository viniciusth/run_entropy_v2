from ..simso.sim_data import SimData
from src.simso.model_builder import ACETModelBuilder
import os


def entrypoint():
    builder = ACETModelBuilder()
    builder.add_cpu()
    builder.add_task(period=80, activation_date=0, wcet=50, deadline=80, acet=30)
    builder.add_task(period=150, activation_date=0, wcet=50, deadline=150, acet=40)
    builder.set_duration(1000)
    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "REORDER.py")
    )
    model = builder.build()
    model.run_model()
    print(model.results.total_exceeded_count)
    data = SimData(model)
    # print(model.logs)
