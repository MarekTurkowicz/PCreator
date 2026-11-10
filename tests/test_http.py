"""HTTP context extraction from structured log events."""

import pytest

from loglens.clef import parse_line
from loglens.http import HttpDetails, extract_http
from loglens.models import LogEvent


def test_extract_http_from_clef():
    event = parse_line(
        '{"@mt":"Request completed", "RequestPath":"/api/orders/42",'
        '"Elapsed":12.75,"StatusCode":200}'
    )
    original = event.properties.copy()

    assert extract_http(event) == HttpDetails("/api/orders/42", 12.75)
    assert event.properties == original


@pytest.mark.parametrize(
    ("properties", "expected"),
    [
        ({}, HttpDetails()),
        ({"RequestPath": "/health"}, HttpDetails("/health", None)),
        ({"Elapsed": 0}, HttpDetails(None, 0)),
        ({"Elapsed": 25}, HttpDetails(None, 25)),
        ({"RequestPath": None, "Elapsed": None}, HttpDetails()),
        ({"Http": {"RequestPath": "/nested", "Elapsed": 10}}, HttpDetails()),
    ],
)
def test_extract_http_with_missing_fields(properties, expected):
    assert extract_http(LogEvent(properties=properties)) == expected


@pytest.mark.parametrize("path", [None, "", "   ", 123, False, [], {}])
def test_invalid_endpoint_preserves_elapsed(path):
    event = LogEvent(properties={"RequestPath": path, "Elapsed": 3.5})

    assert extract_http(event) == HttpDetails(None, 3.5)


@pytest.mark.parametrize(
    "elapsed",
    [None, "12.5", True, False, -1, float("nan"), float("inf"), float("-inf"), [], {}],
)
def test_invalid_elapsed_preserves_endpoint(elapsed):
    event = LogEvent(properties={"RequestPath": "/health", "Elapsed": elapsed})

    assert extract_http(event) == HttpDetails("/health", None)
