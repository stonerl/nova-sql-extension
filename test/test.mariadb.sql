-- CREATE TABLE
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  email VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CREATE VIEW
CREATE VIEW active_users AS
SELECT
  *
FROM
  users
WHERE
  email IS NOT NULL;

-- CREATE FUNCTION
CREATE FUNCTION get_email (name VARCHAR(100)) RETURNS VARCHAR(100) BEGIN DECLARE email_address VARCHAR(100);

SELECT
  email INTO email_address
FROM
  users
WHERE
  users.name = name;

RETURN email_address;

END;

-- CREATE PROCEDURE
CREATE PROCEDURE upsert_user (
  IN user_name VARCHAR(100),
  IN user_email VARCHAR(100)
) BEGIN IF EXISTS (
  SELECT
    1
  FROM
    users
  WHERE
    name = user_name
) THEN
UPDATE users
SET
  email = user_email
WHERE
  name = user_name;

ELSE
INSERT INTO
  users (name, email)
VALUES
  (user_name, user_email);

END IF;

END;

-- CREATE INDEX
CREATE INDEX idx_email ON users (email);

-- Folding: CASE expression
SELECT
  id,
  CASE
    WHEN email LIKE '%@example.com' THEN 'Internal'
    ELSE 'External'
  END AS email_type
FROM
  users;

-- Folding: multi-line SELECT
SELECT
  id,
  name,
  email
FROM
  users
WHERE
  created_at > NOW() - INTERVAL 30 DAY;
