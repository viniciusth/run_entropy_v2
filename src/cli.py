import typer
from src.data.analysis import run_analysis
from src.data.gen_buckets import gen_buckets
from src.data.gen_results import gen_results
from src.samples import tables
import src.samples.reorder as reorder
import logging
import simsogui

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def run_sample(
    name: str = typer.Argument(None),
    utilization: float = typer.Option(0.5, "--utilization", "-u"),
    processors: int = typer.Option(1, "--processors", "-p"),
):
    if name is None or name.lower() == "testing":
        reorder.entrypoint(utilization, processors)
    if name == "tables":
        print("Running tables")
        tables.entrypoint()



@app.command()
def generate_results(file_path: str = typer.Option("buckets.json", "--file-path", "-f")):
    """
    Generates results given a file path with the buckets.
    It will generate a file `{file}_partial.json` with partial results so computation can be resumed if needed.
    The final file will be named `{file}_results.json`
    """
    gen_results(file_path)

@app.command()
def read_results(file_path: str = typer.Option("buckets_results.json", "--file-path", "-f")):
    """
    Reads the results from a file and prints them.
    """
    run_analysis(file_path)


@app.command()
def generate_buckets(file_path: str = typer.Option("buckets.json", "--file-path", "-f")):
    gen_buckets(file_path)

@app.command()
def gui():
    simsogui.run_gui()

@app.callback()
def main(debug: bool = typer.Option(False, "--debug", "-d")):
    if debug:
        print("Debug mode on")
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
