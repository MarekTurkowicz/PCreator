CREATE TABLE IF NOT EXISTS events (
    timestamp TIMESTAMPTZ,
    level VARCHAR,
    message_template VARCHAR,
    message VARCHAR,
    exception VARCHAR,
    properties JSON,
    source VARCHAR,
    line_number BIGINT
);
