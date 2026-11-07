"""Time range and minimum severity filters for stored events."""

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


@pytest.mark.parametrize(("since", "delta"), [
    ("30s", timedelta(seconds=30)),
    ("15m", timedelta(minutes=15)),
    ("2h", timedelta(hours=2)),
    ("3d", timedelta(days=3)),
    ("1w", timedelta(weeks=1)),
])
def test_since_units_and_inclusive_boundary(since, delta):
    now = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
    boundary = now - delta
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, [
            LogEvent(timestamp=boundary - timedelta(microseconds=1), message="old"),
            LogEvent(timestamp=boundary, message="boundary"),
            LogEvent(timestamp=now, message="now"),
            LogEvent(message="undated"),
        ])
        calls = []

        def clock():
            calls.append(True)
            return now

        events = filter_events(connection, since=since, clock=clock)
        assert [event.message for event in events] == ["boundary", "now"]
        assert len(calls) == 1


@pytest.mark.parametrize("now", [
    datetime(2026, 1, 1, 3),
    datetime(2026, 1, 1, 5, tzinfo=timezone(timedelta(hours=2))),
])
def test_since_normalizes_clock_and_combines_with_end(database, now):
    events = filter_events(database, since="2h", clock=lambda: now,
                           end=datetime(2026, 1, 1, 2))
    assert [event.message for event in events] == ["1", "2"]


@pytest.mark.parametrize("since", [
    "", "0h", "-2h", "1.5h", "2", "2H", "2 h", "1h30m", "2y",
    "9" * 30 + "w",
])
def test_invalid_since_is_rejected(database, since):
    with pytest.raises(ValueError, match="since"):
        filter_events(database, since=since)


def test_since_and_start_are_mutually_exclusive(database):
    with pytest.raises(ValueError, match="since.*start"):
        filter_events(database, since="2h", start=datetime(2026, 1, 1))


def test_since_rejects_boundary_after_end(database):
    with pytest.raises(ValueError, match="start.*end"):
        filter_events(database, since="1h",
                      clock=lambda: datetime(2026, 1, 1, 3),
                      end=datetime(2026, 1, 1, 1))


LEVELS = ("Verbose", "Debug", "Information", "Warning", "Error", "Fatal")


@pytest.mark.parametrize("minimum", [None, *LEVELS, "wArNiNg"])
def test_minimum_level_uses_serilog_severity_order(minimum):
    with duckdb.connect() as connection:
        create_schema(connection)
        # Chronological order deliberately differs from severity order.
        events = [
            LogEvent(timestamp=datetime(2026, 1, 1, hour, tzinfo=timezone.utc),
                     level=level, message=level)
            for hour, level in enumerate(reversed(LEVELS))
        ]
        insert_events(connection, events)
        rank = 0 if minimum is None else LEVELS.index(minimum.capitalize())
        expected = [event for event in events if LEVELS.index(event.level) >= rank]
        assert filter_events(connection, min_level=minimum) == expected


def test_minimum_level_combines_with_time_filters():
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, [
            LogEvent(timestamp=datetime(2026, 1, 1, hour), level=level)
            for hour, level in enumerate(["Error", "Debug", "Warning", "Fatal"])
        ] + [LogEvent(level="Fatal")])
        events = filter_events(connection, min_level="Warning", since="2h",
                               clock=lambda: datetime(2026, 1, 1, 3),
                               end=datetime(2026, 1, 1, 2))
        assert [event.level for event in events] == ["Warning"]
        assert len(filter_events(connection, min_level="Fatal")) == 2


@pytest.mark.parametrize("minimum", ["", "Info", "Critical", " Error", 3])
def test_invalid_minimum_level_is_rejected(database, minimum):
    with pytest.raises(ValueError, match="min_level"):
        filter_events(database, min_level=minimum)


def test_minimum_level_on_empty_database():
    with duckdb.connect() as connection:
        create_schema(connection)
        assert filter_events(connection, min_level="Error") == []


@pytest.mark.parametrize("value", ["42", 42, True, None, "O'Reilly"])
def test_context_property_matches_value_and_type(value):
    with duckdb.connect() as connection:
        create_schema(connection)
        values = ["42", 42, True, None, "O'Reilly"]
        insert_events(connection, [
            LogEvent(message=str(index), properties={"UserId": item})
            for index, item in enumerate(values)
        ] + [LogEvent(message="missing")])
        events = filter_events(connection, context_key="UserId", context_value=value)
        assert [event.properties for event in events] == [{"UserId": value}]
        assert len(events) == 1


@pytest.mark.parametrize("key", ["a.b", "a/b~c", 'a"b', "", "x') OR TRUE --"])
def test_context_property_names_are_literal(database, key):
    insert_events(database, [LogEvent(properties={key: "match"})])
    assert len(filter_events(database, context_key=key, context_value="match")) == 1
    assert filter_events(database, context_key=key, context_value="other") == []


def test_context_property_combines_with_existing_filters(database):
    events = filter_events(
        database, context_key="hour", context_value=2, min_level="Information",
        since="2h", clock=lambda: datetime(2026, 1, 1, 3),
        end=datetime(2026, 1, 1, 2),
    )
    assert [event.message for event in events] == ["2"]
    assert filter_events(database, context_key="absent", context_value=None) == []
    assert filter_events(database, context_key="hour", context_value=2,
                         min_level="Error") == []


def test_context_property_on_empty_database():
    with duckdb.connect() as connection:
        create_schema(connection)
        assert filter_events(connection, context_key="UserId", context_value=42) == []
