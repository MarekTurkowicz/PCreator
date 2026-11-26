"""Tests for error counts in fixed UTC time buckets."""

from datetime import datetime, timedelta, timezone

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import count_errors_by_time, create_schema, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402


def test_error_buckets_have_inclusive_start_exclusive_end_and_utc_results():
    samples = [
        ("2025-01-01T00:10:00Z", "Error"),
        ("2025-01-01T00:04:59.999999Z", "Error"),
        ("2025-01-01T02:05:00+02:00", "Fatal"),
        ("2024-12-31T19:00:00-05:00", "Error"),
        ("2025-01-01T00:05:00Z", "Warning"),
        ("2025-01-01T00:05:00Z", "Information"),
        (None, "Error"),
    ]
    with duckdb.connect() as connection:
        create_schema(connection)
        connection.execute("SET TimeZone = 'America/New_York'")
        insert_events(connection, [
            LogEvent(
                timestamp=datetime.fromisoformat(stamp) if stamp else None,
                level=level,
            )
            for stamp, level in samples
        ])

        result = count_errors_by_time(connection, bucket_size=timedelta(minutes=5))

        assert result == [
            (datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc), 2),
            (datetime(2025, 1, 1, 0, 5, tzinfo=timezone.utc), 1),
            (datetime(2025, 1, 1, 0, 10, tzinfo=timezone.utc), 1),
        ]
        assert all(stamp.tzinfo is timezone.utc for stamp, _ in result)


def test_default_minute_buckets_omit_gaps_and_non_errors():
    with duckdb.connect() as connection:
        create_schema(connection)
        assert count_errors_by_time(connection) == []
        insert_events(connection, [LogEvent(
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc), level="Warning"
        )])
        assert count_errors_by_time(connection) == []
        insert_events(connection, [
            LogEvent(timestamp=datetime.fromisoformat(stamp), level="Error")
            for stamp in ["2025-01-01T00:00:59Z", "2025-01-01T00:02:00Z"]
        ])
        assert count_errors_by_time(connection) == [
            (datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc), 1),
            (datetime(2025, 1, 1, 0, 2, tzinfo=timezone.utc), 1),
        ]


def test_fill_gaps_uses_fixed_utc_buckets_across_a_clock_change():
    first = datetime(2025, 3, 9, 6, 30, tzinfo=timezone.utc)
    step = timedelta(minutes=30)
    with duckdb.connect() as connection:
        create_schema(connection)
        connection.execute("SET TimeZone = 'America/New_York'")
        insert_events(connection, [
            LogEvent(first - step, "Warning"),
            LogEvent(first + timedelta(seconds=1), "Error"),
            LogEvent(first + step, "Warning"),
            LogEvent(first + 3 * step, "Fatal"),
            LogEvent(first + 4 * step, "Warning"),
        ])

        result = count_errors_by_time(connection, bucket_size=step, fill_gaps=True)

    assert result == [
        (first, 1),
        (first + step, 0),
        (first + 2 * step, 0),
        (first + 3 * step, 1),
    ]
    assert all(stamp.tzinfo is timezone.utc for stamp, _ in result)


def test_fill_gaps_returns_empty_series_without_dated_errors():
    with duckdb.connect() as connection:
        create_schema(connection)
        assert count_errors_by_time(connection, fill_gaps=True) == []

        insert_events(connection, [
            LogEvent(datetime(2025, 1, 1, tzinfo=timezone.utc), "Warning"),
            LogEvent(level="Error"),
        ])
        assert count_errors_by_time(connection, fill_gaps=True) == []


@pytest.mark.parametrize("size", [timedelta(0), timedelta(seconds=-1)])
def test_bucket_size_must_be_positive(size):
    with duckdb.connect() as connection:
        create_schema(connection)
        with pytest.raises(ValueError, match="bucket_size must be positive"):
            count_errors_by_time(connection, bucket_size=size)
