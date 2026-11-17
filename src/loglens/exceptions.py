"""Extract the outer exception header from .NET exception text."""

import re
from dataclasses import dataclass

from loglens.models import LogEvent


@dataclass(frozen=True)
class ExceptionDetails:
    """Exception type and message, absent when the event has no exception."""

    exception_type: str | None = None
    message: str | None = None


def extract_exception(event: LogEvent) -> ExceptionDetails:
    """Read @x without modifying the event or normalizing message identifiers.

    Keep the outer message's continuation lines, normalizing newlines to LF.
    Stop at a .NET stack frame or inner exception marker. A type-only header
    has an empty message; unstructured text is returned as a message without
    a type. Leading and trailing whitespace around the header is ignored.
    """
    if not event.exception or not event.exception.strip():
        return ExceptionDetails()

    lines = event.exception.strip().splitlines()
    header, separator, message = lines[0].partition(":")
    exception_type = header.strip()
    if not re.fullmatch(r"[A-Za-z_][\w.+`]*", exception_type):
        exception_type = None
        message = lines[0]
    elif not separator:
        message = ""

    message_lines = [message.strip()]
    for line in lines[1:]:
        if line.lstrip().startswith(("at ", "--->", "--- End of inner exception")):
            break
        message_lines.append(line)
    return ExceptionDetails(exception_type, "\n".join(message_lines).rstrip())
