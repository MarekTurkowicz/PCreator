import json

import pytest

from loglens.reader import read_file


def test_read_file_preserves_events_and_source_locations(tmp_path):
    path = tmp_path / "events.clef"
    path.write_text(
        '{"@mt":"Zażółć {Name}","Name":"Łukasz"}\n'
        '{"@l":"Error","@m":"Failed","@x":"Exception"}',
        encoding="utf-8",
    )

    events = list(read_file(path))

    assert len(events) == 2
    assert [event.source for event in events] == [str(path), str(path)]
    assert [event.line_number for event in events] == [1, 2]
    assert events[0].message_template == "Zażółć {Name}"
    assert events[0].properties == {"Name": "Łukasz"}
    assert events[1].level == "Error"
    assert events[1].message == "Failed"
    assert events[1].exception == "Exception"


def test_read_file_opens_lazily_and_accepts_string_path(tmp_path):
    path = tmp_path / "later.clef"
    events = read_file(str(path))

    path.write_text('{}\n', encoding="utf-8")

    assert next(events).line_number == 1
    with pytest.raises(StopIteration):
        next(events)


def test_read_file_parses_only_requested_lines(tmp_path):
    path = tmp_path / "events.clef"
    path.write_text('{"@mt":"First"}\ninvalid JSON\n', encoding="utf-8")
    events = read_file(path)

    assert next(events).message_template == "First"
    with pytest.raises(json.JSONDecodeError):
        next(events)


def test_read_empty_file(tmp_path):
    path = tmp_path / "empty.clef"
    path.write_text("", encoding="utf-8")

    assert list(read_file(path)) == []
