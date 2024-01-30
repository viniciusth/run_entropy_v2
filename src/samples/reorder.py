from ..entropy.case_gen import gen_tasks
from ..entropy.analysis import entropy, HYPERPERIOD_LEN, K
from ..simso.sim_data import SimData
from src.simso.model_builder import ACETModelBuilder
import os
import random


def entrypoint(utilization: float):
    builder = ACETModelBuilder()
    builder.add_cpu()

    task_amount = random.randint(3, 10)
    tasks = gen_tasks(task_amount, utilization)
    for task in tasks:
        builder.add_task(**task)
    # print(tasks)

    # builder.add_task(
    #     period=50,
    #     deadline=50,
    #     activation_date=0,
    #     proportion=0.5,
    #     wcet=9,
    # )
    # builder.add_task(
    #     period=10,
    #     deadline=10,
    #     activation_date=0,
    #     proportion=0.5,
    #     wcet=1,
    # )
    # builder.add_task(
    #     period=10,
    #     deadline=10,
    #     activation_date=0,
    #     proportion=0.5,
    #     wcet=5,
    # )

    builder.set_duration(HYPERPERIOD_LEN * K)

    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "REORDER.py")
    )

    rerun_model = builder.build()
    rerun_model.run_model()

    rerun_data = SimData(rerun_model)
    rerun_hp = rerun_data.into_hyperperiods(HYPERPERIOD_LEN)
    rerun_entropy = entropy(rerun_hp)

    builder.set_scheduler(clas="simso.schedulers.EDF2")
    edf_model = builder.build()
    edf_model.run_model()

    edf_data = SimData(edf_model)
    edf_hp = edf_data.into_hyperperiods(HYPERPERIOD_LEN)
    edf_entropy = entropy(edf_hp)

    assert (
        rerun_model.results.total_exceeded_count
        == edf_model.results.total_exceeded_count
        == 0
    )
    print(rerun_entropy, edf_entropy)
