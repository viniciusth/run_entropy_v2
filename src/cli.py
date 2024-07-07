import typer
from src.data.gen_buckets import gen_buckets
from src.data.gen_results import gen_results
import src.samples.reorder as reorder
import logging

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def run_sample(
    name: str = typer.Argument(None),
    utilization: float = typer.Option(0.5, "--utilization", "-u"),
    processors: int = typer.Option(1, "--processors", "-p"),
):
    if name is None or name.lower() == "testing":
        reorder.entrypoint(utilization, processors)


@app.command()
def generate_results(file_path: str = typer.Option("buckets.json", "--file-path", "-f")):
    """
    Generates results given a file path with the buckets.
    It will generate a file `{file}_partial.json` with partial results so computation can be resumed if needed.
    The final file will be named `{file}_results.json`
    """
    gen_results(file_path)



@app.command()
def generate_buckets(file_path: str = typer.Option("buckets.json", "--file-path", "-f")):
    gen_buckets(file_path)


@app.callback()
def main(debug: bool = typer.Option(False, "--debug", "-d")):
    if debug:
        print("Debug mode on")
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
