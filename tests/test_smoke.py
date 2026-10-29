"""Smoke tests for the initial package skeleton."""

import tomllib
from pathlib import Path

import loglens


def test_package_version_matches_project_metadata():
    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as metadata_file:
        project = tomllib.load(metadata_file)["project"]

    assert project["name"] == "loglens"
    assert loglens.__version__ == project["version"] == "0.1.0"
