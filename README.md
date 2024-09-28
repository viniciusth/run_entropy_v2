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

### Run Tests

All commands are run from the root of the project.
```bash
python -m unittest discover
```


### Steps to follow
- [x] Implementing REORDER with a simple EDF scheduler
- [x] Implementing entropy analysis and case generation
- [x] Add FG_RUN with delta
- [x] Analyze results
- [x] Implement Multiprocessor REORDER via partitioning (already done by simso)
- [x] Create tasksets with different number of processors/utilizations
- [] Generate results and save data
- [] Analyze results, create graphs and tables
