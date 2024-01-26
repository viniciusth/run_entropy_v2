from ..entropy.analysis import entropy, HYPERPERIOD_LEN, K
from ..simso.sim_data import SimData
from src.simso.model_builder import ACETModelBuilder
import os


def entrypoint():
    builder = ACETModelBuilder()
    builder.add_cpu()
    builder.add_task(period=12, activation_date=0, wcet=8, deadline=12, proportion=0.5)
    builder.add_task(period=50, activation_date=0, wcet=8, deadline=50, proportion=0.5)
    builder.set_duration(HYPERPERIOD_LEN * K)
    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "REORDER.py")
    )
    model = builder.build()
    model.run_model()
    print(model.results.total_exceeded_count)
    data = SimData(model)
    hp = data.into_hyperperiods(HYPERPERIOD_LEN)
    # print(hp)
    print(entropy(hp))

    builder.set_scheduler(clas="simso.schedulers.EDF2")
    model = builder.build()
    model.run_model()
    print(model.results.total_exceeded_count)
    data = SimData(model)
    print(entropy(data.into_hyperperiods(HYPERPERIOD_LEN)))
