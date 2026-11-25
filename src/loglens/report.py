"""Build and render reports from the existing log statistics."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from html import escape
from io import StringIO
from typing import TYPE_CHECKING

from loglens.exceptions import ExceptionGroupSummary, rank_exception_groups

if TYPE_CHECKING:
    import duckdb

_MARKDOWN_CELL_ESCAPES = str.maketrans({char: f"\\{char}" for char in "\\|`<>&[]*_~"})


@dataclass(frozen=True)
class EndpointStats:
    """Request count, error fraction, and optional latency percentiles in ms."""

    path: str
    request_count: int
    error_rate: float
    p50_ms: float | None
    p95_ms: float | None
    p99_ms: float | None


@dataclass(frozen=True)
class Report:
    """Log statistics for a single selection of events."""

    total_events: int
    level_counts: tuple[tuple[str, int], ...]
    endpoints: tuple[EndpointStats, ...]
    errors_by_time: tuple[tuple[datetime, int], ...]
    exception_groups: tuple[ExceptionGroupSummary, ...]


def build_report(
    connection: duckdb.DuckDBPyConnection,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    since: str | None = None,
    clock: Callable[[], datetime] | None = None,
) -> Report:
    """Summarize an inclusive range, using the time semantics of filter_events.

    Error counts use one-minute UTC buckets. A bounded selection is copied
    to a private in-memory database so all aggregates use the same events.
    """
    import duckdb

    from loglens.database import create_schema, filter_events, insert_events

    events = filter_events(connection, start=start, end=end, since=since, clock=clock)
    exception_groups = tuple(rank_exception_groups(events))
    if start is None and end is None and since is None:
        return _summarize(connection, exception_groups)

    with duckdb.connect() as scoped:
        create_schema(scoped)
        insert_events(scoped, events)
        return _summarize(scoped, exception_groups)


def _summarize(
    connection: duckdb.DuckDBPyConnection,
    exception_groups: tuple[ExceptionGroupSummary, ...],
) -> Report:
    from loglens.database import (
        count_errors_by_time,
        count_events_by_level,
        count_requests_by_endpoint,
        response_time_percentiles_by_endpoint,
    )

    level_counts = tuple(count_events_by_level(connection))
    durations = {
        path: (p50, p95, p99)
        for path, p50, p95, p99 in response_time_percentiles_by_endpoint(connection)
    }
    endpoints = tuple(
        EndpointStats(
            path, count, float(rate), *durations.get(path, (None, None, None))
        )
        for path, count, rate in count_requests_by_endpoint(connection)
    )
    return Report(
        total_events=sum(count for _, count in level_counts),
        level_counts=level_counts,
        endpoints=endpoints,
        errors_by_time=tuple(count_errors_by_time(connection)),
        exception_groups=exception_groups,
    )


def _escape_markdown_cell(value: str) -> str:
    return " ".join(value.splitlines()).translate(_MARKDOWN_CELL_ESCAPES)


def render_markdown(report: Report) -> str:
    """Render the event summary and endpoint metrics as Markdown tables."""
    lines = ["# LogLens report", "", "## Summary", ""]
    lines.extend([f"Total events: {report.total_events}", ""])
    if report.level_counts:
        lines.extend(["| Level | Events |", "| --- | ---: |"])
        lines.extend(
            f"| {_escape_markdown_cell(level)} | {count} |"
            for level, count in report.level_counts
        )
    else:
        lines.append("No events.")

    lines.extend(["", "## Endpoints", ""])
    if report.endpoints:
        lines.extend([
            "| Endpoint | Requests | Error rate | p50 (ms) | p95 (ms) | p99 (ms) |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for endpoint in report.endpoints:
            path = _escape_markdown_cell(endpoint.path)
            percentiles = " | ".join(
                "-" if value is None else f"{value:.2f}"
                for value in (endpoint.p50_ms, endpoint.p95_ms, endpoint.p99_ms)
            )
            lines.append(
                f"| {path} | {endpoint.request_count} | "
                f"{endpoint.error_rate:.2%} | {percentiles} |"
            )
    else:
        lines.append("No endpoint data.")

    return "\n".join(lines) + "\n"


def render_csv(report: Report) -> str:
    """Render endpoint statistics as CSV with fractional error rates."""
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        ("endpoint", "request_count", "error_rate", "p50_ms", "p95_ms", "p99_ms")
    )
    writer.writerows(
        (
            endpoint.path,
            endpoint.request_count,
            endpoint.error_rate,
            endpoint.p50_ms,
            endpoint.p95_ms,
            endpoint.p99_ms,
        )
        for endpoint in report.endpoints
    )
    return output.getvalue()


def _html_table(headers: tuple[str, ...], rows: Iterable[tuple[str, ...]]) -> list[str]:
    header = "".join(f'<th scope="col">{escape(label)}</th>' for label in headers)
    lines = ["<table>", f"<thead><tr>{header}</tr></thead>", "<tbody>"]
    for row in rows:
        cells = "".join(f"<td>{escape(value)}</td>" for value in row)
        lines.append(f"<tr>{cells}</tr>")
    lines.extend(["</tbody>", "</table>"])
    return lines


def render_html(report: Report) -> str:
    """Render the event summary and endpoint metrics as a standalone HTML document."""
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>LogLens report</title>",
        "</head>",
        "<body>",
        "<h1>LogLens report</h1>",
        "<h2>Summary</h2>",
        f"<p>Total events: {report.total_events:d}</p>",
    ]
    if report.level_counts:
        rows = ((level, str(count)) for level, count in report.level_counts)
        lines.extend(_html_table(("Level", "Events"), rows))
    else:
        lines.append("<p>No events.</p>")

    lines.append("<h2>Endpoints</h2>")
    if report.endpoints:
        endpoint_rows = []
        for endpoint in report.endpoints:
            percentiles = tuple(
                "-" if value is None else f"{value:.2f}"
                for value in (endpoint.p50_ms, endpoint.p95_ms, endpoint.p99_ms)
            )
            endpoint_rows.append((
                endpoint.path,
                str(endpoint.request_count),
                f"{endpoint.error_rate:.2%}",
                *percentiles,
            ))
        headers = (
            "Endpoint", "Requests", "Error rate", "p50 (ms)", "p95 (ms)", "p99 (ms)"
        )
        lines.extend(_html_table(headers, endpoint_rows))
    else:
        lines.append("<p>No endpoint data.</p>")

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines) + "\n"
