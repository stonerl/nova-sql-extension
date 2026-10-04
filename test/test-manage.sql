-- Generic ANSI SQL test file (syntax: sql-generic)
-- Object management statements (GRANT / REVOKE / USE / DESCRIBE / …)

USE mydb;
USE ROLE etl_admin;

GRANT SELECT ON users TO analyst_role;
GRANT INSERT, UPDATE ON reporting.monthly_stats TO user_a, user_b;
GRANT ALL PRIVILEGES ON DATABASE mydb TO admin_role WITH GRANT OPTION;
GRANT USAGE ON SCHEMA reporting TO PUBLIC;
GRANT SELECT (id, name) ON users TO readonly_role;
GRANT ROLE etl_developer TO ROLE etl_admin;

REVOKE SELECT ON users FROM analyst_role;
REVOKE ALL PRIVILEGES ON reporting.monthly_stats FROM user_a CASCADE;
REVOKE GRANT OPTION FOR SELECT ON users FROM readonly_role;
REVOKE ROLE etl_developer FROM ROLE etl_admin;

DESCRIBE users;
DESC users;
DESC TABLE users;

CALL refresh_stats(42);
EXEC usp_refresh_daily;
EXECUTE audit_log_writer(event_type);

LOCK TABLES monthly_stats READ, users WRITE;
UNLOCK TABLES;

KILL 42;
KILL QUERY 7;
CHECKPOINT;

LOAD DATA LOCAL INFILE '/tmp/import.csv' INTO TABLE users;
LOAD DATA INPATH '/tmp/import.csv' OVERWRITE INTO TABLE users;

SHOW DATABASES;
SHOW GRANTS FOR analyst_role;
SHOW FULL GRANTS FOR ROLE etl_admin;
