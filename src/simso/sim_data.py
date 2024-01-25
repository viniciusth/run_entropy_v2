from simso.core import Model, ProcEvent


class SimData:
    """
    Extracts information from the model, should be constructed after the model has been run.
    """

    def __init__(self, model: Model):
        c = model.cycles_per_ms
        self.processor_executions = []
        for processor in model.processors:
            last_task = None
            computed = []
            for evt in processor.monitor:
                if evt[1].event == ProcEvent.RUN:
                    assert last_task is None
                    last_task = (evt[0], evt[1].args.task.identifier)
                elif evt[1].event == ProcEvent.OVERHEAD and last_task is not None:
                    computed.append((last_task[0] // c, evt[0] // c, last_task[1]))
                    last_task = None

            if last_task is not None:
                computed.append((last_task[0] // c, model.now() // c, last_task[1]))

            self.processor_executions.append(computed)
        print(self.processor_executions)
