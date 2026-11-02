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
