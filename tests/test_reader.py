"""Streaming CLEF file reading and input locations."""

import json

import pytest

from loglens.clef import read_file


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
