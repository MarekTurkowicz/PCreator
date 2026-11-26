"""The report command analyzes a directory and selects an output format."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("typer")

from rich.text import Text  # noqa: E402
from typer.testing import CliRunner  # noqa: E402

from loglens.cli import app  # noqa: E402


def test_report_writes_markdown_from_samples(tmp_path):
    samples = Path(__file__).parents[1] / "samples"
    output = tmp_path / "report.md"

    result = CliRunner().invoke(app, ["report", str(samples), "--out", str(output)])

    assert result.exit_code == 0, result.output
    markdown = output.read_text(encoding="utf-8")
    assert markdown.startswith("# LogLens report\n")
    assert "| Warning | 1 |" in markdown
    assert "## Endpoints\n" in markdown


def test_report_filters_by_since_and_prints_markdown(tmp_path):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(minutes=5)).isoformat()
    old = (now - timedelta(days=1)).isoformat()
    (tmp_path / "requests.clef").write_text(
        f'{{"@t":"{old}","@l":"Error","RequestPath":"/old"}}\n'
        f'{{"@t":"{recent}","RequestPath":"/recent"}}\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["report", str(tmp_path), "--since", "2h"])

    assert result.exit_code == 0, result.output
    assert "Total events: 1\n" in result.stdout
    assert "| /recent | 1 |" in result.stdout
    assert "/old" not in result.stdout


def test_report_rejects_invalid_since_before_writing_output(tmp_path):
    output = tmp_path / "report.md"
    result = CliRunner().invoke(
        app, ["report", str(tmp_path), "--since", "yesterday", "--out", str(output)]
    )

    assert result.exit_code != 0
    assert "since must be a positive integer" in result.output
    assert not output.exists()


@pytest.mark.parametrize(
    ("extension", "prefix"),
    [
        (".HTML", "<!doctype html>\n"),
        (".htm", "<!doctype html>\n"),
        (".csv", "endpoint,request_count,error_rate,p50_ms,p95_ms,p99_ms\r\n"),
        (".markdown", "# LogLens report\n"),
        ("", "# LogLens report\n"),
    ],
)
def test_report_infers_format_from_output_extension(tmp_path, extension, prefix):
    output = tmp_path / f"report{extension}"

    result = CliRunner().invoke(app, ["report", str(tmp_path), "--out", str(output)])

    assert result.exit_code == 0, result.output
    assert output.read_bytes().startswith(prefix.encode())
    assert result.stdout == ""


def test_report_accepts_explicit_format_on_stdout(tmp_path):
    result = CliRunner().invoke(app, ["report", str(tmp_path), "--format", "html"])

    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("<!doctype html>\n")


def test_report_explicit_format_overrides_output_extension(tmp_path):
    output = tmp_path / "report.md"
    result = CliRunner().invoke(
        app, ["report", str(tmp_path), "--format", "csv", "--out", str(output)]
    )

    assert result.exit_code == 0, result.output
    assert output.read_text(encoding="utf-8").startswith("endpoint,request_count,")


@pytest.mark.parametrize(
    ("options", "message"),
    [(["--format", "json"], "--format"), ([], "Unsupported report extension")],
)
def test_report_rejects_unsupported_formats(tmp_path, options, message):
    output = tmp_path / "report.json"
    output.write_text("existing report", encoding="utf-8")

    result = CliRunner().invoke(
        app, ["report", str(tmp_path), "--out", str(output), *options]
    )

    assert result.exit_code == 2, result.output
    error_output = Text.from_ansi(result.output).plain
    assert message in error_output
    assert "json" in error_output
    assert output.read_text(encoding="utf-8") == "existing report"
