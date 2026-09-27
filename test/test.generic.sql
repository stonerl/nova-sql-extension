-- Generic ANSI SQL test file (syntax: sql-generic)
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users (email);

INSERT INTO
  users (id, name, email)
VALUES
  (1, 'Ada', 'ada@example.com');

SELECT
  u.name,
  COUNT(o.id) AS orders
FROM
  users u
  JOIN orders o ON o.user_id = u.id
WHERE
  u.active = true
GROUP BY
  u.name
HAVING
  COUNT(o.id) > 5
ORDER BY
  orders DESC
LIMIT
  10;

UPDATE users
SET
  name = 'Grace'
WHERE
  id = 1;

DELETE FROM users
WHERE
  active = false;

WITH
  totals AS (
    SELECT
      user_id,
      SUM(amount) AS total
    FROM
      payments
    GROUP BY
      user_id
  )
SELECT
  *
FROM
  totals
WHERE
  total > 100;

SELECT
  CASE
    WHEN score >= 90 THEN 'A'
    ELSE 'F'
  END AS grade
FROM
  results;

-- multi-line comment test
/*
spanning
lines
*/
SELECT
  1;
