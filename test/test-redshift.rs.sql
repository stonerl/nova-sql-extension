-- Amazon Redshift test file (syntax: redshift)
CREATE TABLE sales (
  sale_id BIGINT IDENTITY (1, 1),
  account_id INTEGER NOT NULL,
  amount DECIMAL(12, 2) NOT NULL,
  distkey INTEGER DISTKEY,
  sortkey TIMESTAMP
) DISTSTYLE KEY DISTKEY (account_id) SORTKEY (amount, sortkey);

CREATE VIEW top_accounts AS
WITH
  ranked AS (
    SELECT
      account_id,
      SUM(amount) AS total,
      DENSE_RANK() OVER (
        ORDER BY
          SUM(amount) DESC
      ) AS rnk
    FROM
      sales
    GROUP BY
      account_id
  )
SELECT
  *
FROM
  ranked
WHERE
  rnk <= 10;

SELECT
  account_id,
  LISTAGG(amount, ', ') WITHIN GROUP (
    ORDER BY
      amount
  ) AS amounts
FROM
  sales
WHERE
  amount LIKE '%'
GROUP BY
  account_id;

UNLOAD ('SELECT * FROM sales') TO 's3://bucket/sales_' CREDENTIALS 'aws_access_key_id=XXX;aws_secret_access_key=YYY' DELIMITER '|' GZIP;
