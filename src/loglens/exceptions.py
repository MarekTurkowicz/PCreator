"""Extract, normalize, group, and rank .NET exceptions."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from loglens.models import LogEvent

_UUID = re.compile(
    r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b[0-9]+\b")

type ExceptionSignature = tuple[str | None, str]


@dataclass(frozen=True)
class ExceptionDetails:
    """Exception type and message, absent when the event has no exception."""

    exception_type: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class ExceptionGroupSummary:
    """Occurrence count and timestamp bounds for an exception signature."""

    signature: ExceptionSignature
    count: int
    first_seen: datetime | None
    last_seen: datetime | None


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


def normalize_exception_message(message: str) -> str:
    """Replace standalone decimal digit sequences and hyphenated UUIDs.

    Replace UUIDs first so their numeric segments stay together. Preserve
    punctuation, whitespace, and digits within words such as error codes.
    """
    return _NUMBER.sub("<number>", _UUID.sub("<uuid>", message))


def group_exceptions(
    events: Iterable[LogEvent],
) -> dict[ExceptionSignature, list[LogEvent]]:
    """Group events by outer exception type and normalized message.

    Skip events without exception text and preserve input order within each group.
    """
    groups: dict[ExceptionSignature, list[LogEvent]] = {}
    for event in events:
        details = extract_exception(event)
        if details.message is None:
            continue
        signature = (
            details.exception_type,
            normalize_exception_message(details.message),
        )
        groups.setdefault(signature, []).append(event)
    return groups


def rank_exception_groups(events: Iterable[LogEvent]) -> list[ExceptionGroupSummary]:
    """Rank by descending occurrence count, keeping input order for ties.

    Events without timestamps count toward the total. Bounds use dated
    events only and are both None when all timestamps in a group are missing.
    """
    return summarize_exception_groups(group_exceptions(events))


def summarize_exception_groups(
    groups: dict[ExceptionSignature, list[LogEvent]],
) -> list[ExceptionGroupSummary]:
    """Rank already grouped exceptions so callers can also access examples."""
    summaries = []
    for signature, group in groups.items():
        timestamps = [event.timestamp for event in group if event.timestamp is not None]
        summaries.append(
            ExceptionGroupSummary(
                signature=signature,
                count=len(group),
                first_seen=min(timestamps, default=None),
                last_seen=max(timestamps, default=None),
            )
        )
    return sorted(summaries, key=lambda summary: summary.count, reverse=True)
