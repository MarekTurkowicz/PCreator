"""Absolute time range filters for stored events."""

from datetime import datetime, timedelta, timezone

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import create_schema, filter_events, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402


@pytest.fixture
def database():
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, [
            LogEvent(timestamp=datetime(2026, 1, 1, hour, tzinfo=timezone.utc),
                     message=str(hour), properties={"hour": hour})
            for hour in range(4)
        ] + [LogEvent(message="undated")])
        yield connection


@pytest.mark.parametrize(("start", "end", "expected"), [
    (None, None, ["0", "1", "2", "3", "undated"]),
    (1, None, ["1", "2", "3"]),
    (None, 2, ["0", "1", "2"]),
    (1, 2, ["1", "2"]),
    (2, 2, ["2"]),
    (4, None, []),
])
def test_absolute_time_bounds(database, start, end, expected):
    def bound(hour):
        if hour is None:
            return None
        return datetime(2026, 1, 1, hour, tzinfo=timezone.utc)

    events = filter_events(database, start=bound(start), end=bound(end))

    assert [event.message for event in events] == expected
    for event in events:
        if event.timestamp is not None:
            assert event.properties == {"hour": int(event.message)}


def test_bounds_normalize_offsets_and_naive_datetimes_to_utc(database):
    start = datetime(2026, 1, 1, 3, tzinfo=timezone(timedelta(hours=2)))
    events = filter_events(database, start=start, end=datetime(2026, 1, 1, 2))
    assert [event.message for event in events] == ["1", "2"]
    assert all(event.timestamp.tzinfo == timezone.utc for event in events)


def test_reversed_range_is_rejected(database):
    with pytest.raises(ValueError, match="start.*end"):
        filter_events(database, start=datetime(2026, 1, 2), end=datetime(2026, 1, 1))


def test_empty_database():
    with duckdb.connect() as connection:
        create_schema(connection)
        assert filter_events(connection) == []
