-- Apache HiveQL test file (syntax: hiveql)
CREATE EXTERNAL TABLE IF NOT EXISTS logs (ts TIMESTAMP, level STRING, message STRING) PARTITIONED BY (dt STRING)
STORED AS ORC LOCATION '/warehouse/logs' TBLPROPERTIES ('orc.compress' = 'SNAPPY');

LOAD DATA INPATH
  '/tmp/events.log'
INTO TABLE
  logs PARTITION (dt = '2026-09-27');

SELECT
  level,
  COUNT(1) AS cnt
FROM
  logs
WHERE
  dt = '2026-09-27'
  AND ts > '2026-09-27 00:00:00'
GROUP BY
  level
HAVING
  cnt > 100
ORDER BY
  cnt DESC
LIMIT
  20;

SELECT
  rlike ('^[A-Z]+', level) AS is_upper
FROM
  logs
LIMIT
  3;

SELECT
  a.level,
  b.cnt
FROM
  (
    SELECT
      level,
      COUNT(1) AS cnt
    FROM
      logs
    GROUP BY
      level
  ) a
  JOIN (
    SELECT
      level
    FROM
      logs
    WHERE
      level = 'ERROR'
  ) b ON a.level = b.level;

INSERT OVERWRITE DIRECTORY
  '/tmp/export'
ROW FORMAT DELIMITED
SELECT
  *
FROM
  logs
WHERE
  level = 'ERROR';
