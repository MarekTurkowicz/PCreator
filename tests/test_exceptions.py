"""Extract and normalize messages from .NET exceptions."""

import json

import pytest

from loglens.clef import parse_line
from loglens.exceptions import (
    ExceptionDetails,
    extract_exception,
    normalize_exception_message,
)
from loglens.models import LogEvent


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_extract_multiline_dotnet_exception_from_clef(newline):
    exception = newline.join(
        [
            "System.InvalidOperationException: Request failed: order 42",
            "Please retry later.",
            " ---> System.IO.IOException: Connection closed",
            "   at Example.Client.Send() in /src/Client.cs:line 12",
            "   --- End of inner exception stack trace ---",
            "   at Example.Service.Run()",
        ]
    )
    event = parse_line(json.dumps({"@x": exception}))

    assert extract_exception(event) == ExceptionDetails(
        "System.InvalidOperationException",
        "Request failed: order 42\nPlease retry later.",
    )
    assert event.exception == exception


def test_stack_trace_is_excluded_without_inner_exception():
    event = LogEvent(
        exception="MyApp.CustomException: Failed\n   at MyApp.Run()\n   at Main()"
    )

    assert extract_exception(event) == ExceptionDetails(
        "MyApp.CustomException", "Failed"
    )


@pytest.mark.parametrize("exception", [None, "", " \r\n "])
def test_absent_exception(exception):
    assert extract_exception(LogEvent(exception=exception)) == ExceptionDetails()


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        ("System.Exception", ExceptionDetails("System.Exception", "")),
        ("System.Exception: ", ExceptionDetails("System.Exception", "")),
        ("System.Exception: a:b", ExceptionDetails("System.Exception", "a:b")),
        ("Failure without a type", ExceptionDetails(None, "Failure without a type")),
        (
            "System.Exception: Failed\n\nDetails\n   at App.Run()",
            ExceptionDetails("System.Exception", "Failed\n\nDetails"),
        ),
    ],
)
def test_exception_header_variants(exception, expected):
    assert extract_exception(LogEvent(exception=exception)) == expected


@pytest.mark.parametrize(
    ("number", "uuid"),
    [
        ("42", "123e4567-e89b-12d3-a456-426614174000"),
        ("8701", "A987FBC9-4BED-4078-8F07-9141BA07C9F3"),
        ("0", "00000000-0000-0000-0000-000000000000"),
    ],
)
def test_normalize_exception_message_replaces_ids(number, uuid):
    message = f"Order #{number} failed.\nRequest ({uuid}) was rejected."
    event = LogEvent(exception=f"System.Exception: {message}")
    details = extract_exception(event)

    assert details.message == message
    assert normalize_exception_message(details.message) == (
        "Order #<number> failed.\nRequest (<uuid>) was rejected."
    )


@pytest.mark.parametrize(
    "message", ["", "  Access denied.  ", "HTTP2 raised E42 in job_12."]
)
def test_normalize_exception_message_preserves_static_text(message):
    assert normalize_exception_message(message) == message
