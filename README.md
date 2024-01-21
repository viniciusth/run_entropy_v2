# RUN Entropy

### Setup project

```bash
chmod +x setup.sh
./setup.sh
```

or

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
- [] Implementing REORDER with a simple EDF scheduler
- [] Implementing entropy analysis and case generation
- [] Integrating REORDER scheduler with RUN
- [] Analyzing entropy of REORDER, RUN, REORDER + RUN.
