from imp import os

from src.entropy.analysis import entropy
from ..simso.sim_data import SimData
from src.simso.model_builder import ACETModelBuilder

def entrypoint():
    tasks = [
        {"period": 5, "deadline": 5, "activation_date": 0, "proportion": 0.5, "wcet": 2},
        {"period": 10, "deadline": 10, "activation_date": 0, "proportion": 0.5, "wcet": 1},
        {"period": 20, "deadline": 20, "activation_date": 0, "proportion": 0.5, "wcet": 2},
    ]
    builder = ACETModelBuilder()
    for _ in range(1):
        builder.add_cpu()

    for task in tasks:
        builder.add_task(**task)
    builder.set_duration(200) # 10 hyperperiods

    do_edf(builder)
    do_reorder(builder)
    do_run(builder)
    do_runr(builder)

def do_edf(builder):
    builder.set_scheduler(clas="simso.schedulers.P_EDF")
    model = builder.build()
    model.run_model()

    sim_data = SimData(model)
    hyperperiods = sim_data.into_hyperperiods(20, 10)
    assert hyperperiods is not None

    print("EDF")
    for cpu in hyperperiods:
        for hp in cpu:
            # print as , separated
            print(",".join(str(x) for x in hp)+",")
    entropy_val = entropy(hyperperiods, 3, 1, 10, 20)
    print("Entropy: ", entropy_val)

def do_reorder(builder):
    builder.set_scheduler(filename=os.path.join(os.getcwd(), "src", "schedulers", "P_REORDER.py"))
    model = builder.build()
    model.run_model()

    sim_data = SimData(model)
    hyperperiods = sim_data.into_hyperperiods(20, 10)
    assert hyperperiods is not None

    print("REORDER")
    for cpu in hyperperiods:
        for hp in cpu:
            # print as , separated
            print(",".join(str(x) for x in hp)+",")

    entropy_val = entropy(hyperperiods, 3, 1, 10, 20)
    print("Entropy: ", entropy_val)

def do_run(builder):
    builder.set_scheduler(clas="simso.schedulers.RUN")
    model = builder.build()
    model.run_model()

    sim_data = SimData(model)
    hyperperiods = sim_data.into_hyperperiods(20, 10)
    assert hyperperiods is not None

    print("RUN")
    for cpu in hyperperiods:
        for hp in cpu:
            # print as , separated
            print(",".join(str(x) for x in hp)+",")

    entropy_val = entropy(hyperperiods, 3, 1, 10, 20)
    print("Entropy: ", entropy_val)


def do_runr(builder):
    builder.set_scheduler(filename=os.path.join(os.getcwd(), "src", "schedulers", "RUN_RANDOM.py"))
    model = builder.build()
    model.run_model()

    sim_data = SimData(model)
    hyperperiods = sim_data.into_hyperperiods(20, 10)
    assert hyperperiods is not None

    print("RUN_RANDOM")
    for cpu in hyperperiods:
        for hp in cpu:
            # print as , separated
            print(",".join(str(x) for x in hp)+",")

    entropy_val = entropy(hyperperiods, 3, 1, 10, 20)
    print("Entropy: ", entropy_val)

