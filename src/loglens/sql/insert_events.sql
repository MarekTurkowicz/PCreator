INSERT INTO events (
    timestamp, level, message_template, message, exception,
    properties, source, line_number
) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
