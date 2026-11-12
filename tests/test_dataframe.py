"""DataFrame query results retain SQL columns, types and parameters."""

from datetime import datetime, timezone

import pytest

duckdb = pytest.importorskip("duckdb")
pd = pytest.importorskip("pandas")

from loglens.database import (  # noqa: E402
    create_schema,
    insert_events,
    query_dataframe,
)
from loglens.models import LogEvent  # noqa: E402


def test_query_dataframe_preserves_columns_types_and_bound_parameters():
    stamp = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    message = "Failure ' OR 1=1 --"
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, [
            LogEvent(timestamp=stamp, level="Error", message=message, line_number=7),
            LogEvent(message="Other"),
        ])

        frame = query_dataframe(
            connection,
            "SELECT timestamp, level, line_number FROM events WHERE message = ?",
            [message],
        )

        assert isinstance(frame, pd.DataFrame)
        assert list(frame.columns) == ["timestamp", "level", "line_number"]
        assert frame.shape == (1, 3)
        assert isinstance(frame["timestamp"].dtype, pd.DatetimeTZDtype)
        assert frame.loc[0, "timestamp"] == pd.Timestamp(stamp)
        assert pd.api.types.is_string_dtype(frame["level"])
        assert pd.api.types.is_integer_dtype(frame["line_number"])
        assert frame.loc[0, "level"] == "Error"
        assert frame.loc[0, "line_number"] == 7
        # Fetching the frame leaves the caller's connection usable.
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (2,)


def test_query_dataframe_empty_result_keeps_column_types():
    with duckdb.connect() as connection:
        create_schema(connection)
        frame = query_dataframe(connection, "SELECT level, line_number FROM events")

    assert frame.empty
    assert list(frame.columns) == ["level", "line_number"]
    assert pd.api.types.is_object_dtype(frame["level"])
    assert pd.api.types.is_integer_dtype(frame["line_number"])


def test_query_dataframe_supports_aggregates_and_null_values():
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, [LogEvent(), LogEvent(line_number=2)])
        frame = query_dataframe(
            connection,
            "SELECT COUNT(*) AS total, AVG(line_number) AS mean_line FROM events",
        )
        nullable = query_dataframe(connection, "SELECT line_number FROM events")

    assert list(frame.columns) == ["total", "mean_line"]
    assert frame.loc[0, "total"] == 2
    assert frame.loc[0, "mean_line"] == 2.0
    assert pd.api.types.is_integer_dtype(frame["total"])
    assert pd.api.types.is_float_dtype(frame["mean_line"])
    assert nullable["line_number"].isna().sum() == 1
