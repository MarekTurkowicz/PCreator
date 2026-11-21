"""CLI request traces for ingested CLEF events."""

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from loglens.cli import app  # noqa: E402
from loglens.database import open_database  # noqa: E402


def test_trace_shows_matching_events_in_chronological_order(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "requests.clef").write_text(
        '{"@t":"2026-01-01T01:00:02Z","@l":"Warning",'
        '"@mt":"End {Request}","@m":"Ended request","CorrelationId":"42"}\n'
        '{"@t":"2026-01-01T01:00:01Z","@m":"Another request","CorrelationId":"420"}\n'
        '{"@mt":"Undated event","CorrelationId":"42"}\n'
        '{"@t":"2026-01-01T02:00:00+01:00",'
        '"@mt":"Started request","CorrelationId":"42"}\n',
        encoding="utf-8",
    )
    database = tmp_path / "events.duckdb"
    runner = CliRunner()
    ingest = runner.invoke(app, ["ingest", str(logs), str(database)])
    assert ingest.exit_code == 0, ingest.output

    result = runner.invoke(app, ["trace", str(database), "42"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "Timestamp\tLevel\tMessage",
        "2026-01-01T01:00:00+00:00\tInformation\tStarted request",
        "2026-01-01T01:00:02+00:00\tWarning\tEnded request",
        "-\tInformation\tUndated event",
    ]


def test_trace_reports_missing_request(tmp_path):
    database = tmp_path / "empty.duckdb"
    open_database(database).close()

    result = CliRunner().invoke(app, ["trace", str(database), "unknown"])

    assert result.exit_code == 0, result.output
    assert result.output == "No matching events.\n"
