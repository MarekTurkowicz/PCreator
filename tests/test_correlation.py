"""Look up stored CLEF events for a single correlation ID."""

import pytest

duckdb = pytest.importorskip("duckdb")

from loglens.clef import read_file  # noqa: E402
from loglens.database import (  # noqa: E402
    create_schema,
    find_events_by_correlation_id,
    insert_events,
)


def test_find_events_isolates_requests(tmp_path):
    path = tmp_path / "requests.clef"
    path.write_text(
        '{"@m":"Finished","CorrelationId":"42"}\n'
        '{"@m":"Other request","CorrelationId":"420"}\n'
        '{"@m":"Started","CorrelationId":"42"}\n'
        '{"@m":"Numeric ID","CorrelationId":42}\n'
        '{"@m":"Missing ID","RequestId":"42"}\n',
        encoding="utf-8",
    )
    events = list(read_file(path))
    with duckdb.connect() as connection:
        create_schema(connection)
        insert_events(connection, events)

        matches = find_events_by_correlation_id(connection, "42")

        assert sorted(event.line_number for event in matches) == [1, 3]
        assert all(event.source == str(path) for event in matches)
        assert find_events_by_correlation_id(connection, "420") == [events[1]]
        assert find_events_by_correlation_id(connection, "unknown") == []
