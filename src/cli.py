import typer
import src.samples.reorder as reorder

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def run_sample(name: str = typer.Argument(None)):
    if name is None or name.lower() == "testing":
        reorder.entrypoint()


@app.command()
def run_analysis():
    pass


if __name__ == "__main__":
    app()
