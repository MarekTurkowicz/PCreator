"""Store normalized log events in DuckDB."""

import json
import re
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path

import duckdb

from loglens.models import LogEvent

_LEVEL_RANKS = {
    level.lower(): rank
    for rank, level in enumerate(
        ("Verbose", "Debug", "Information", "Warning", "Error", "Fatal"), start=1
    )
}


def open_database(path: str | Path) -> duckdb.DuckDBPyConnection:
    """Open or create a persistent database and initialize its event schema.

    The caller owns the returned connection and must close it, for example by
    using it as a context manager. Existing events are preserved on reopening.
    The parent directory must already exist.
    """
    connection = duckdb.connect(str(path))
    try:
        create_schema(connection)
    except Exception:
        connection.close()
        raise
    return connection


def create_schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the events table on a caller-owned connection if it is absent.

    Timestamps retain their timezone semantics, arbitrary properties use JSON,
    and optional event fields may be NULL. Existing tables and rows are preserved.
    """
    schema = files("loglens").joinpath("sql/schema.sql").read_text(encoding="utf-8")
    connection.execute(schema)


def filter_events(
    connection: duckdb.DuckDBPyConnection,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    since: str | None = None,
    clock: Callable[[], datetime] | None = None,
    min_level: str | None = None,
) -> list[LogEvent]:
    """Return events in an inclusive time range, ordered by timestamp.

    Either bound may be omitted. Naive bounds mean UTC, like CLEF timestamps.
    Instead of start, since accepts a positive integer followed by s, m, h, d
    or w. Its lower bound is clock() minus that duration; the default clock is
    the current UTC time. Naive clock values also mean UTC. End is independent
    of the clock, and defaults to no upper bound.
    Undated events are returned last only when neither bound is supplied.
    min_level includes that severity and higher in Serilog order: Verbose,
    Debug, Information, Warning, Error, Fatal. Names are case-insensitive;
    unsupported names raise ValueError. None leaves severity unrestricted.
    The caller retains ownership of the connection.
    """
    minimum_rank = None
    if min_level is not None:
        if not isinstance(min_level, str) or min_level.lower() not in _LEVEL_RANKS:
            raise ValueError("min_level must be a standard Serilog level")
        minimum_rank = _LEVEL_RANKS[min_level.lower()]
    if since is not None:
        if start is not None:
            raise ValueError("since and start cannot be used together")
        match = re.fullmatch(r"([0-9]+)([smhdw])", since)
        if match is None:
            raise ValueError(
                "since must be a positive integer with unit s, m, h, d or w"
            )
        try:
            amount = int(match[1])
            if amount <= 0:
                raise ValueError("since must be positive")
            seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
            duration = timedelta(seconds=amount * seconds[match[2]])
        except (ValueError, OverflowError) as error:
            raise ValueError("since duration is invalid or out of range") from error
        now = clock() if clock is not None else datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        try:
            start = now.astimezone(timezone.utc) - duration
        except OverflowError as error:
            raise ValueError("since duration is out of range") from error
    if start is not None and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if start is not None and end is not None and start > end:
        raise ValueError("start must be before or equal to end")

    query = files("loglens").joinpath("sql/filter_events.sql").read_text(
        encoding="utf-8"
    )
    rows = connection.execute(
        query, [start, start, end, end, minimum_rank, minimum_rank]
    ).fetchall()
    return [
        LogEvent(
            timestamp=row[0].astimezone(timezone.utc) if row[0] is not None else None,
            level=row[1],
            message_template=row[2],
            message=row[3],
            exception=row[4],
            properties=json.loads(row[5]),
            source=row[6],
            line_number=row[7],
        )
        for row in rows
    ]


def insert_events(
    connection: duckdb.DuckDBPyConnection,
    events: Iterable[LogEvent],
    *,
    batch_size: int = 1000,
) -> int:
    """Append events to an existing schema and return the inserted count.

    Consume the iterable lazily, buffering at most batch_size rows. The caller
    owns the connection and transaction; completed batches may remain if a later
    batch fails outside a transaction.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    query = files("loglens").joinpath("sql/insert_events.sql").read_text(
        encoding="utf-8"
    )
    batch = []
    inserted = 0
    for event in events:
        batch.append(
            (
                event.timestamp,
                event.level,
                event.message_template,
                event.message,
                event.exception,
                json.dumps(event.properties),
                event.source,
                event.line_number,
            )
        )
        if len(batch) == batch_size:
            connection.executemany(query, batch)
            inserted += len(batch)
            batch.clear()

    if batch:
        connection.executemany(query, batch)
        inserted += len(batch)
    return inserted
