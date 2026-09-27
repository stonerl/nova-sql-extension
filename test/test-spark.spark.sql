-- Apache Spark SQL test file (syntax: sparksql)
CREATE TABLE IF NOT EXISTS events (
  id BIGINT,
  kind STRING,
  payload MAP < STRING,
  STRING >,
  occurred_at TIMESTAMP
) USING DELTA PARTITIONED BY (kind) COMMENT 'events table';

CREATE TEMPORARY VIEW tmp_events AS
SELECT
  *
FROM
  events
WHERE
  kind = 'click';

SELECT
  kind,
  EXPLODE (MAP_KEYS(payload)) AS key,
  COUNT(1) OVER (
    PARTITION BY
      kind
    ORDER BY
      id ROWS BETWEEN 2 PRECEDING
      AND CURRENT ROW
  ) AS roll
FROM
  events
LATERAL VIEW explode (payload) t AS k,
v
WHERE
  id BETWEEN 1 AND 100
DISTRIBUTE BY
  kind
SORT BY
  id DESC
LIMIT
  100;

INSERT INTO TABLE
  tmp_events
SELECT
  *
FROM
  events
WHERE
  id % 2 = 0;

CACHE TABLE tmp_events;

UNCACHE TABLE tmp_events;

SET spark.sql.shuffle.partitions = 200;

REFRESH TABLE tmp_events;
