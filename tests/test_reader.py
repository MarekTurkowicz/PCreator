"""Streaming CLEF file reading and input locations."""

import json

import pytest

from loglens.clef import read_file, read_files


def test_read_files_preserves_order_and_source_locations(tmp_path):
    first = tmp_path / "first.clef"
    second = tmp_path / "second.json"
    first.write_text('{"@mt":"First"}\n{"@mt":"Second"}\n', encoding="utf-8")
    second.write_text('{"@mt":"Third","RequestId":42}\n', encoding="utf-8")

    events = list(read_files([str(second), first]))

    assert [event.message_template for event in events] == ["Third", "First", "Second"]
    assert [event.source for event in events] == [str(second), str(first), str(first)]
    assert [event.line_number for event in events] == [1, 1, 2]
    assert events[0].properties == {"RequestId": 42}


def test_read_files_is_lazy_and_accepts_iterable(tmp_path):
    first = tmp_path / "first.clef"
    second = tmp_path / "second.clef"
    events = read_files(path for path in (first, second))
    first.write_text('{"@mt":"First"}\n', encoding="utf-8")

    assert next(events).message_template == "First"
    second.write_text('{"@mt":"Second"}\n', encoding="utf-8")
    assert next(events).source == str(second)
    assert list(events) == []


def test_read_files_empty_input():
    assert list(read_files([])) == []


def test_read_files_forwards_strict_mode(tmp_path, caplog):
    first = tmp_path / "mixed.clef"
    second = tmp_path / "valid.clef"
    first.write_text('invalid\n{"@mt":"First"}\n', encoding="utf-8")
    second.write_text('{"@mt":"Second"}\n', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        list(read_files([first, second]))
    events = list(read_files([first, second], strict=False))

    assert [event.message_template for event in events] == ["First", "Second"]
    assert [event.line_number for event in events] == [2, 1]
    assert f"{first}:1" in caplog.text


def test_read_files_propagates_missing_file_in_tolerant_mode(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(read_files([tmp_path / "missing.clef"], strict=False))


@pytest.mark.parametrize("use_string", [False, True])
def test_read_file_preserves_events_and_locations(tmp_path, use_string):
    path = tmp_path / "events.clef"
    path.write_text(
        '{"@mt":"Zażółć","RequestId":42}\n'
        '{"@mt":"Failed","@l":"error","@x":"Failure"}\n',
        encoding="utf-8",
    )

    events = list(read_file(str(path) if use_string else path))

    assert [event.message_template for event in events] == ["Zażółć", "Failed"]
    assert [event.line_number for event in events] == [1, 2]
    assert [event.source for event in events] == [str(path), str(path)]
    assert events[0].properties == {"RequestId": 42}
    assert events[1].level == "Error"
    assert events[1].exception == "Failure"


def test_read_file_reads_events_lazily(tmp_path):
    path = tmp_path / "lazy.clef"
    events = read_file(path)
    # Creating the iterator must not open the file yet.
    path.write_text('{"@mt":"First"}\ninvalid json\n', encoding="utf-8")

    assert next(events).message_template == "First"
    with pytest.raises(json.JSONDecodeError):
        next(events)


def test_read_file_empty_file(tmp_path):
    path = tmp_path / "empty.clef"
    path.write_text("", encoding="utf-8")

    assert list(read_file(path)) == []


@pytest.mark.parametrize(
    "invalid_line",
    ["invalid json", "[]", '{"@t":"bad date"}', '{"@l":"unknown"}', ""],
)
def test_read_file_tolerates_invalid_lines_with_diagnostics(
    tmp_path, caplog, invalid_line
):
    path = tmp_path / "mixed.clef"
    path.write_text(
        '{"@mt":"First"}\n' + invalid_line + '\n{"@mt":"Last"}\n',
        encoding="utf-8",
    )

    events = list(read_file(path, strict=False))

    assert [event.message_template for event in events] == ["First", "Last"]
    assert [event.line_number for event in events] == [1, 3]
    assert all(event.source == str(path) for event in events)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert f"{path}:2" in record.getMessage()
    with pytest.raises(ValueError) as error:
        list(read_file(path, strict=True))
    assert str(error.value) in record.getMessage()


def test_read_file_tolerates_multiple_invalid_lines(tmp_path, caplog):
    path = tmp_path / "invalid.clef"
    path.write_text("bad\n[]\n", encoding="utf-8")

    assert list(read_file(path, strict=False)) == []
    assert len(caplog.records) == 2


def test_read_file_tolerant_mode_propagates_file_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(read_file(tmp_path / "missing.clef", strict=False))
