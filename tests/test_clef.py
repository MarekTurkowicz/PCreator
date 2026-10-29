"""Tests for reading individual CLEF events."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from loglens.clef import parse_line
from loglens.models import LogEvent


def test_parse_sample_fields():
    sample = Path(__file__).resolve().parents[1] / "samples" / "basic.clef"

    event = parse_line(sample.read_text(encoding="utf-8"))

    assert isinstance(event, LogEvent)
    assert event.timestamp == datetime(2026, 10, 29, 12, 34, 56, tzinfo=UTC)
    assert event.level == "Warning"
    assert event.message_template == "Request {RequestId} completed"
    assert event.message == "Request request-1 completed"


def test_missing_fields_use_model_defaults():
    assert parse_line("{}") == LogEvent()


@pytest.mark.parametrize(
    "level", ["Verbose", "Debug", "Information", "Warning", "Error", "Fatal"]
)
@pytest.mark.parametrize("spelling", [str.lower, str.upper, str.title])
def test_serilog_levels_are_normalized(level, spelling):
    event = parse_line(json.dumps({"@l": spelling(level)}))

    assert event.level == level


@pytest.mark.parametrize(
    "level", ["unknown", "Info", "Warn", "", " Error ", None, 123, True, [], {}]
)
def test_unknown_or_invalid_levels_are_rejected(level):
    with pytest.raises(ValueError, match="CLEF level"):
        parse_line(json.dumps({"@l": level}))


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-29T12:34:56.123456Z",
        "2026-10-29T14:34:56.123456+02:00",
        "2026-10-29T07:04:56.123456-05:30",
        "2026-10-29T12:34:56.123456",
    ],
)
def test_timestamps_are_normalized_to_utc(timestamp):
    event = parse_line(json.dumps({"@t": timestamp}))

    assert event.timestamp == datetime(2026, 10, 29, 12, 34, 56, 123456, tzinfo=UTC)
    assert event.timestamp.tzinfo is UTC


def test_utc_conversion_crosses_date_boundary():
    event = parse_line('{"@t":"2026-01-01T00:30:00+02:00"}')

    assert event.timestamp == datetime(2025, 12, 31, 22, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "timestamp", ["", "not-a-date", "2026-02-30T12:00:00Z", 123, True, [], {}]
)
def test_invalid_timestamps_are_rejected(timestamp):
    with pytest.raises(ValueError):
        parse_line(json.dumps({"@t": timestamp}))


def test_null_timestamp_remains_unset():
    assert parse_line('{"@t":null}').timestamp is None


def test_rendered_message_does_not_require_template():
    event = parse_line('{"@m":"Application started"}')

    assert event.message == "Application started"
    assert event.message_template == ""


def test_invalid_json_raises_decode_error():
    with pytest.raises(json.JSONDecodeError):
        parse_line("invalid json")


@pytest.mark.parametrize("line", ["[]", "null", '"text"', "42"])
def test_non_object_json_is_rejected(line):
    with pytest.raises(ValueError, match="JSON object"):
        parse_line(line)
