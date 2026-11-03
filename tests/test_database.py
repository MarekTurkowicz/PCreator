"""Contract tests for the DuckDB event schema."""

import json
from datetime import datetime, timezone

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.database import create_schema, insert_events  # noqa: E402
from loglens.models import LogEvent  # noqa: E402


def test_schema_has_event_columns_and_types():
    with duckdb.connect() as connection:
        create_schema(connection)

        columns = connection.execute("DESCRIBE events").fetchall()

        assert [(column[0], column[1]) for column in columns] == [
            ("timestamp", "TIMESTAMP WITH TIME ZONE"),
            ("level", "VARCHAR"),
            ("message_template", "VARCHAR"),
            ("message", "VARCHAR"),
            ("exception", "VARCHAR"),
            ("properties", "JSON"),
            ("source", "VARCHAR"),
            ("line_number", "BIGINT"),
        ]


def test_schema_initializes_an_empty_database_and_can_be_repeated():
    with duckdb.connect() as connection:
        assert connection.execute("SHOW TABLES").fetchall() == []

        create_schema(connection)
        create_schema(connection)

        assert connection.execute("SHOW TABLES").fetchall() == [("events",)]
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (0,)


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 5])
def test_insert_events_streams_full_and_partial_batches(count):
    consumed = 0
    batches = []

    def events():
        nonlocal consumed
        for index in range(count):
            consumed += 1
            yield LogEvent(message_template=f"Event {index}", line_number=index + 1)

    with duckdb.connect() as connection:
        create_schema(connection)

        class RecordingConnection:
            def executemany(self, query, rows):
                batches.append((len(rows), consumed))
                return connection.executemany(query, rows)

        assert insert_events(RecordingConnection(), events(), batch_size=2) == count
        assert batches == [
            (min(2, count - start), min(start + 2, count))
            for start in range(0, count, 2)
        ]
        assert connection.execute(
            "SELECT message_template, line_number FROM events ORDER BY line_number"
        ).fetchall() == [(f"Event {index}", index + 1) for index in range(count)]


def test_insert_events_preserves_fields_and_appends():
    pytest.importorskip("pytz")
    timestamp = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    properties = {"user": {"name": "Łukasz", "roles": ["admin", None]}, "ok": True}
    event = LogEvent(
        timestamp=timestamp,
        level="Error",
        message_template="Failed {user}",
        message="Failed 'user'",
        exception="Error: failure\n  at Handler()",
        properties=properties,
        source="logs/input.clef",
        line_number=7,
    )
    with duckdb.connect() as connection:
        create_schema(connection)
        assert insert_events(connection, [event]) == 1
        assert insert_events(connection, [LogEvent()]) == 1
        rows = connection.execute(
            "SELECT * FROM events ORDER BY line_number NULLS LAST"
        ).fetchall()

        assert rows[0][:5] == (
            timestamp, "Error", "Failed {user}", "Failed 'user'", event.exception
        )
        assert json.loads(rows[0][5]) == properties
        assert rows[0][6:] == ("logs/input.clef", 7)
        assert rows[1] == (None, "Information", "", None, None, "{}", None, None)


@pytest.mark.parametrize("batch_size", [0, -1])
def test_insert_events_rejects_invalid_batch_size_before_reading(batch_size):
    def events():
        pytest.fail("Invalid batch size must be rejected before reading events")
        yield LogEvent()

    with duckdb.connect() as connection:
        create_schema(connection)
        with pytest.raises(ValueError, match="batch_size"):
            insert_events(connection, events(), batch_size=batch_size)
