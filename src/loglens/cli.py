"""Command-line entry point for LogLens."""

from pathlib import Path
from typing import Annotated

import typer

from loglens import __version__
from loglens.clef import parse_line, read_files
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


@app.command()
def ingest(
    directory: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, readable=True)
    ],
    database: Annotated[Path, typer.Argument(help="Destination DuckDB file.")],
) -> None:
    """Append a directory's log events to DuckDB, skipping malformed lines."""
    import duckdb

    from loglens.database import insert_events, open_database

    try:
        paths = find_log_files(directory)
        with open_database(database) as connection:
            inserted = insert_events(connection, read_files(paths, strict=False))
    except (OSError, UnicodeError, duckdb.Error) as error:
        typer.echo(f"Cannot ingest logs: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Inserted events: {inserted}")


@app.command()
def stats(
    database: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
) -> None:
    """Show level counts and endpoint statistics from an ingested DuckDB file."""
    import duckdb

    from loglens.database import (
        count_events_by_level,
        count_requests_by_endpoint,
        response_time_percentiles_by_endpoint,
    )

    try:
        with duckdb.connect(str(database), read_only=True) as connection:
            levels = count_events_by_level(connection)
            endpoints = count_requests_by_endpoint(connection)
            durations = {
                path: values
                for path, *values in response_time_percentiles_by_endpoint(connection)
            }
    except (OSError, duckdb.Error) as error:
        typer.echo(f"Cannot read statistics: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("Levels\nLevel\tEvents")
    for level, count in levels:
        typer.echo(f"{level}\t{count}")
    if not levels:
        typer.echo("No data.")

    typer.echo(
        "\nEndpoints\nEndpoint\tRequests\tError rate\tp50 (ms)\tp95 (ms)\tp99 (ms)"
    )
    for path, count, error_rate in endpoints:
        values = durations.get(path)
        percentiles = (
            "\t".join(f"{value:.2f}" for value in values) if values else "-\t-\t-"
        )
        typer.echo(f"{path}\t{count}\t{error_rate:.2%}\t{percentiles}")
    if not endpoints:
        typer.echo("No data.")


@app.command()
def errors(
    database: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    limit: Annotated[int, typer.Option(min=1, help="Maximum number of groups.")] = 10,
) -> None:
    """Show the most frequent exception groups and an example per group."""
    import duckdb

    from loglens.database import filter_events
    from loglens.exceptions import group_exceptions, summarize_exception_groups

    try:
        with duckdb.connect(str(database), read_only=True) as connection:
            groups = group_exceptions(filter_events(connection))
    except (OSError, duckdb.Error) as error:
        typer.echo(f"Cannot read exceptions: {error}", err=True)
        raise typer.Exit(code=1) from error

    if not groups:
        typer.echo("No exceptions.")
        return

    for summary in summarize_exception_groups(groups)[:limit]:
        exception_type, message = summary.signature
        signature = ": ".join(part for part in (exception_type, message) if part)
        first_seen = summary.first_seen.isoformat() if summary.first_seen else "-"
        last_seen = summary.last_seen.isoformat() if summary.last_seen else "-"
        example = groups[summary.signature][0].exception
        typer.echo(
            f"{signature}\nOccurrences: {summary.count}\n"
            f"First seen: {first_seen}\nLast seen: {last_seen}\n"
            f"Example:\n{example}\n"
        )


@app.command()
def trace(
    database: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    correlation_id: Annotated[str, typer.Argument(help="Request CorrelationId.")],
) -> None:
    """Show events for one request in chronological order."""
    import duckdb

    from loglens.database import find_events_by_correlation_id

    try:
        with duckdb.connect(str(database), read_only=True) as connection:
            events = find_events_by_correlation_id(connection, correlation_id)
    except (OSError, duckdb.Error) as error:
        typer.echo(f"Cannot read trace: {error}", err=True)
        raise typer.Exit(code=1) from error

    if not events:
        typer.echo("No matching events.")
        return

    typer.echo("Timestamp\tLevel\tMessage")
    for event in events:
        timestamp = event.timestamp.isoformat() if event.timestamp is not None else "-"
        message = event.message if event.message is not None else event.message_template
        typer.echo(f"{timestamp}\t{event.level}\t{message}")


@app.command()
def report(
    directory: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, readable=True)
    ],
    since: Annotated[
        str | None, typer.Option(help="Include events since a relative time, e.g. 2h.")
    ] = None,
    out: Annotated[
        Path | None, typer.Option(dir_okay=False, help="Write Markdown to this file.")
    ] = None,
) -> None:
    """Generate a Markdown report from a directory's CLEF logs."""
    import duckdb

    from loglens.database import create_schema, insert_events
    from loglens.report import build_report, render_markdown

    try:
        paths = find_log_files(directory)
        with duckdb.connect() as connection:
            create_schema(connection)
            insert_events(connection, read_files(paths, strict=False))
            markdown = render_markdown(build_report(connection, since=since))
        if out is not None:
            out.write_text(markdown, encoding="utf-8")
        else:
            typer.echo(markdown, nl=False)
    except (OSError, ValueError, duckdb.Error) as error:
        typer.echo(f"Cannot generate report: {error}", err=True)
        raise typer.Exit(code=1) from error
