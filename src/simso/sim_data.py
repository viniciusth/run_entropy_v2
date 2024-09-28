from simso.core import Model, ProcEvent

from src.entropy.analysis import K


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
        all_empty = True
        for processor in self.processor_executions:
            hyperperiods = []
            cur_hyperperiod_end = 0
            assert sorted(processor, key=lambda x: x[0]) == processor, "Processor not sorted"
            for start, end, task in processor:
                assert end - start + 1 <= hyperperiod_len, "Hyperperiod too short"
                if start == end:
                    continue

                while start >= cur_hyperperiod_end:
                    hyperperiods.append([0 for _ in range(hyperperiod_len)])
                    cur_hyperperiod_end += hyperperiod_len

                for i in range(start, min(end, cur_hyperperiod_end)):
                    hyperperiods[-1][i % hyperperiod_len] = task

                if end > cur_hyperperiod_end:
                    hyperperiods.append([0 for _ in range(hyperperiod_len)])
                    for i in range(cur_hyperperiod_end, end):
                        hyperperiods[-1][i % hyperperiod_len] = task
                    cur_hyperperiod_end += hyperperiod_len
            diff = K - len(hyperperiods)
            if diff > 0:
                hyperperiods += [[0 for _ in range(hyperperiod_len)] for _ in range(diff)]
            else:
                all_empty = False

            assert len(hyperperiods) == K, f"Expected {K} hyperperiods, got {len(hyperperiods)}"
            executions.append(hyperperiods)
        if all_empty:
            print("All processors are empty, skipping invalid taskset")
            return None
        return executions
