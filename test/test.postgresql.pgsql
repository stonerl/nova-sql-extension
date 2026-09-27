-- PostgreSQL test file (syntax: postgresql)
-- v0.3.11 grammar: policies, materialized views, procedures
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
  owner TEXT NOT NULL,
  balance NUMERIC(12, 2) DEFAULT 0 CHECK (balance >= 0),
  tags TEXT[]
);

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY account_owner ON accounts FOR ALL TO app_user USING (owner = CURRENT_USER)
WITH
  CHECK (owner = CURRENT_USER);

CREATE MATERIALIZED VIEW rich_accounts AS
SELECT
  owner,
  SUM(balance) AS total
FROM
  accounts
GROUP BY
  owner;

REFRESH MATERIALIZED VIEW CONCURRENTLY rich_totals;

CREATE OR REPLACE PROCEDURE transfer (from_id UUID, to_id UUID, amount NUMERIC) LANGUAGE plpgsql AS $$
BEGIN
  UPDATE accounts SET balance = balance - 1 WHERE id = from_id;
  UPDATE accounts SET balance = balance + 1 WHERE id = to_id;
END;
$$;

SELECT
  a.owner,
  a.balance::text
FROM
  accounts a
WHERE
  a.tags && ARRAY['vip']
ORDER BY
  a.balance DESC NULLS LAST
LIMIT
  10;

-- dollar-quoted string
SELECT
  $tag$raw string with 'quotes'$tag$::text;
