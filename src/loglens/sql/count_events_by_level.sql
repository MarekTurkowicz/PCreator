SELECT level, COUNT(*) AS event_count
FROM events
GROUP BY level
ORDER BY level;
