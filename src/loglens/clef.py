"""Parse CLEF JSON events from individual lines or a file stream."""

import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from loglens.models import LogEvent

logger = logging.getLogger(__name__)


def read_file(path: str | Path, *, strict: bool = True) -> Iterator[LogEvent]:
    """Yield events lazily with their source path and one-based line number.

    The UTF-8 file is opened on the first iteration and closed on exhaustion,
    an error, or explicit iterator.close(). By default invalid lines propagate
    the parser's exception. With strict=False they are skipped with a warning
    containing the source path, line number and reason. File errors propagate
    in either mode. Call close() when stopping iteration early to release the file.
    """
    with open(path, encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                event = parse_line(line)
            except ValueError as error:
                if strict:
                    raise
                logger.warning("%s:%d: %s", path, line_number, error)
                continue
            event.source = str(path)
            event.line_number = line_number
            yield event


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
    Exceptions and nested context values are preserved without conversion.
    CLEF metadata is excluded from context; escaped @@ names lose one @.
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
        exception=data.get("@x"),
        properties={
            (key[1:] if key.startswith("@@") else key): value
            for key, value in data.items()
            if not key.startswith("@") or key.startswith("@@")
        },
    )
