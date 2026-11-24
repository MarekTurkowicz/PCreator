"""Report statistics for a selected time range."""

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest

from loglens.models import LogEvent
from loglens.report import (
    EndpointStats,
    Report,
    build_report,
    render_csv,
    render_markdown,
)


@pytest.fixture
def report_data():
    duckdb = pytest.importorskip("duckdb")
    from loglens.database import create_schema, insert_events

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


def test_render_markdown_formats_summary_and_endpoint_tables():
    report = Report(
        total_events=4,
        level_counts=(("Error", 1), ("Fatal", 1), ("Information", 1), ("Warning", 1)),
        endpoints=(
            EndpointStats("/api", 2, 0.5, 10, 10, 10),
            EndpointStats("/missing-duration", 1, 0, None, None, None),
        ),
        errors_by_time=(),
        exception_groups=(),
    )

    assert render_markdown(report) == (
        "# LogLens report\n\n"
        "## Summary\n\n"
        "Total events: 4\n\n"
        "| Level | Events |\n"
        "| --- | ---: |\n"
        "| Error | 1 |\n"
        "| Fatal | 1 |\n"
        "| Information | 1 |\n"
        "| Warning | 1 |\n\n"
        "## Endpoints\n\n"
        "| Endpoint | Requests | Error rate | p50 (ms) | p95 (ms) | p99 (ms) |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: |\n"
        "| /api | 2 | 50.00% | 10.00 | 10.00 | 10.00 |\n"
        "| /missing-duration | 1 | 0.00% | - | - | - |\n"
    )


def test_render_markdown_escapes_endpoint_cells():
    path = "/zażółć\\|`a`\r\n<script>&copy;[b](c)*_~"
    report = Report(1, (), (EndpointStats(path, 1, 0, 0, None, None),), (), ())

    assert render_markdown(report).splitlines()[-1] == (
        r"| /zażółć\\\|\`a\` \<script\>\&copy;\[b\](c)\*\_\~"
        " | 1 | 0.00% | 0.00 | - | - |"
    )


def test_render_markdown_describes_empty_data():
    markdown = render_markdown(Report(0, (), (), (), ()))

    assert "Total events: 0\n\nNo events.\n" in markdown
    assert markdown.endswith("## Endpoints\n\nNo endpoint data.\n")


def test_render_csv_exports_endpoint_metrics_and_quotes_paths():
    path = '/zażółć,"api"\r\nnext'
    report = Report(
        total_events=4,
        level_counts=(("Error", 1), ("Information", 3)),
        endpoints=(
            EndpointStats(path, 3, 1 / 3, 0.0, 12.345, 25.75),
            EndpointStats("/missing-duration", 1, 0.0, None, None, None),
        ),
        errors_by_time=(),
        exception_groups=(),
    )

    rows = list(csv.reader(StringIO(render_csv(report), newline="")))

    assert rows == [
        ["endpoint", "request_count", "error_rate", "p50_ms", "p95_ms", "p99_ms"],
        [path, "3", str(1 / 3), "0.0", "12.345", "25.75"],
        ["/missing-duration", "1", "0.0", "", "", ""],
    ]


def test_render_csv_without_endpoints_outputs_only_headers():
    report = Report(0, (), (), (), ())

    assert render_csv(report) == (
        "endpoint,request_count,error_rate,p50_ms,p95_ms,p99_ms\r\n"
    )
