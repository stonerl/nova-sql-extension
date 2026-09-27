-- SingleStore test file (syntax: singlestore)
-- v0.3.11 grammar: SPLIT TABLETS, INCLUDE (covering index)
CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100),
  email VARCHAR(255),
  amount DOUBLE DEFAULT 0,
  SHARD KEY (id),
  KEY (email)
  WITH
    METADATA,
    KEY (name, amount) /* covering */
) AUTOSTATS_CARDINALITY_MODE = PERIODIC;

SPLIT TABLES users;

ALTER TABLE users
FORCE;

INSERT INTO
  users (name, email)
VALUES
  ('Ada', 'ada@example.com')
ON DUPLICATE KEY UPDATE
  amount = amount + 1;

SELECT
  *
FROM
  users
WHERE
  name RLIKE '^A';

SELECT
  name,
  SUM(amount) AS total
FROM
  users
GROUP BY
  name
ORDER BY
  total DESC
LIMIT
  10;

SET
  GLOBAL sync_ddl_mode = 'OFF';

CREATE DATABASE IF NOT EXISTS shop;
