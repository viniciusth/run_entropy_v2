# RUN Entropy

### Setup project
Usage of python 3.7 is obligatory for GUI, unfortunately simsogui doesnt support newer versions of python.

```bash
chmod +x setup.sh
source ./setup.sh
```

or for windows (unmaintained)

```powershell
./setup.ps1
```

### Run Project

All commands are run from the root of the project.
```bash
python -m src.cli [OPTIONS] COMMAND [ARGS]...
```

Explore with
```bash
python -m src.cli --help
python -m src.cli COMMAND --help
```

### Generate task set, results and read results.
```bash
python -m src.cli generate-buckets
python -m src.cli generate-results
python -m src.cli read-results
```
This generates the tasksets as defined by the RUN-R paper, and generates the results for the tasksets.
The results are then read and displayed.

### Run Tests

All commands are run from the root of the project.
```bash
python -m unittest discover
```

### Result generation internals
The result generation writes snapshots into a file so the execution can be stopped at any moment, so if a crash occurs, the results are not lost.
Or if the user wants to stop the execution, the results are saved.

For speeding up the execution, the implementation uses multiprocessing and the number of processes can be set with the `THREAD_COUNT` variable.
There is a hard limit on the amount of in progress tasks which is currently statically set to 20, this is even more than should be needed but be mindful if your processor has more than 16 cores.
Also, to not keep saving the results to the savefile every time a result is generated, we run for `THREAD_COUNT*5` tasks before saving the current results to the savefile.

#### REORDER
The REORDER implementation is not in a perfect state, there are some issues that I couldn't figure out at the time.
My suggestion if you need to use REORDER would be reading the REORDER++ paper which came out on 2023 and implement that one instead, from scratch.

