"""CLI statistics summarize a persisted CLEF sample."""

import pytest

duckdb = pytest.importorskip("duckdb")
pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from loglens.cli import app  # noqa: E402
from loglens.database import open_database  # noqa: E402


def test_stats_displays_ingested_sample(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "http.clef").write_text(
        '{"RequestPath":"/api","Elapsed":10}\n'
        '{"@l":"Error","RequestPath":"/api","Elapsed":30}\n'
        '{"@l":"Warning","RequestPath":"/health"}\n',
        encoding="utf-8",
    )
    database = tmp_path / "events.duckdb"
    runner = CliRunner()
    assert runner.invoke(app, ["ingest", str(logs), str(database)]).exit_code == 0

    result = runner.invoke(app, ["stats", str(database)])

    assert result.exit_code == 0, result.output
    assert result.output == (
        "Levels\nLevel\tEvents\nError\t1\nInformation\t1\nWarning\t1\n"
        "\nEndpoints\nEndpoint\tRequests\tError rate\tp50 (ms)\tp95 (ms)\tp99 (ms)\n"
        "/api\t2\t50.00%\t20.00\t29.00\t29.80\n"
        "/health\t1\t0.00%\t-\t-\t-\n"
    )


def test_stats_empty_database(tmp_path):
    database = tmp_path / "empty.duckdb"
    open_database(database).close()

    result = CliRunner().invoke(app, ["stats", str(database)])

    assert result.exit_code == 0, result.output
    assert "Level\tEvents\n" in result.output
    assert "Endpoint\tRequests\tError rate" in result.output
    assert result.output.count("No data.") == 2


def test_stats_rejects_missing_database_without_creating_it(tmp_path):
    database = tmp_path / "missing.duckdb"

    result = CliRunner().invoke(app, ["stats", str(database)])

    assert result.exit_code == 2
    assert not database.exists()


def test_stats_reports_invalid_database(tmp_path):
    database = tmp_path / "invalid.duckdb"
    database.write_text("invalid", encoding="utf-8")

    result = CliRunner().invoke(app, ["stats", str(database)])

    assert result.exit_code == 1
    assert "Cannot read statistics:" in result.output
    assert database.read_text(encoding="utf-8") == "invalid"
