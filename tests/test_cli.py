"""Tests for the LogLens command-line interface."""

import pytest

pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from loglens import __version__  # noqa: E402
from loglens.cli import app  # noqa: E402


def test_version_command():
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output == f"{__version__}\n"


def test_inspect_counts_valid_and_invalid_events(tmp_path):
    (tmp_path / "first.clef").write_text(
        '{"@mt":"Hello"}\nnot json\n{"@l":"Error"}\n', encoding="utf-8"
    )
    (tmp_path / "second.JSON").write_text(
        '{"@t":"bad date"}\n[]\n{"@mt":"World"}\n', encoding="utf-8"
    )
    (tmp_path / "ignored.txt").write_text("invalid\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "ignored.clef").write_text("{}\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["inspect", str(tmp_path)])

    assert result.exit_code == 0
    assert result.output == "Valid events: 3\nInvalid events: 3\n"


@pytest.mark.parametrize(
    ("contents", "expected"),
    [
        (None, "Valid events: 0\nInvalid events: 0\n"),
        ("invalid\n\n", "Valid events: 0\nInvalid events: 2\n"),
    ],
)
def test_inspect_empty_or_invalid_directory(tmp_path, contents, expected):
    if contents is not None:
        (tmp_path / "events.clef").write_text(contents, encoding="utf-8")

    result = CliRunner().invoke(app, ["inspect", str(tmp_path)])

    assert result.exit_code == 0
    assert result.output == expected


def test_inspect_rejects_missing_directory(tmp_path):
    result = CliRunner().invoke(app, ["inspect", str(tmp_path / "missing")])

    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_inspect_reports_unreadable_encoding(tmp_path):
    (tmp_path / "events.clef").write_bytes(b"\xff\n")

    result = CliRunner().invoke(app, ["inspect", str(tmp_path)])

    assert result.exit_code == 1
    assert "Cannot inspect logs:" in result.output
    assert "Valid events:" not in result.output
