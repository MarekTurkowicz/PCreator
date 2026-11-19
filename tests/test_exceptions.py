"""Extract, normalize, and rank .NET exceptions."""

import json
from datetime import UTC, datetime

import pytest

from loglens.clef import parse_line
from loglens.exceptions import (
    ExceptionDetails,
    ExceptionGroupSummary,
    extract_exception,
    group_exceptions,
    normalize_exception_message,
    rank_exception_groups,
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


def test_group_exceptions_by_type_and_normalized_message():
    first, second, different_type, different_message = (
        parse_line(json.dumps({"@x": exception}))
        for exception in (
            "System.Exception: Order 42 failed (123e4567-e89b-12d3-a456-426614174000)"
            "\n   at First.Run()",
            "System.Exception: Order 73 failed (A987FBC9-4BED-4078-8F07-9141BA07C9F3)"
            "\n   at Second.Run()",
            "System.IO.IOException: Order 12 failed "
            "(123e4567-e89b-12d3-a456-426614174000)",
            "System.Exception: Order 42 expired",
        )
    )

    events = iter([first, different_type, second, different_message])
    assert group_exceptions(events) == {
        ("System.Exception", "Order <number> failed (<uuid>)"): [first, second],
        ("System.IO.IOException", "Order <number> failed (<uuid>)"): [different_type],
        ("System.Exception", "Order <number> expired"): [different_message],
    }


def test_group_exceptions_handles_missing_type_message_and_exception():
    untyped = LogEvent(exception="Order 42 failed")
    type_only = LogEvent(exception="System.Exception")
    absent = [LogEvent(), LogEvent(exception=""), LogEvent(exception=" \n ")]

    assert group_exceptions(iter(absent)) == {}
    assert group_exceptions(iter([*absent, untyped, type_only])) == {
        (None, "Order <number> failed"): [untyped],
        ("System.Exception", ""): [type_only],
    }


def test_rank_exception_groups_by_count_with_chronological_bounds():
    first = datetime(2025, 1, 1, tzinfo=UTC)
    last = datetime(2025, 1, 3, tzinfo=UTC)
    events = iter(
        [
            LogEvent(exception="Missing order 1"),
            LogEvent(timestamp=last, exception="System.Exception: Order 2 failed"),
            LogEvent(timestamp=first, exception="System.Exception: Access denied"),
            LogEvent(exception="System.Exception: Order 3 failed"),
            LogEvent(timestamp=first, exception="System.Exception: Order 4 failed"),
            LogEvent(timestamp=last),
        ]
    )

    assert rank_exception_groups(events) == [
        ExceptionGroupSummary(
            ("System.Exception", "Order <number> failed"), 3, first, last
        ),
        ExceptionGroupSummary((None, "Missing order <number>"), 1, None, None),
        ExceptionGroupSummary(("System.Exception", "Access denied"), 1, first, first),
    ]


def test_rank_exception_groups_without_exceptions():
    assert rank_exception_groups([LogEvent()]) == []
