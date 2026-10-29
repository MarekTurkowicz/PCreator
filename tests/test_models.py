"""Tests for the common log event model."""

from datetime import UTC, datetime

from loglens.models import LogEvent


def test_log_event_defaults():
    event = LogEvent()

    assert event.timestamp is None
    assert event.level == "Information"
    assert event.message_template == ""
    assert event.message is None
    assert event.exception is None
    assert event.properties == {}
    assert event.source is None
    assert event.line_number is None


def test_log_event_properties_are_independent():
    first = LogEvent()
    second = LogEvent()

    first.properties["RequestId"] = "request-1"

    assert second.properties == {}


def test_log_event_preserves_supplied_values():
    timestamp = datetime(2026, 10, 29, 12, tzinfo=UTC)
    properties = {"RequestId": "request-1", "Http": {"StatusCode": 500}}
    event = LogEvent(
        timestamp=timestamp,
        level="Error",
        message_template="Request {RequestId} failed",
        message="Request request-1 failed",
        exception="System.Exception: Failure",
        properties=properties,
        source="application.clef",
        line_number=3,
    )

    assert event.timestamp == timestamp
    assert event.level == "Error"
    assert event.message_template == "Request {RequestId} failed"
    assert event.message == "Request request-1 failed"
    assert event.exception == "System.Exception: Failure"
    assert event.properties == properties
    assert event.source == "application.clef"
    assert event.line_number == 3
