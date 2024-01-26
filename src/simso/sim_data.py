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

    def into_hyperperiods(self, hyperperiod_len: int):
        """
        Returns a list of processor executions, where each execution is split into hyperperiods of length hyperperiod_len.
        """
        executions = []
        for processor in self.processor_executions:
            hyperperiods = []
            cur_hyperperiod = 0
            for start, end, task in processor:
                assert end - start + 1 <= hyperperiod_len, "Hyperperiod too short"

                if start >= cur_hyperperiod:
                    hyperperiods.append([0] * hyperperiod_len)
                    cur_hyperperiod += hyperperiod_len

                for i in range(start, min(end, cur_hyperperiod)):
                    hyperperiods[-1][i % hyperperiod_len] = task

                if end >= cur_hyperperiod:
                    hyperperiods.append([0] * hyperperiod_len)
                    for i in range(cur_hyperperiod, end):
                        hyperperiods[-1][i % hyperperiod_len] = task
                    cur_hyperperiod += hyperperiod_len
            executions.append(hyperperiods)
        return executions
