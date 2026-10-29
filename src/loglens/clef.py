"""Parse the core fields of a single CLEF JSON event."""

import json
from datetime import datetime

from loglens.models import LogEvent


def parse_line(line: str) -> LogEvent:
    """Read a JSON object into an event, raising on malformed input.

    Timestamps retain their input offset and levels retain their spelling.
    Missing fields use the event model's defaults.
    """
    data = json.loads(line)
    if not isinstance(data, dict):
        raise ValueError("CLEF event must be a JSON object")

    timestamp = data.get("@t")
    return LogEvent(
        timestamp=datetime.fromisoformat(timestamp) if timestamp is not None else None,
        level=data.get("@l", "Information"),
        message_template=data.get("@mt", ""),
        message=data.get("@m"),
    )
