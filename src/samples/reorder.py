from src.simso.model_builder import ACETModelBuilder
import os


def entrypoint():
    builder = ACETModelBuilder()
    builder.add_cpu()
    builder.add_task(period=100, activation_date=0, wcet=50, deadline=100, acet=30)
    builder.add_task(period=200, activation_date=0, wcet=50, deadline=200, acet=40)
    builder.set_duration(1000)
    builder.set_scheduler(
        filename=os.path.join(os.getcwd(), "src", "schedulers", "REORDER.py")
    )
    model = builder.build()
    model.run_model()
    print(model.results.total_exceeded_count)
