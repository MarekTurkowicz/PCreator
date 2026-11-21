"""CLI exception ranking for ingested CLEF events."""

import re

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from loglens.cli import app  # noqa: E402
from loglens.database import open_database  # noqa: E402


def test_errors_limits_ranked_groups_and_shows_an_original_exception(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "errors.clef").write_text(
        '{"@l":"Error","@x":"System.TimeoutException: Timeout"}\n'
        '{"@t":"2026-01-01T01:00:00Z","@l":"Error",'
        '"@x":"System.Exception: Order 42 missing\\n   at Orders.Load()"}\n'
        '{"@t":"2026-01-01T02:00:00Z","@l":"Fatal",'
        '"@x":"System.Exception: Order 99 missing"}\n'
        '{"@l":"Error"}\n',
        encoding="utf-8",
    )
    database = tmp_path / "events.duckdb"
    runner = CliRunner()
    assert runner.invoke(app, ["ingest", str(logs), str(database)]).exit_code == 0

    result = runner.invoke(app, ["errors", str(database), "--limit", "1"])

    assert result.exit_code == 0, result.output
    assert "System.Exception: Order <number> missing" in result.output
    assert "Occurrences: 2" in result.output
    assert "First seen: 2026-01-01T01:00:00+00:00" in result.output
    assert "Last seen: 2026-01-01T02:00:00+00:00" in result.output
    assert "System.Exception: Order 42 missing\n   at Orders.Load()" in result.output
    assert "System.TimeoutException" not in result.output

    result = runner.invoke(app, ["errors", str(database)])

    assert result.exit_code == 0, result.output
    assert result.output.index("System.Exception:") < result.output.index(
        "System.TimeoutException:"
    )


def test_errors_empty_database(tmp_path):
    database = tmp_path / "empty.duckdb"
    open_database(database).close()

    result = CliRunner().invoke(app, ["errors", str(database)])

    assert result.exit_code == 0, result.output
    assert result.output == "No exceptions.\n"


def test_errors_rejects_nonpositive_limit(tmp_path):
    database = tmp_path / "empty.duckdb"
    open_database(database).close()

    result = CliRunner().invoke(app, ["errors", str(database), "--limit", "0"])

    assert result.exit_code == 2, result.output
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert "--limit" in output
