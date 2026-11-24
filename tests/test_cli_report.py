"""The report command analyzes a directory and renders Markdown."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("typer")

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
