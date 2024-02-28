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
- [x] Implementing REORDER with a simple EDF scheduler
- [x] Implementing entropy analysis and case generation
- [x] Add FG_RUN with delta
- [] Analyze results
