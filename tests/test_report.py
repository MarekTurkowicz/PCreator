"""Report statistics for a selected time range."""

from datetime import datetime, timedelta, timezone

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import create_schema, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402
from loglens.report import EndpointStats, build_report  # noqa: E402


@pytest.fixture
def report_data():
    start = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)
    exception = "System.InvalidOperationException: Request failed"
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(
            connection,
            [
                LogEvent(start, properties={"RequestPath": "/api", "Elapsed": 10}),
                LogEvent(
                    end,
                    "Error",
                    exception=exception,
                    properties={"RequestPath": "/api", "Elapsed": 10},
                ),
                LogEvent(
                    end, "Warning", properties={"RequestPath": "/missing-duration"}
                ),
                LogEvent(end, "Fatal"),
                LogEvent(
                    start - timedelta(microseconds=1),
                    "Error",
                    exception=exception,
                    properties={"RequestPath": "/api", "Elapsed": 1000},
                ),
                LogEvent(end + timedelta(microseconds=1), "Error", exception=exception),
                LogEvent(level="Error", exception=exception),
            ],
        )
        yield connection, start, end


def test_build_report_combines_statistics_for_inclusive_bounds(report_data):
    connection, start, end = report_data

    report = build_report(connection, start=start, end=end)

    assert report.total_events == 4
    assert report.level_counts == (
        ("Error", 1),
        ("Fatal", 1),
        ("Information", 1),
        ("Warning", 1),
    )
    assert report.endpoints == (
        EndpointStats("/api", 2, 0.5, 10, 10, 10),
        EndpointStats("/missing-duration", 1, 0, None, None, None),
    )
    assert report.errors_by_time == ((end, 2),)
    (group,) = report.exception_groups
    assert group.signature == ("System.InvalidOperationException", "Request failed")
    assert (group.count, group.first_seen, group.last_seen) == (1, end, end)
    assert build_report(connection).total_events == 7


def test_build_report_for_empty_range(report_data):
    connection, _, end = report_data

    report = build_report(connection, start=end + timedelta(days=1))

    assert report.total_events == 0
    assert report.level_counts == ()
    assert report.endpoints == ()
    assert report.errors_by_time == ()
    assert report.exception_groups == ()


def test_build_report_with_relative_lower_bound(report_data):
    connection, start, end = report_data

    relative = build_report(connection, since="1m", clock=lambda: end, end=end)

    assert relative == build_report(connection, start=start, end=end)
