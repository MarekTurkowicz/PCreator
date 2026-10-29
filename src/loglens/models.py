"""Shared data models for structured log events."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEvent:
    """A log event with optional metadata and arbitrary context properties.

    Missing timestamps remain unset; parsers are responsible for converting
    input timestamps and levels to their normalized representations. The
    message template and rendered message are kept separately because CLEF
    can provide either. Source and line number identify the input location
    when the event is read from a file.
    """

    timestamp: datetime | None = None
    level: str = "Information"
    message_template: str = ""
    message: str | None = None
    exception: str | None = None
    properties: dict[str, object] = field(default_factory=dict)
    source: str | None = None
    line_number: int | None = None
