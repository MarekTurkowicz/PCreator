"""Request counts and error fractions grouped by HTTP endpoint."""

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import count_requests_by_endpoint, create_schema, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402


def test_endpoint_counts_and_error_fractions():
    events = [
        LogEvent(level=level, properties={"RequestPath": path})
        for path, level in [
            ("/orders", "Information"),
            ("/orders", "Error"),
            ("/orders", "Fatal"),
            ("/health", "Warning"),
            ("/failed", "Error"),
            ("/failed", "Fatal"),
        ]
    ]
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, events)

        assert count_requests_by_endpoint(connection) == [
            ("/failed", 2, 1.0),
            ("/health", 1, 0.0),
            ("/orders", 3, pytest.approx(2 / 3)),
        ]


def test_empty_database_has_no_endpoint_counts():
    with duckdb.connect() as connection:
        create_schema(connection)

        assert count_requests_by_endpoint(connection) == []


def test_invalid_paths_are_ignored_and_valid_paths_preserved():
    properties = [
        {}, {"RequestPath": None}, {"RequestPath": ""},
        {"RequestPath": " \t\n"}, {"RequestPath": 123},
        {"RequestPath": False}, {"RequestPath": []}, {"RequestPath": {}},
        {"Http": {"RequestPath": "/nested"}},
        {"RequestPath": " /quoted'path "},
    ]
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, (LogEvent(properties=p) for p in properties))

        assert count_requests_by_endpoint(connection) == [(" /quoted'path ", 1, 0.0)]
