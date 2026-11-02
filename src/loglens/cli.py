"""Command-line entry point for LogLens."""

import typer

from loglens import __version__

app = typer.Typer(help="Analyze Serilog CLEF logs.")


@app.callback()
def main() -> None:
    """Analyze Serilog CLEF logs."""


@app.command()
def version() -> None:
    """Print the installed LogLens version."""
    typer.echo(__version__)
