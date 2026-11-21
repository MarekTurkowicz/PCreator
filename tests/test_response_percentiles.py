"""Response duration percentiles grouped by HTTP endpoint."""

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import (  # noqa: E402
    create_schema,
    insert_events,
    response_time_percentiles_by_endpoint,
)
from loglens.models import LogEvent  # noqa: E402


def test_known_durations_use_linear_interpolation_and_group_by_endpoint():
    events = [
        LogEvent(properties={"RequestPath": "/orders", "Elapsed": elapsed})
        for elapsed in [100, 0, 30, 10, 90, 40, 80, 20, 60, 70, 50]
    ]
    events.append(LogEvent(properties={"RequestPath": "/health", "Elapsed": 2.5}))
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, events)

        assert response_time_percentiles_by_endpoint(connection) == [
            ("/health", 2.5, 2.5, 2.5),
            ("/orders", 50.0, 95.0, 99.0),
        ]


def test_invalid_durations_and_paths_do_not_contribute():
    properties = [
        {"RequestPath": "/valid", "Elapsed": value}
        for value in [None, -1, True, "42", [], {}, float("inf"), float("nan")]
    ]
    properties.extend(
        {"RequestPath": path, "Elapsed": 500}
        for path in [None, "", " \t\n", 12, False, [], {}]
    )
    properties.extend([
        {"RequestPath": "/missing"},
        {"Elapsed": 500},
        {"RequestPath": " /quoted'path ", "Elapsed": 0},
        {"RequestPath": "/valid", "Elapsed": 10},
        {"RequestPath": "/valid", "Elapsed": 20},
    ])
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, (LogEvent(properties=p) for p in properties))

        results = response_time_percentiles_by_endpoint(connection)
        assert [row[0] for row in results] == [" /quoted'path ", "/valid"]
        assert results[0][1:] == pytest.approx((0.0, 0.0, 0.0))
        assert results[1][1:] == pytest.approx((15.0, 19.5, 19.9))


def test_empty_database_has_no_response_percentiles():
    with duckdb.connect() as connection:
        create_schema(connection)

        assert response_time_percentiles_by_endpoint(connection) == []
