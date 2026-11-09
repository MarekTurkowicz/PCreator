"""Tests for event counts grouped by logging level."""

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import count_events_by_level, create_schema, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402


def test_counts_group_all_levels_and_include_undated_events():
    levels = [
        "Warning", "Error", "Information", "Error", "Verbose",
        "Fatal", "Debug", "Information", "Information",
    ]
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, (LogEvent(level=level) for level in levels))

        assert count_events_by_level(connection) == [
            ("Debug", 1),
            ("Error", 2),
            ("Fatal", 1),
            ("Information", 3),
            ("Verbose", 1),
            ("Warning", 1),
        ]
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (9,)


def test_counts_return_no_rows_for_empty_database():
    with duckdb.connect() as connection:
        create_schema(connection)

        assert count_events_by_level(connection) == []
