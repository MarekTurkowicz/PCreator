"""Contract shared with the minimal Serilog generator (no .NET required)."""

from datetime import UTC
from pathlib import Path

from loglens.clef import read_file


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
