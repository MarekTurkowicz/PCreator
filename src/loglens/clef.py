"""Parse the core fields of a single CLEF JSON event."""

import json
from datetime import UTC, datetime

from loglens.models import LogEvent

_SERILOG_LEVELS = {
    level.lower(): level
    for level in ("Verbose", "Debug", "Information", "Warning", "Error", "Fatal")
}


def _normalize_level(value: object) -> str:
    """Return the canonical Serilog name or reject an unsupported level."""
    if isinstance(value, str):
        level = _SERILOG_LEVELS.get(value.lower())
        if level is not None:
            return level
    raise ValueError("CLEF level must be a standard Serilog level")


def parse_line(line: str) -> LogEvent:
    """Read a JSON object into an event, raising on malformed input.

    Timestamps are converted to UTC; timestamps without an offset assume UTC.
    Levels are matched case-insensitively to canonical Serilog names.
    Invalid timestamps and unsupported levels raise ValueError.
    Missing fields use the event model's defaults.
    """
    data = json.loads(line)
    if not isinstance(data, dict):
        raise ValueError("CLEF event must be a JSON object")

    timestamp = data.get("@t")
    if timestamp is not None:
        if not isinstance(timestamp, str):
            raise ValueError("CLEF timestamp must be an ISO 8601 string")
        timestamp = datetime.fromisoformat(timestamp)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        timestamp = timestamp.astimezone(UTC)

    return LogEvent(
        timestamp=timestamp,
        level=_normalize_level(data.get("@l", "Information")),
        message_template=data.get("@mt", ""),
        message=data.get("@m"),
    )
