WITH durations AS (
    SELECT
        timestamp,
        json_extract_string(properties, '$.RequestPath') AS endpoint,
        TRY_CAST(json_extract(properties, '$.Elapsed') AS DOUBLE) AS elapsed_ms
    FROM events
    WHERE timestamp IS NOT NULL
        AND json_type(properties, '$.RequestPath') = 'VARCHAR'
        AND json_type(properties, '$.Elapsed') IN ('BIGINT', 'UBIGINT', 'DOUBLE')
)
SELECT
    endpoint,
    time_bucket(
        CAST(? AS INTERVAL), timestamp, TIMESTAMPTZ '1970-01-01 00:00:00+00'
    ) AS bucket_start,
    quantile_cont(elapsed_ms, 0.95) AS p95
FROM durations
WHERE regexp_matches(endpoint, '\S')
    AND isfinite(elapsed_ms)
    AND elapsed_ms >= 0
GROUP BY endpoint, bucket_start
HAVING COUNT(*) >= ?
ORDER BY endpoint, bucket_start;
