"""Command-line entry point for LogLens."""

from pathlib import Path
from typing import Annotated

import typer

from loglens import __version__
from loglens.clef import parse_line
from loglens.discovery import find_log_files

app = typer.Typer(help="Analyze Serilog CLEF logs.")


@app.callback()
def main() -> None:
    """Analyze Serilog CLEF logs."""


@app.command()
def version() -> None:
    """Print the installed LogLens version."""
    typer.echo(__version__)


@app.command()
def inspect(
    directory: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, readable=True)
    ],
) -> None:
    """Count valid and invalid CLEF events in a directory's log files."""
    valid = invalid = 0
    try:
        for path in find_log_files(directory):
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    try:
                        parse_line(line)
                    except ValueError:
                        invalid += 1
                    else:
                        valid += 1
    except (OSError, UnicodeError) as error:
        typer.echo(f"Cannot inspect logs: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Valid events: {valid}")
    typer.echo(f"Invalid events: {invalid}")
