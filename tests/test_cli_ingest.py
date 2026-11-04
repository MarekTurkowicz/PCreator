"""CLI ingestion persists directory contents in DuckDB."""

from pathlib import Path

import pytest

duckdb = pytest.importorskip("duckdb")
pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from loglens.cli import app  # noqa: E402


def test_ingest_persists_sample_and_skips_invalid_lines(tmp_path):
    directory = tmp_path / "logs"
    directory.mkdir()
    sample = Path(__file__).parents[1] / "samples" / "basic.clef"
    (directory / "basic.clef").write_bytes(sample.read_bytes())
    (directory / "extra.JSON").write_text(
        'invalid\n{"@l":"Error","RequestId":"r-2"}\n', encoding="utf-8"
    )
    (directory / "ignored.txt").write_text("{}\n", encoding="utf-8")
    database = tmp_path / "events.duckdb"

    result = CliRunner().invoke(app, ["ingest", str(directory), str(database)])

    assert result.exit_code == 0, result.output
    assert "Inserted events: 2" in result.output
    with duckdb.connect(str(database)) as connection:
        rows = connection.execute(
            "SELECT level, source, line_number FROM events ORDER BY source"
        ).fetchall()
        assert rows == [
            ("Warning", str(directory / "basic.clef"), 1),
            ("Error", str(directory / "extra.JSON"), 2),
        ]
        assert connection.execute(
            "SELECT properties->>'RequestId' FROM events WHERE level = 'Error'"
        ).fetchone() == ("r-2",)


def test_ingest_empty_directory(tmp_path):
    database = tmp_path / "events.duckdb"
    result = CliRunner().invoke(app, ["ingest", str(tmp_path), str(database)])

    assert result.exit_code == 0, result.output
    assert result.output == "Inserted events: 0\n"
    with duckdb.connect(str(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (0,)


def test_ingest_rejects_missing_directory(tmp_path):
    result = CliRunner().invoke(
        app, ["ingest", str(tmp_path / "missing"), str(tmp_path / "events.duckdb")]
    )

    assert result.exit_code == 2
    assert not (tmp_path / "events.duckdb").exists()


def test_ingest_reports_database_error(tmp_path):
    result = CliRunner().invoke(
        app, ["ingest", str(tmp_path), str(tmp_path / "missing" / "events.duckdb")]
    )

    assert result.exit_code == 1
    assert "Cannot ingest logs:" in result.output


def test_ingest_reports_invalid_encoding(tmp_path):
    (tmp_path / "bad.clef").write_bytes(b"\xff\n")

    result = CliRunner().invoke(
        app, ["ingest", str(tmp_path), str(tmp_path / "events.duckdb")]
    )

    assert result.exit_code == 1
    assert "Cannot ingest logs:" in result.output
    assert "Inserted events:" not in result.output
