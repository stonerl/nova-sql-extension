-- Trino (Presto) test file (syntax: trino)
CREATE TABLE memory.default.events (id BIGINT, kind VARCHAR, amount DOUBLE);

CREATE MATERIALIZED VIEW mv_totals AS
SELECT
  kind,
  SUM(amount) AS total
FROM
  events
GROUP BY
  kind;

SELECT
  kind,
  amount,
  ROW_NUMBER() OVER (
    PARTITION BY
      kind
    ORDER BY
      amount DESC
  ) AS rnk
FROM
  events
WHERE
  kind IN ('click', 'view')
GROUP BY
  kind,
  amount
HAVING
  COUNT(*) > 2
ORDER BY
  rnk
FETCH FIRST
  10 ROWS
WITH
  TIES;

SELECT
  id,
  CAST(amount AS DECIMAL(10, 2)) AS amount2
FROM
  events
WHERE
  amount IS NOT NULL
OFFSET
  5;

PREPARE stmt
FROM
SELECT
  *
FROM
  events
WHERE
  kind = ?;

EXECUTE stmt USING 'click';

EXPLAIN ANALYZE
SELECT
  *
FROM
  events;

SHOW TABLES
FROM
  memory.default;
