"""Contract shared with the minimal Serilog generator (no .NET required)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from loglens.clef import read_file
from loglens.http import extract_http


def test_generate_http_serilog_sample():
    sample = Path(__file__).resolve().parents[1] / "samples" / "dotnet-http.clef"
    events = list(read_file(sample))

    assert len(events) == 3
    start = datetime(1970, 1, 1, 16, 2, 4, tzinfo=UTC)
    assert [event.timestamp for event in events] == [
        start + timedelta(milliseconds=index) for index in range(3)
    ]
    assert [extract_http(event).elapsed_ms for event in events] == [0.1, 250, 500.0]
    for event in events:
        http = extract_http(event)
        assert event.timestamp is not None
        assert event.timestamp.tzinfo is UTC
        assert event.level == "Information"
        assert http.endpoint in {"/api/orders", "/api/products", "/health"}
        assert http.elapsed_ms is not None
        assert 0.1 <= http.elapsed_ms <= 500
        assert event.properties["RequestMethod"] == "GET"
        assert event.properties["StatusCode"] == 200
        assert event.exception is None


def test_minimal_serilog_sample():
    sample = Path(__file__).resolve().parents[1] / "samples" / "dotnet-minimal.clef"

    events = list(read_file(sample))

    assert len(events) == 1
    event = events[0]
    assert event.timestamp is not None
    assert event.timestamp.tzinfo is UTC
    assert event.level == "Information"
    assert event.message_template == "Hello from LogLens"
    assert event.properties == {}
    assert event.exception is None


def test_generate_count_serilog_sample():
    sample = Path(__file__).resolve().parents[1] / "samples" / "dotnet-count.clef"

    events = list(read_file(sample))

    assert len(events) == 3
    assert [event.line_number for event in events] == [1, 2, 3]
    for event in events:
        assert event.timestamp is not None
        assert event.timestamp.tzinfo is UTC
        assert event.level == "Information"
        assert event.message_template == "Hello from LogLens"
        assert event.properties == {}
        assert event.exception is None


def test_generate_seed_serilog_sample():
    """Contract for generate --count 3 --seed 42, including stable UTC times."""
    sample = Path(__file__).resolve().parents[1] / "samples" / "dotnet-seed.clef"

    events = list(read_file(sample))

    assert len(events) == 3
    start = datetime(1970, 1, 1, 16, 2, 4, tzinfo=UTC)
    assert [event.timestamp for event in events] == [
        start + timedelta(milliseconds=index) for index in range(3)
    ]
    for event in events:
        assert event.level == "Information"
        assert event.message_template == "Hello from LogLens"
        assert event.properties == {}
        assert event.exception is None
