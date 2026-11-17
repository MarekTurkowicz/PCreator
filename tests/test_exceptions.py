"""Extract exception headers from multiline .NET exception strings."""

import json

import pytest

from loglens.clef import parse_line
from loglens.exceptions import ExceptionDetails, extract_exception
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
