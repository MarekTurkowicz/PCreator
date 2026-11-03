"""Contract tests for the DuckDB event schema."""

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import create_schema  # noqa: E402


def test_schema_has_event_columns_and_types():
    with duckdb.connect() as connection:
        create_schema(connection)

        columns = connection.execute("DESCRIBE events").fetchall()

        assert [(column[0], column[1]) for column in columns] == [
            ("timestamp", "TIMESTAMP WITH TIME ZONE"),
            ("level", "VARCHAR"),
            ("message_template", "VARCHAR"),
            ("message", "VARCHAR"),
            ("exception", "VARCHAR"),
            ("properties", "JSON"),
            ("source", "VARCHAR"),
            ("line_number", "BIGINT"),
        ]


def test_schema_initializes_an_empty_database_and_can_be_repeated():
    with duckdb.connect() as connection:
        assert connection.execute("SHOW TABLES").fetchall() == []

        create_schema(connection)
        create_schema(connection)

        assert connection.execute("SHOW TABLES").fetchall() == [("events",)]
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (0,)
