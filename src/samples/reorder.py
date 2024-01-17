from src.simso.model_builder import ModelBuilder
import os

def entrypoint():
    builder = ModelBuilder()
    builder.add_cpu()
    builder.add_task(100, 0, 50, 100)
    builder.add_task(200, 0, 50, 200)
    builder.set_duration(1000)
    builder.set_scheduler(filename=os.path.join(os.getcwd(), "src", "schedulers", "REORDER.py"))
    model = builder.build()
    model.run_model()