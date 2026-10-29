"""Parse the core fields of a single CLEF JSON event."""

import json
from datetime import UTC, datetime

from loglens.models import LogEvent


def parse_line(line: str) -> LogEvent:
    """Read a JSON object into an event, raising on malformed input.

    Timestamps are converted to UTC; timestamps without an offset assume UTC.
    Invalid timestamps raise ValueError. Levels retain their spelling.
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
        level=data.get("@l", "Information"),
        message_template=data.get("@mt", ""),
        message=data.get("@m"),
    )
