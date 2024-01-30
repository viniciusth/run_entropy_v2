import typer
from src.data.gen_buckets import gen_buckets
import src.samples.reorder as reorder
import logging

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def run_sample(
    name: str = typer.Argument(None),
    utilization: float = typer.Option(0.5, "--utilization", "-u"),
):
    if name is None or name.lower() == "testing":
        reorder.entrypoint(utilization)


@app.command()
def run_analysis():
    pass


@app.command()
def generate_buckets(file_path: str = typer.Option(None, "--file-path", "-f")):
    gen_buckets(file_path)


@app.command()
def compute_results():
    pass


@app.callback()
def main(debug: bool = typer.Option(False, "--debug", "-d")):
    if debug:
        print("Debug mode on")
        logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    app()
