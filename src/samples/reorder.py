from ..entropy.case_gen import gen_tasks
from ..entropy.analysis import entropy, HYPERPERIOD_LEN, K
from ..simso.sim_data import SimData
from src.simso.model_builder import ACETModelBuilder
import os
import random


def entrypoint(utilization: float, processors: int):
    builder = ACETModelBuilder()

    for _ in range(processors):
        builder.add_cpu()

    task_amount = random.randint(processors + 2, 3 * processors)
    tasks = gen_tasks(task_amount, utilization)
    for task in tasks:
        builder.add_task(**task)
    builder.set_duration(HYPERPERIOD_LEN * K)

    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "P_REORDER.py")
    )  # type: ignore

    rerun_model = builder.build()
    rerun_model.run_model()

    rerun_data = SimData(rerun_model)
    rerun_hp = rerun_data.into_hyperperiods(HYPERPERIOD_LEN)
    rerun_entropy = entropy(rerun_hp, task_amount, processors)

    builder.set_scheduler(clas="simso.schedulers.P_EDF")  # type: ignore
    edf_model = builder.build()
    edf_model.run_model()

    edf_data = SimData(edf_model)
    edf_hp = edf_data.into_hyperperiods(HYPERPERIOD_LEN)
    edf_entropy = entropy(edf_hp, task_amount, processors)

    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "FG_RUN.py")
    )  # type: ignore
    fgrun_model = builder.build()
    fgrun_model.run_model()
    fgrun_data = SimData(fgrun_model)
    fgrun_hp = fgrun_data.into_hyperperiods(HYPERPERIOD_LEN)
    fgrun_entropy = entropy(fgrun_hp, task_amount, processors)
    assert (
        rerun_model.results.total_exceeded_count  # type: ignore
        == edf_model.results.total_exceeded_count  # type: ignore
        == fgrun_model.results.total_exceeded_count  # type: ignore
        == 0
    ), "Exceeded count is not 0: {} {} {}".format(
        rerun_model.results.total_exceeded_count,  # type: ignore
        edf_model.results.total_exceeded_count,  # type: ignore
        fgrun_model.results.total_exceeded_count,  # type: ignore
    )

    print(rerun_entropy, edf_entropy, fgrun_entropy)
