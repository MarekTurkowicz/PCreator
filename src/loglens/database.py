"""Initialize storage for normalized log events in DuckDB."""

from importlib.resources import files

import duckdb


def create_schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the events table on a caller-owned connection if it is absent.

    Timestamps retain their timezone semantics, arbitrary properties use JSON,
    and optional event fields may be NULL. Existing tables and rows are preserved.
    """
    schema = files("loglens").joinpath("sql/schema.sql").read_text(encoding="utf-8")
    connection.execute(schema)
