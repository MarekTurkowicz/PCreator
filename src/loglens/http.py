"""Extract HTTP request details from Serilog context properties."""

from dataclasses import dataclass
from math import isfinite

from loglens.models import LogEvent


@dataclass(frozen=True)
class HttpDetails:
    """An HTTP endpoint and response duration, independently optional."""

    endpoint: str | None = None
    elapsed_ms: float | None = None


def extract_http(event: LogEvent) -> HttpDetails:
    """Read top-level RequestPath and Elapsed from an event without mutation.

    RequestPath is preserved verbatim when it is a nonblank string; paths
    are not grouped or normalized. Serilog request completion logs express
    Elapsed in milliseconds. Accept finite, nonnegative integers and floats,
    excluding booleans. Missing or invalid values become None independently,
    so ordinary non-HTTP events are also supported. Nested properties and
    numeric strings are not interpreted.
    """
    endpoint = event.properties.get("RequestPath")
    if not isinstance(endpoint, str) or not endpoint.strip():
        endpoint = None

    elapsed = event.properties.get("Elapsed")
    if (
        not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or elapsed < 0
        or (isinstance(elapsed, float) and not isfinite(elapsed))
    ):
        elapsed = None

    return HttpDetails(endpoint=endpoint, elapsed_ms=elapsed)
