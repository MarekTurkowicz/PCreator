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
