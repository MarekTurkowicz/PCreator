SELECT timestamp, level, message_template, message, exception,
       properties, source, line_number
FROM events
WHERE (CAST(? AS TIMESTAMPTZ) IS NULL OR timestamp >= CAST(? AS TIMESTAMPTZ))
  AND (CAST(? AS TIMESTAMPTZ) IS NULL OR timestamp <= CAST(? AS TIMESTAMPTZ))
ORDER BY timestamp ASC NULLS LAST;
