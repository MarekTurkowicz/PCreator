"""Discovery of supported log files in a directory."""

import pytest

from loglens.discovery import find_log_files


@pytest.mark.parametrize("use_string", [False, True])
def test_find_log_files_filters_and_sorts(tmp_path, use_string):
    for name in (
        "z.clef", "a.json", "b.CLEF", "c.JSON", "notes.txt", "x.json.bak", "noext"
    ):
        (tmp_path / name).write_text("", encoding="utf-8")
    nested = tmp_path / "nested.clef"
    nested.mkdir()
    (nested / "hidden.json").write_text("", encoding="utf-8")

    files = find_log_files(str(tmp_path) if use_string else tmp_path)

    assert files == [
        tmp_path / name for name in ("a.json", "b.CLEF", "c.JSON", "z.clef")
    ]


def test_find_log_files_empty_directory(tmp_path):
    assert find_log_files(tmp_path) == []


def test_find_log_files_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_log_files(tmp_path / "missing")


def test_find_log_files_rejects_file_input(tmp_path):
    path = tmp_path / "events.clef"
    path.write_text("", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        find_log_files(path)
