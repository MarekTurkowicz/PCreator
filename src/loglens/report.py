"""Build a report from the existing log statistics."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import duckdb

from loglens.database import (
    count_errors_by_time,
    count_events_by_level,
    count_requests_by_endpoint,
    create_schema,
    filter_events,
    insert_events,
    response_time_percentiles_by_endpoint,
)
from loglens.exceptions import ExceptionGroupSummary, rank_exception_groups


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
