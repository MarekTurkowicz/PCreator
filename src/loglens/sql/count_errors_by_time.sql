SELECT
    time_bucket(
        CAST(? AS INTERVAL), timestamp, TIMESTAMPTZ '1970-01-01 00:00:00+00'
    ) AS bucket_start,
    COUNT(*) AS error_count
FROM events
WHERE level IN ('Error', 'Fatal') AND timestamp IS NOT NULL
GROUP BY bucket_start
ORDER BY bucket_start;
