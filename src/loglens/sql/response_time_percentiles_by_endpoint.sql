WITH durations AS (
    SELECT
        json_extract_string(properties, '$.RequestPath') AS endpoint,
        TRY_CAST(json_extract(properties, '$.Elapsed') AS DOUBLE) AS elapsed_ms
    FROM events
    WHERE json_type(properties, '$.RequestPath') = 'VARCHAR'
        AND json_type(properties, '$.Elapsed') IN ('BIGINT', 'UBIGINT', 'DOUBLE')
)
SELECT
    endpoint,
    quantile_cont(elapsed_ms, 0.50) AS p50,
    quantile_cont(elapsed_ms, 0.95) AS p95,
    quantile_cont(elapsed_ms, 0.99) AS p99
FROM durations
WHERE regexp_matches(endpoint, '\S')
    AND isfinite(elapsed_ms)
    AND elapsed_ms >= 0
GROUP BY endpoint
ORDER BY endpoint;
