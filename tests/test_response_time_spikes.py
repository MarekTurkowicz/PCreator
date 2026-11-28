"""Detect endpoint latency spikes from dated HTTP events."""

from datetime import datetime, timedelta, timezone

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import (  # noqa: E402
    create_schema,
    detect_response_time_spikes,
    insert_events,
)
from loglens.models import LogEvent  # noqa: E402

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
MINUTE = timedelta(minutes=1)


def events(endpoint, minute, durations):
    stamp = None if minute is None else START + minute * MINUTE
    return [
        LogEvent(
            timestamp=stamp, properties={"RequestPath": endpoint, "Elapsed": elapsed}
        )
        for elapsed in durations
    ]


def test_spike_requires_enough_valid_observations_in_current_and_baseline_buckets():
    logs = (
        events("/orders", 0, [10] * 5)
        + events("/orders", 1, [1000] * 4 + [True, "1000", -1, None])
        + events("/orders", 2, [0, 0, 0, 0, 30])
        + events("/orders", None, [1000] * 5)
        + events("/health", 1, [1] * 5)
        + events("/health", 2, [1] * 5)
        + events(" ", 0, [1] * 5)
        + events(" ", 2, [100] * 5)
        + events("/sparse", 0, [1] * 4)
        + events("/sparse", 1, [100] * 5)
    )
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, logs)

        spikes = detect_response_time_spikes(connection, window_size=2)
        assert len(spikes) == 1
        stamp, endpoint, p95, baseline = spikes[0]
        assert stamp == START + 2 * MINUTE
        assert stamp.tzinfo is timezone.utc
        assert endpoint == "/orders"
        assert (p95, baseline) == pytest.approx((24.0, 10.0))


def test_baseline_uses_only_endpoint_buckets_within_the_previous_window():
    logs = (
        events("/orders", 0, [90])
        + events("/orders", 2, [10])
        + events("/orders", 3, [18])
        + events("/orders", 4, [28])
        + events("/health", 6, [3])
    )
    with duckdb.connect() as connection:
        create_schema(connection)
        assert detect_response_time_spikes(connection, window_size=2) == []
        insert_events(connection, logs)

        spikes = detect_response_time_spikes(
            connection, window_size=2, min_observations=1
        )
        assert spikes == [
            (START + 4 * MINUTE, "/orders", 28.0, 14.0),
        ]
