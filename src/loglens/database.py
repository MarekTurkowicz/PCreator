"""Store normalized log events in DuckDB."""

import json
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path

import duckdb

from loglens.models import LogEvent


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
