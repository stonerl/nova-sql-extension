-- Apache Flink SQL test file (syntax: flinksql)
CREATE TABLE events (
  id INT,
  kind STRING,
  amount DECIMAL(10, 2),
  event_time TIMESTAMP(3),
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'events',
  'properties.bootstrap.servers' = 'localhost:9092',
  'format' = 'json'
);

CREATE TABLE hourly_totals (
  window_start TIMESTAMP(3),
  window_end TIMESTAMP(3),
  total DECIMAL(18, 2)
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://localhost:5432/warehouse'
);

INSERT INTO hourly_totals
SELECT
  window_start,
  window_end,
  SUM(amount) AS total
FROM TABLE(
  TUMBLE(TABLE events, DESCRIPTOR(event_time), INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end;

SELECT kind, amount
FROM events
MATCH_RECOGNIZE (
  PARTITION BY kind
  ORDER BY event_time
  MEASURES A.amount AS start_amount
  ONE ROW PER MATCH
  PATTERN (A B+)
  DEFINE B AS B.amount > A.amount
);
