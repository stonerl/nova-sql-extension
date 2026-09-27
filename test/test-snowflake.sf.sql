-- Snowflake test file (syntax: snowflake)
CREATE WAREHOUSE IF NOT EXISTS wh_dev WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;

CREATE TABLE db.schema.users (
  id NUMBER(38, 0) AUTOINCREMENT,
  name VARCHAR(100),
  variant_col VARIANT,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY
  (loaded_at);

CREATE STAGE IF NOT EXISTS my_stage URL = 's3://bucket/prefix/' FILE_FORMAT = (TYPE = PARQUET);

COPY INTO db.schema.users (name) FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1);

SELECT
  id,
  name,
  variant_col:type::STRING AS
tag
,
  LAG(loaded_at) OVER (
    PARTITION BY
      name
    ORDER BY
      loaded_at
  ) AS prev_load
FROM
  db.schema.users
WHERE
  loaded_at > DATEADD(day, -7, CURRENT_TIMESTAMP())
QUALIFY
  prev_load IS NULL;

CREATE TASK t_refresh WAREHOUSE = wh_dev SCHEDULE = 'USING CRON 0 * * * * UTC' AS
INSERT INTO
  audit
SELECT
  id
FROM
  db.schema.users;

ALTER TASK t_resume RESUME;

SET
  val = 42;

SELECT
  $val;
