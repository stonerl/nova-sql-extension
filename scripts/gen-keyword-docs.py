#!/usr/bin/env python3
"""Generate keyword hover documentation for the patched sqls language server.

Reads sqls' own dialect/keyword.go (the authoritative keyword vocabulary the
lexer matches against) and emits internal/handler/keyword_docs.go containing
a `keywordDocs` map[string]string with Markdown hover content.

Tiers:
  T1 (~70)  rich docs: classification, description, example, vendor-docs link
  T2 (~180) one-line docs
  T3 (rest) auto-classified one-liners by curated category sets
  EXTRA (~70) grammar-vocabulary words absent from sqls' dialect tables

Original wording throughout — no verbatim third-party documentation.
"""

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# T1 — rich documentation (statements + core clauses)
# --------------------------------------------------------------------------

T1 = {
    "SELECT": """**SQL statement** — retrieves rows from one or more tables or views. The most fundamental DML statement.

```sql
SELECT id, name FROM users WHERE active = true ORDER BY name;
```

Docs: [PostgreSQL: SELECT](https://www.postgresql.org/docs/current/sql-select.html) · [MySQL: SELECT](https://dev.mysql.com/doc/refman/8.0/en/select.html)""",
    "FROM": """**SQL clause** — specifies the source tables, views or sub-queries a query reads from. Follows the select list in `SELECT` statements.

```sql
SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id;
```

Docs: [PostgreSQL: FROM](https://www.postgresql.org/docs/current/sql-select.html#SQL-FROM)""",
    "WHERE": """**SQL clause** — filters rows using a boolean condition. Rows failing the predicate are excluded from the result (or from the DML operation).

```sql
DELETE FROM sessions WHERE expires_at < NOW();
```

Docs: [PostgreSQL: WHERE](https://www.postgresql.org/docs/current/sql-select.html)""",
    "GROUP BY": """**SQL clause** — groups rows sharing common values so aggregate functions (`COUNT`, `SUM`, …) compute one result per group. Non-aggregated columns must appear in the group list.

```sql
SELECT department, COUNT(*) FROM employees GROUP BY department;
```

Docs: [PostgreSQL: GROUP BY](https://www.postgresql.org/docs/current/tutorial-agg.html)""",
    "HAVING": """**SQL clause** — filters the results of aggregation, applied after `GROUP BY`. Unlike `WHERE`, it can reference aggregate function results.

```sql
SELECT country, COUNT(*) FROM users GROUP BY country HAVING COUNT(*) > 100;
```

Docs: [PostgreSQL: HAVING](https://www.postgresql.org/docs/current/tutorial-agg.html#TUTORIAL-HAVING)""",
    "ORDER BY": """**SQL clause** — sorts the result rows. Each sort key can be qualified `ASC` (ascending, default) or `DESC` (descending).

```sql
SELECT * FROM products ORDER BY price DESC, name ASC;
```

Docs: [PostgreSQL: ORDER BY](https://www.postgresql.org/docs/current/queries-order.html)""",
    "LIMIT": """**SQL clause** — restricts the number of rows returned. Composable with `OFFSET` for paging (dialect-dependent syntax).

```sql
SELECT * FROM logs ORDER BY created_at DESC LIMIT 50;
```

Docs: [PostgreSQL: LIMIT](https://www.postgresql.org/docs/current/queries-limit.html)""",
    "OFFSET": """**SQL clause** — skips the first *n* rows before returning results. Used with `LIMIT` for pagination.

```sql
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 40;
```

Docs: [PostgreSQL: LIMIT](https://www.postgresql.org/docs/current/queries-limit.html)""",
    "JOIN": """**SQL clause** — combines rows from two relations based on a join condition. Variants (`INNER`, `LEFT`, `RIGHT`, `FULL`, `CROSS`) control which unmatched rows survive.

```sql
SELECT o.id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

Docs: [PostgreSQL: Joins](https://www.postgresql.org/docs/current/tutorial-join.html)""",
    "ON": """**SQL clause** — defines the join condition or (in some dialects) a filter for index/trigger/foreign-key behavior. In joins it pairs rows from the two relations.

```sql
SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id;
```

Docs: [PostgreSQL: Joins](https://www.postgresql.org/docs/current/tutorial-join.html)""",
    "USING": """**SQL clause** — shorthand join condition for columns sharing the same name in both relations. `USING (id)` is equivalent to `ON a.id = b.id` and merges the join column into one output column.

```sql
SELECT * FROM orders JOIN customers USING (customer_id);
```

Docs: [PostgreSQL: USING](https://www.postgresql.org/docs/current/sql-select.html)""",
    "INSERT": """**SQL statement** — inserts new rows into a table. Accepts explicit `VALUES`, an `INSERT ... SELECT` result set, or `DEFAULT VALUES`.

```sql
INSERT INTO users (name, email) VALUES ('Ada', 'ada@example.com');
```

Docs: [PostgreSQL: INSERT](https://www.postgresql.org/docs/current/sql-insert.html)""",
    "INTO": """**SQL keyword** — target clause of `INSERT`, `SELECT ... INTO`, and `MERGE` statements. In `INSERT` it names the receiving table and columns.

```sql
INSERT INTO audit_log (action, at) VALUES ('login', NOW());
```

Docs: [PostgreSQL: INSERT](https://www.postgresql.org/docs/current/sql-insert.html)""",
    "VALUES": """**SQL clause** — supplies the row expressions for `INSERT`, or a standalone row-set constructor in dialects that support it (PostgreSQL: `VALUES` can be queried like a table).

```sql
INSERT INTO settings (key, value) VALUES ('theme', 'dark'), ('lang', 'en');
```

Docs: [PostgreSQL: VALUES](https://www.postgresql.org/docs/current/sql-values.html)""",
    "UPDATE": """**SQL statement** — modifies values of existing rows matching the `WHERE` condition. Without `WHERE`, every row is updated.

```sql
UPDATE products SET price = price * 1.1 WHERE category = 'electronics';
```

Docs: [PostgreSQL: UPDATE](https://www.postgresql.org/docs/current/sql-update.html)""",
    "SET": """**SQL clause** — assigns new values to columns in `UPDATE`, or configures session/connection state (`SET NAMES`, `SET TRANSACTION`, `SET LOCAL` depending on dialect).

```sql
UPDATE users SET last_login = NOW() WHERE id = 42;
```

Docs: [PostgreSQL: UPDATE](https://www.postgresql.org/docs/current/sql-update.html)""",
    "DELETE": """**SQL statement** — removes rows matching the `WHERE` condition from a table. Without `WHERE`, all rows are deleted (see also `TRUNCATE`).

```sql
DELETE FROM sessions WHERE expires_at < NOW();
```

Docs: [PostgreSQL: DELETE](https://www.postgresql.org/docs/current/sql-delete.html)""",
    "CREATE": """**SQL statement keyword** — prefix of data-definition (DDL) statements that create objects: `CREATE TABLE`, `CREATE VIEW`, `CREATE INDEX`, `CREATE DATABASE`, `CREATE USER`, `CREATE FUNCTION` and more.

```sql
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);
```

Docs: [PostgreSQL: CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)""",
    "ALTER": """**SQL statement keyword** — prefix of DDL statements that modify existing objects: `ALTER TABLE`, `ALTER VIEW`, `ALTER INDEX`, `ALTER DATABASE` and more.

```sql
ALTER TABLE users ADD COLUMN bio TEXT;
```

Docs: [PostgreSQL: ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)""",
    "DROP": """**SQL statement keyword** — prefix of DDL statements that destroy objects and their data: `DROP TABLE`, `DROP VIEW`, `DROP INDEX`, `DROP DATABASE` and more. Often supports `IF EXISTS` and `CASCADE`.

```sql
DROP TABLE IF EXISTS old_logs;
```

Docs: [PostgreSQL: DROP TABLE](https://www.postgresql.org/docs/current/sql-droptable.html)""",
    "TABLE": """**SQL keyword** — names a table object. Appears in `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `TRUNCATE TABLE` and (PostgreSQL/MySQL 8) as the `TABLE` statement shorthand for `SELECT * FROM`.

```sql
CREATE TABLE users (id INT PRIMARY KEY);
```

Docs: [PostgreSQL: CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)""",
    "VIEW": """**SQL keyword** — names a view (a stored query exposed as a virtual table) in `CREATE VIEW`, `DROP VIEW`, `ALTER VIEW`.

```sql
CREATE VIEW active_users AS SELECT * FROM users WHERE active = true;
```

Docs: [PostgreSQL: CREATE VIEW](https://www.postgresql.org/docs/current/sql-createview.html)""",
    "INDEX": """**SQL keyword** — names an index (an access structure that speeds up lookups) in `CREATE INDEX`, `ALTER INDEX`, `DROP INDEX`.

```sql
CREATE INDEX idx_users_email ON users (email);
```

Docs: [PostgreSQL: CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)""",
    "DATABASE": """**SQL keyword** — names a database (schema container) in `CREATE DATABASE`, `ALTER DATABASE`, `DROP DATABASE`, `USE DATABASE`.

```sql
CREATE DATABASE shop;
```

Docs: [PostgreSQL: CREATE DATABASE](https://www.postgresql.org/docs/current/sql-createdatabase.html)""",
    "TRUNCATE": """**SQL statement** — removes all rows from a table quickly, bypassing per-row triggers. Roughly `DELETE FROM t` without `WHERE`, but typically non-logged/non-transactional in some dialects.

```sql
TRUNCATE TABLE staging_data;
```

Docs: [PostgreSQL: TRUNCATE](https://www.postgresql.org/docs/current/sql-truncate.html)""",
    "UNION": """**SQL operator** — combines the result sets of two queries into one, removing duplicate rows. Use `UNION ALL` to keep duplicates (faster). Matching column counts/types required.

```sql
SELECT name FROM customers
UNION
SELECT name FROM suppliers;
```

Docs: [PostgreSQL: UNION](https://www.postgresql.org/docs/current/queries-union.html)""",
    "UNION ALL": """**SQL operator** — combines result sets of two queries, keeping duplicate rows. Cheaper than `UNION` because no dedup pass is required.

```sql
SELECT name FROM customers
UNION ALL
SELECT name FROM suppliers;
```

Docs: [PostgreSQL: UNION](https://www.postgresql.org/docs/current/queries-union.html)""",
    "WITH": """**SQL clause** — defines Common Table Expressions (CTEs): named, optional temporary result sets readable by the main statement. Improves readability and enables recursion with `RECURSIVE`.

```sql
WITH totals AS (
  SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id
)
SELECT * FROM totals WHERE total > 1000;
```

Docs: [PostgreSQL: WITH](https://www.postgresql.org/docs/current/queries-with.html)""",
    "RECURSIVE": """**SQL keyword** — allows a CTE to reference itself, enabling tree/graph traversal with a base (anchor) term and a recursive term. Terminate recursion with `LIMIT` or a stop condition.

```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id FROM nodes WHERE parent_id IS NULL
  UNION ALL
  SELECT n.id, n.parent_id FROM nodes n JOIN tree t ON n.parent_id = t.id
)
SELECT * FROM tree;
```

Docs: [PostgreSQL: Recursive CTEs](https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE)""",
    "AS": """**SQL keyword** — introduces an alias for tables, columns, sub-queries or CTE names. Optional in most dialects (`name alias` ≡ `name AS alias`).

```sql
SELECT COUNT(*) AS total FROM orders o AS o2;
```

Docs: [PostgreSQL: Aliases](https://www.postgresql.org/docs/current/sql-select.html#SQL-ALIASES)""",
    "DISTINCT": """**SQL keyword** — removes duplicate rows from a result set. `SELECT DISTINCT ON (col)` (PostgreSQL) keeps the first row per group.

```sql
SELECT DISTINCT country FROM users;
```

Docs: [PostgreSQL: DISTINCT](https://www.postgresql.org/docs/current/sql-select.html#SQL-DISTINCT)""",
    "CASE": """**SQL expression** — conditional logic inside queries. Simple form compares an expression to values; searched form evaluates independent boolean conditions. Ends with `END`.

```sql
SELECT name,
  CASE WHEN score >= 90 THEN 'A' ELSE 'F' END AS grade
FROM students;
```

Docs: [PostgreSQL: CASE](https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-CASE)""",
    "WHEN": """**SQL keyword** — branch marker inside `CASE` expressions: each `WHEN condition THEN result` pair is evaluated in order, first match wins.

```sql
CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' ELSE 'F' END
```

Docs: [PostgreSQL: CASE](https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-CASE)""",
    "THEN": """**SQL keyword** — separates a `CASE` branch condition from its result value (see `WHEN`).

```sql
CASE WHEN active THEN 'yes' ELSE 'no' END
```

Docs: [PostgreSQL: CASE](https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-CASE)""",
    "ELSE": """**SQL keyword** — fallback branch of `CASE` expressions and conditional execution in procedural dialects. Optional in `CASE`; default result is `NULL`.

```sql
CASE WHEN a > b THEN 'a' ELSE 'b' END
```

Docs: [PostgreSQL: CASE](https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-CASE)""",
    "END": """**SQL keyword** — terminates `CASE` expressions and (in procedural dialects) `BEGIN ... END` blocks.

```sql
CASE WHEN x THEN 1 ELSE 0 END
```

Docs: [PostgreSQL: CASE](https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-CASE)""",
    "CAST": """**SQL function/expression** — converts a value to a target data type. Standard form: `CAST(expr AS type)`; dialect shorthand `expr::type` exists in PostgreSQL.

```sql
SELECT CAST('42' AS INTEGER), CAST(price AS VARCHAR) FROM products;
```

Docs: [PostgreSQL: CAST](https://www.postgresql.org/docs/current/typeconv.html)""",
    "AND": """**Logical operator** — true only when both operands are true. Combines boolean conditions.

```sql
SELECT * FROM users WHERE active = true AND verified = true;
```

Docs: [PostgreSQL: Logical Operators](https://www.postgresql.org/docs/current/functions-logical.html)""",
    "OR": """**Logical operator** — true when at least one operand is true. `AND` binds tighter than `OR`; use parentheses to make intent explicit.

```sql
SELECT * FROM users WHERE country = 'AT' OR country = 'DE';
```

Docs: [PostgreSQL: Logical Operators](https://www.postgresql.org/docs/current/functions-logical.html)""",
    "NOT": """**Logical operator** — negates a boolean condition. Also composes into `NOT IN`, `NOT LIKE`, `NOT EXISTS`, `IS NOT NULL`.

```sql
SELECT * FROM users WHERE NOT (country = 'US');
```

Docs: [PostgreSQL: Logical Operators](https://www.postgresql.org/docs/current/functions-logical.html)""",
    "IN": """**Operator** — matches a value against a list or sub-query result. `expr IN (v1, v2, …)` is true when expr equals any element.

```sql
SELECT * FROM users WHERE country IN ('AT', 'DE', 'CH');
```

Docs: [PostgreSQL: IN](https://www.postgresql.org/docs/current/functions-comparison.html)""",
    "BETWEEN": """**Operator** — range check: `expr BETWEEN a AND b` is true when `expr >= a AND expr <= b` (inclusive bounds). Negate with `NOT BETWEEN`.

```sql
SELECT * FROM orders WHERE created_at BETWEEN '2026-01-01' AND '2026-12-31';
```

Docs: [PostgreSQL: BETWEEN](https://www.postgresql.org/docs/current/functions-comparison.html)""",
    "LIKE": """**Pattern-matching operator** — compares a string against a pattern where `%` matches any sequence and `_` matches one character. Case-sensitive in most dialects; see `ILIKE` (PostgreSQL) / `RLIKE` (MySQL) for alternatives.

```sql
SELECT * FROM users WHERE name LIKE 'Ada%';
```

Docs: [PostgreSQL: LIKE](https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-LIKE)""",
    "IS": """**Operator** — null-safe comparisons and type predicates: `IS NULL`, `IS NOT NULL`, `IS TRUE/FALSE`, `IS OF (type)`. `=` cannot compare against `NULL`.

```sql
SELECT * FROM users WHERE deleted_at IS NULL;
```

Docs: [PostgreSQL: IS NULL](https://www.postgresql.org/docs/current/functions-comparison.html#FUNCTIONS-COMPARISON-IS-NULL)""",
    "NULL": """**Literal** — the null marker: absence of a value, distinct from zero or empty string. Use `IS NULL` / `IS NOT NULL` to test; most operations propagate `NULL`.

```sql
SELECT * FROM users WHERE deleted_at IS NULL;
```

Docs: [PostgreSQL: NULL](https://www.postgresql.org/docs/current/functions-comparison.html#FUNCTIONS-COMPARISON-IS-NULL)""",
    "EXISTS": """**Operator** — boolean predicate over a sub-query: true when the sub-query returns at least one row. `NOT EXISTS` is the standard anti-join idiom.

```sql
SELECT * FROM customers c WHERE EXISTS (
  SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```

Docs: [PostgreSQL: EXISTS](https://www.postgresql.org/docs/current/functions-subquery.html)""",
    "TRANSACTION": """**SQL keyword** — marks transaction-related statements (`BEGIN TRANSACTION`, `COMMIT TRANSACTION`, `SET TRANSACTION`) and isolation modes (`READ UNCOMMITTED/COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`).

```sql
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

Docs: [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)""",
    "BEGIN": """**SQL statement** — starts a transaction block (or a procedural block in dialects with stored programs). Commit with `COMMIT`, abort with `ROLLBACK`.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

Docs: [PostgreSQL: BEGIN](https://www.postgresql.org/docs/current/sql-begin.html)""",
    "COMMIT": """**SQL statement** — ends the current transaction, making all its changes permanent and visible to other transactions.

```sql
BEGIN; UPDATE ...; COMMIT;
```

Docs: [PostgreSQL: COMMIT](https://www.postgresql.org/docs/current/sql-commit.html)""",
    "ROLLBACK": """**SQL statement** — ends the current transaction, discarding all its changes. `ROLLBACK TO SAVEPOINT` discards only part of it.

```sql
BEGIN; UPDATE ...; -- something went wrong
ROLLBACK;
```

Docs: [PostgreSQL: ROLLBACK](https://www.postgresql.org/docs/current/sql-rollback.html)""",
    "SAVEPOINT": """**SQL statement** — sets a named marker inside a transaction to which you can later `ROLLBACK TO` without discarding the whole transaction.

```sql
BEGIN; SAVEPOINT before_delete; DELETE ...; ROLLBACK TO SAVEPOINT before_delete; COMMIT;
```

Docs: [PostgreSQL: SAVEPOINT](https://www.postgresql.org/docs/current/sql-savepoint.html)""",
    "PRIMARY": """**DDL keyword** — part of `PRIMARY KEY`: a constraint marking the column(s) as the row's unique, non-null identity, usually backed by an index.

```sql
CREATE TABLE users (id INT PRIMARY KEY, email VARCHAR(255));
```

Docs: [PostgreSQL: Primary Keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-PRIMARY-KEYS)""",
    "FOREIGN": """**DDL keyword** — part of `FOREIGN KEY`: a constraint requiring values in the referencing column to exist in the referenced table's key, enforcing referential integrity.

```sql
CREATE TABLE orders (
  customer_id INT REFERENCES customers (id)
);
```

Docs: [PostgreSQL: Foreign Keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FKEYS)""",
    "KEY": """**SQL keyword** — in `PRIMARY KEY`/`FOREIGN KEY` defines identity/referential constraints; in `ON DUPLICATE KEY UPDATE` (MySQL) drives upsert behavior. In some dialects `KEY` also marks an index member in `CREATE TABLE`.

```sql
CREATE TABLE t (id INT PRIMARY KEY);
```

Docs: [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)""",
    "REFERENCES": """**DDL keyword** — target clause of a `FOREIGN KEY` constraint: names the referenced table (and optionally columns) plus referential actions (`ON DELETE CASCADE`).

```sql
CREATE TABLE orders (
  customer_id INT REFERENCES customers (id) ON DELETE CASCADE
);
```

Docs: [PostgreSQL: REFERENCES](https://www.postgresql.org/docs/current/sql-createtable.html#SQL-CREATETABLE-PARSEXPR-REFERENCES-CLAUSE)""",
    "CONSTRAINT": """**DDL keyword** — names a constraint explicitly (`CONSTRAINT name CHECK/PRIMARY KEY/FOREIGN KEY/UNIQUE`), enabling targeted `ALTER ... DROP CONSTRAINT` later.

```sql
ALTER TABLE users ADD CONSTRAINT email_unique UNIQUE (email);
```

Docs: [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)""",
    "DEFAULT": """**DDL keyword** — supplies the value used for a column when an `INSERT` omits it.

```sql
CREATE TABLE users (created_at TIMESTAMP DEFAULT NOW());
```

Docs: [PostgreSQL: Defaults](https://www.postgresql.org/docs/current/ddl-default.html)""",
    "CHECK": """**DDL keyword** — inline constraint enforcing a boolean expression over row values.

```sql
CREATE TABLE products (price NUMERIC CHECK (price >= 0));
```

Docs: [PostgreSQL: CHECK](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS)""",
    "UNIQUE": """**DDL keyword** — constraint enforcing column (or column-group) uniqueness across rows; creates an implicit index.

```sql
CREATE TABLE users (email VARCHAR(255) UNIQUE);
```

Docs: [PostgreSQL: UNIQUE](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS)""",
    "GRANT": """**SQL statement** — assigns privileges or roles to users/roles.

```sql
GRANT SELECT, INSERT ON shop.* TO app_user;
```

Docs: [PostgreSQL: GRANT](https://www.postgresql.org/docs/current/sql-grant.html)""",
    "REVOKE": """**SQL statement** — removes previously granted privileges or roles.

```sql
REVOKE INSERT ON shop.* FROM app_user;
```

Docs: [PostgreSQL: REVOKE](https://www.postgresql.org/docs/current/sql-revoke.html)""",
    "EXPLAIN": """**SQL statement** — shows the query plan without executing (or with execution + timings when `ANALYZE` follows in PostgreSQL). First stop for query-performance work.

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 7;
```

Docs: [PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/current/sql-explain.html)""",
    "USE": """**SQL statement** — selects the default database/schema for subsequent statements (MySQL family). Not standard SQL — PostgreSQL uses `\\c` / search_path instead.

```sql
USE shop;
SELECT COUNT(*) FROM orders;
```

Docs: [MySQL: USE](https://dev.mysql.com/doc/refman/8.0/en/use.html)""",
    "SHOW": """**SQL statement** — introspects server state in MySQL-family dialects: `SHOW TABLES`, `SHOW COLUMNS FROM t`, `SHOW CREATE TABLE t`, `SHOW VARIABLES LIKE ...`.

```sql
SHOW TABLES;
SHOW CREATE TABLE users;
```

Docs: [MySQL: SHOW](https://dev.mysql.com/doc/refman/8.0/en/show.html)""",
    "MERGE": """**SQL statement** — conditional upsert: matches source rows against a target table and applies `WHEN MATCHED` / `WHEN NOT MATCHED` actions (insert/update/delete).

```sql
MERGE INTO stock s USING incoming i ON s.sku = i.sku
WHEN MATCHED THEN UPDATE SET qty = s.qty + i.qty
WHEN NOT MATCHED THEN INSERT VALUES (i.sku, i.qty);
```

Docs: [PostgreSQL: MERGE](https://www.postgresql.org/docs/current/sql-merge.html)""",
    "RETURNING": """**SQL clause** (PostgreSQL / MariaDB / SQLite) — makes DML statements output the affected rows, avoiding a follow-up `SELECT`.

```sql
INSERT INTO users (name) VALUES ('Ada') RETURNING id;
```

Docs: [PostgreSQL: RETURNING](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT)""",
    "ASC": """**Sort qualifier** — ascending order (default) for `ORDER BY` and index definitions.

```sql
SELECT * FROM products ORDER BY name ASC;
```

Docs: [PostgreSQL: ORDER BY](https://www.postgresql.org/docs/current/queries-order.html)""",
    "DESC": """**Sort qualifier** — descending order for `ORDER BY` and index definitions.

```sql
SELECT * FROM products ORDER BY price DESC;
```

Docs: [PostgreSQL: ORDER BY](https://www.postgresql.org/docs/current/queries-order.html)""",
}

# --------------------------------------------------------------------------
# T2 — one-line documentation
# --------------------------------------------------------------------------

T2 = {
    "LEFT": "**Join/keyword** — `LEFT [OUTER] JOIN`: keeps all rows from the left relation, NULL-extended where no match exists.",
    "RIGHT": "**Join/keyword** — `RIGHT [OUTER] JOIN`: keeps all rows from the right relation, NULL-extended where no match exists.",
    "FULL": "**Join/keyword** — `FULL [OUTER] JOIN`: keeps rows from both sides, NULL-extending unmatched ones.",
    "INNER": "**Join/keyword** — `INNER JOIN`: only rows with a matching pair on both sides.",
    "OUTER": "**Join/keyword** — optional word in `LEFT/RIGHT/FULL OUTER JOIN`; has no semantic effect.",
    "CROSS": "**Join/keyword** — `CROSS JOIN`: cartesian product of both relations (no join condition).",
    "NATURAL": "**Join/keyword** — `NATURAL JOIN`: joins on all identically named columns (use sparingly).",
    "HAVING": "**SQL clause** — post-aggregation row filter applied after `GROUP BY`.",
    "BY": "**SQL keyword** — marks the grouping/sorting specification (`GROUP BY`, `ORDER BY`) or partition rules.",
    "ALL": "**Keyword** — keeps duplicates in `UNION ALL`, asserts a predicate over every row (`ALL (subquery)`), or grants all privileges.",
    "ANY": "**Operator** — true if the comparison holds for at least one element of the sub-query/array result.",
    "SOME": "**Operator** — synonym of `ANY`.",
    "LIKE": "**Pattern operator** — `%`/`_` wildcard string comparison (case-sensitive in most dialects).",
    "RLIKE": "**Pattern operator** (MySQL family) — regex-based string match; synonym of `REGEXP`.",
    "REGEXP": "**Pattern operator** — regular-expression string match (MySQL family); synonym of `RLIKE`.",
    "ILIKE": "**Pattern operator** (PostgreSQL) — case-insensitive `LIKE`.",
    "SIMILAR": "**Pattern operator** — `SIMILAR TO`: SQL-standard regex-ish pattern match (PostgreSQL).",
    "ESCAPE": "**String clause** — defines the escape character for `LIKE`-family patterns (default `\\`).",
    "DIV": "**Arithmetic operator** (MySQL) — integer division (`7 DIV 2` → 3).",
    "MOD": "**Arithmetic operator** — modulo/remainder (`9 MOD 4` → 1); function synonym `MOD(a, b)`.",
    "XOR": "**Logical operator** — exclusive-or: true when exactly one operand is true.",
    "COLLATE": "**Keyword** — applies an explicit collation to an expression, column or index for comparison/sorting.",
    "CHARACTER": "**Keyword** — `CHARACTER SET`/`CHARACTER VARYING` (standard spellings of charset and VARCHAR).",
    "CHARSET": "**Keyword** (MySQL) — alias of `CHARACTER SET`; sets string charset.",
    "CASCADE": "**Referential action** — propagate parent changes to children (`ON DELETE CASCADE`, `DROP ... CASCADE`).",
    "RESTRICT": "**Referential action** — reject parent change when children exist (`ON DELETE RESTRICT`).",
    "NO": "**Keyword** — in `NO ACTION` (deferred FK check default) and `NO WRITE` variants.",
    "ACTION": "**Keyword** — completes `NO ACTION` referential action for foreign keys.",
    "DEFERRABLE": "**Constraint keyword** (PostgreSQL) — FK/constraint checks may be postponed to transaction commit.",
    "DEFERRED": "**Constraint keyword** — with `INITIALLY DEFERRED`: check fires at COMMIT, not per statement.",
    "IMMEDIATE": "**Constraint keyword** — with `INITIALLY IMMEDIATE`: check fires per statement (default).",
    "INITIALLY": "**Constraint keyword** — declares a deferrable constraint's initial mode.",
    "UNSIGNED": "**Type modifier** (MySQL) — numeric type accepts only non-negative values, doubling the positive range.",
    "SIGNED": "**Type modifier** (MySQL) — default numeric signedness; also in `CAST(... AS SIGNED)`.",
    "ZEROFILL": "**Type modifier** (MySQL, deprecated) — pads numeric display with leading zeros to full width.",
    "AUTO_INCREMENT": "**Column attribute** (MySQL) — generates sequential values for the column; PostgreSQL equivalent is `GENERATED ... AS IDENTITY`/`SERIAL`.",
    "COMMENT": "**Keyword** — inline column/table comment (MySQL); also a statement to manage comments.",
    "IF": "**Keyword** — conditional guards: `DROP TABLE IF EXISTS`, procedural `IF ... THEN`, functions `IF(cond, a, b)` / `IFNULL`.",
    "NOT": "**Logical operator** — negation; composes `NOT IN`, `NOT LIKE`, `IS NOT NULL`, `NOT EXISTS`.",
    "DUPLICATE": "**Keyword** (MySQL) — `ON DUPLICATE KEY UPDATE` upsert clause; `INSERT IGNORE` counterpart.",
    "IGNORE": "**Keyword** (MySQL) — demotes certain errors to warnings during DML (`INSERT IGNORE`, `UPDATE IGNORE`).",
    "LOW_PRIORITY": "**Keyword** (MySQL, deprecated) — delays the DML statement until no other readers.",
    "HIGH_PRIORITY": "**Keyword** (MySQL) — boosts scheduling priority of the statement.",
    "DELAYED": "**Keyword** (MySQL, deprecated) — buffered insert scheduling.",
    "STRAIGHT_JOIN": "**Join hint** (MySQL) — forces the optimizer's table order for joins.",
    "SQL_CALC_FOUND_ROWS": "**Keyword** (MySQL, deprecated) — computes the total row count alongside a LIMITed query.",
    "STRAIGHT": "**Hint fragment** (MySQL) — part of `STRAIGHT_JOIN`.",
    "QUICK": "**Modifier** — `DELETE QUICK` (MySQL): leaves space in index for reuse.",
    "PARTITION": "**Keyword** — partition selection (`SELECT ... PARTITION (p0)`), management in DDL (`ALTER TABLE ... PARTITION BY ...`).",
    "PARTITIONS": "**Keyword** — counts/displays partitions (`SHOW PARTITIONS`, `PARTITIONS` option).",
    "SUBPARTITION": "**Keyword** — sub-partitioning (composite partitioned tables, MySQL).",
    "TABLESPACE": "**Keyword** — assigns a table to a storage tablespace (PostgreSQL/MySQL/SingleStore).",
    "ENGINE": "**Keyword** (MySQL) — storage engine selection in `CREATE TABLE ... ENGINE=InnoDB`.",
    "CHARACTER_SET": "**Keyword fragment** (MySQL) — charset clause in DDL.",
    "VARCHAR": "**Data type** — variable-length character string with a maximum length.",
    "CHAR": "**Data type** — fixed-length character string, blank-padded.",
    "TEXT": "**Data type** — variable-length large text (MySQL TEXT family; PostgreSQL unbounded text).",
    "TINYTEXT": "**Data type** (MySQL) — text up to 255 bytes.",
    "MEDIUMTEXT": "**Data type** (MySQL) — text up to ~16 MB.",
    "LONGTEXT": "**Data type** (MySQL) — text up to ~4 GB.",
    "BLOB": "**Data type** — binary large object; MySQL size family (TINY/MEDIUM/LONG BLOB).",
    "TINYBLOB": "**Data type** (MySQL) — BLOB up to 255 bytes.",
    "MEDIUMBLOB": "**Data type** (MySQL) — BLOB up to ~16 MB.",
    "LONGBLOB": "**Data type** (MySQL) — BLOB up to ~4 GB.",
    "BINARY": "**Data type/keyword** — fixed-length byte string; also `BINARY` collation operator (byte-wise compare).",
    "VARBINARY": "**Data type** — variable-length byte string.",
    "INT": "**Data type** — integer (MySQL aliases: INTEGER, TINYINT, SMALLINT, MEDIUMINT, BIGINT).",
    "INTEGER": "**Data type** — standard-spelling integer.",
    "TINYINT": "**Data type** (MySQL) — 1-byte integer (0-255 unsigned).",
    "SMALLINT": "**Data type** — 2-byte integer.",
    "MEDIUMINT": "**Data type** (MySQL) — 3-byte integer.",
    "BIGINT": "**Data type** — 8-byte integer.",
    "FLOAT": "**Data type** — single-precision floating point.",
    "DOUBLE": "**Data type** — double-precision floating point (MySQL: `DOUBLE PRECISION`).",
    "REAL": "**Data type** — SQL-standard floating point (mapping is dialect-dependent).",
    "DECIMAL": "**Data type** — exact fixed-point numeric with scale/precision (alias `NUMERIC`).",
    "NUMERIC": "**Data type** — exact numeric, standard spelling of DECIMAL.",
    "DATE": "**Data type** — calendar date without time.",
    "DATETIME": "**Data type** — date and wall-clock time without timezone.",
    "TIMESTAMP": "**Data type** — date/time, often timezone-normalized (MySQL: UTC-stored).",
    "TIME": "**Data type** — time of day or duration.",
    "YEAR": "**Data type** (MySQL) — 4-digit year.",
    "BOOLEAN": "**Data type** — logical true/false (stored as BOOL/SMALLINT depending on dialect).",
    "BOOL": "**Data type** — alias of BOOLEAN.",
    "JSON": "**Data type** — native JSON document storage with partial indexing in modern engines.",
    "ENUM": "**Data type** (MySQL) — string column restricted to a fixed list of values.",
    "BIT": "**Data type** — bit-field type `BIT(n)` (MySQL/PostgreSQL).",
    "UUID": "**Data type** (PostgreSQL et al.) — 128-bit universally unique identifier.",
    "SERIAL": "**Data type** (PostgreSQL) — auto-incrementing integer shorthand (`BIGSERIAL` for 8-byte).",
    "MONEY": "**Data type** (PostgreSQL/T-SQL) — currency amount with fixed fractional precision.",
    "CLOB": "**Data type** (standard/oracle-ish) — character large object.",
    "NCLOB": "**Data type** — national-charset character large object.",
    "INTERVAL": "**Data type/keyword** — duration value (`INTERVAL '1 day'`, `DATE_ADD(..., INTERVAL 3 DAY)`).",
    "ARRAY": "**Data type/keyword** — ordered collection type (PostgreSQL, ClickHouse, BigQuery...).",
    "MAP": "**Data type** (Hive/Spark/ClickHouse) — key-value collection.",
    "STRUCT": "**Data type** (Hive/Spark/ClickHouse) — nested record type.",
    "GEOMETRY": "**Data type** — spatial geometry (MySQL/Spatial).",
    "POINT": "**Data type** — 2D spatial point.",
    "LINESTRING": "**Data type** — spatial line.",
    "POLYGON": "**Data type** — spatial polygon.",
    "MULTIPOINT": "**Data type** — spatial point collection.",
    "COUNT": "**Aggregate function** — number of rows/nonnull values (`COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)`).",
    "SUM": "**Aggregate function** — arithmetic sum of non-NULL values.",
    "AVG": "**Aggregate function** — arithmetic mean of non-NULL values.",
    "MIN": "**Aggregate function** — smallest value.",
    "MAX": "**Aggregate function** — largest value.",
    "COALESCE": "**Function** — returns the first non-NULL argument; standard NULL handling tool.",
    "NULLIF": "**Function** — returns NULL when the two arguments are equal.",
    "IFNULL": "**Function** (MySQL) — returns the second argument when the first is NULL.",
    "ISNULL": "**Function** (MySQL) — boolean NULL test.",
    "IF": "**Function** (MySQL) — `IF(cond, then, else)` inline conditional.",
    "CONCAT": "**Function** — joins strings (NULL-propagating in MySQL; PostgreSQL uses `||`).",
    "SUBSTRING": "**Function** — extracts part of a string by position/length.",
    "LENGTH": "**Function** — string length in characters (MySQL: `CHAR_LENGTH` for chars).",
    "LOWER": "**Function** — lowercases a string.",
    "UPPER": "**Function** — uppercases a string.",
    "TRIM": "**Function** — strips leading/trailing (or both) spaces or given characters.",
    "REPLACE": "**Function/statement** — string replacement; MySQL also has `REPLACE INTO` upsert statement.",
    "NOW": "**Function** — current timestamp (MySQL/PG); PostgreSQL also `NOW()` at statement start.",
    "CURRENT_DATE": "**Function/keyword** — today's date.",
    "CURRENT_TIME": "**Function/keyword** — current time of day.",
    "CURRENT_TIMESTAMP": "**Function/keyword** — current date and time.",
    "CURRENT_USER": "**Function/keyword** — user name executing the statement.",
    "SESSION_USER": "**Keyword** — the authenticated session user (differs from CURRENT_USER under SET ROLE).",
    "CURRENT_ROLE": "**Keyword** (PostgreSQL) — currently active role.",
    "CAST": "**Function** — explicit type conversion `CAST(expr AS type)`.",
    "CONVERT": "**Function** — type/charset conversion (MySQL: `CONVERT(expr, type)` / T-SQL: `CONVERT(type, expr)`).",
    "EXTRACT": "**Function** — pulls a field (YEAR, MONTH, ...) from a date/time.",
    "DATEDIFF": "**Function** — difference between two dates in days.",
    "DATE_ADD": "**Function** (MySQL) — adds an interval to a date/datetime.",
    "DATE_SUB": "**Function** (MySQL) — subtracts an interval from a date/datetime.",
    "UNIX_TIMESTAMP": "**Function** (MySQL) — epoch-seconds representation.",
    "RAND": "**Function** (MySQL) — random float in [0,1); PostgreSQL: `random()`.",
    "RANDOM": "**Function** (PostgreSQL) — random float in [0,1).",
    "SQRT": "**Function** — square root.",
    "POWER": "**Function** — exponentiation `POWER(base, exp)`.",
    "ROUND": "**Function** — rounds to n decimal places.",
    "FLOOR": "**Function** — rounds down.",
    "CEIL": "**Function** — rounds up.",
    "CEILING": "**Function** — alias of CEIL.",
    "ABS": "**Function** — absolute value.",
    "LOG": "**Function** — logarithm (base-arg order is dialect-specific).",
    "LN": "**Function** — natural logarithm.",
    "EXP": "**Function** — e raised to a power.",
    "PI": "**Function** — constant π.",
    "TRUE": "**Literal** — boolean true.",
    "FALSE": "**Literal** — boolean false.",
    "AUTOINCREMENT": "**Column attribute** (SQLite) — keyword spelling of auto-increment (rarely needed; INTEGER PRIMARY KEY suffices).",
    "IF": "**Keyword** — conditional guard in procedural dialects and `IF EXISTS/IF NOT EXISTS` DDL guards.",
    "ONLINE": "**DDL keyword** (MySQL/SingleStore) — allow concurrent DML during the operation.",
    "ALGORITHM": "**DDL hint** (MySQL) — `ALTER TABLE ... ALGORITHM=INPLACE|COPY|INSTANT`.",
    "LOCK": "**Keyword** — `LOCK TABLES`/`FOR UPDATE` row locking; also DDL lock mode.",
    "SHARE": "**Lock mode** — `LOCK IN SHARE MODE` (MySQL): shared row lock for consistent reads.",
    "MODE": "**Keyword fragment** — completes lock/setting names (`LOCK IN SHARE MODE`, sql_mode references).",
    "ROW": "**Keyword** — `ROW()` value constructor, row-level clauses (`ROW_NUMBER()`), row format options.",
    "ROWS": "**Keyword** — window frame bounds (`ROWS BETWEEN ... AND ...`) and multi-row DML syntax.",
    "RANGE": "**Keyword** — window frame (`RANGE BETWEEN`), partition types (`RANGE COLUMNS`).",
    "UNBOUNDED": "**Window keyword** — frame start/end extends to all rows (`UNBOUNDED PRECEDING/FOLLOWING`).",
    "PRECEDING": "**Window keyword** — frame offset before the current row.",
    "FOLLOWING": "**Window keyword** — frame offset after the current row.",
    "CURRENT": "**Keyword fragment** — `CURRENT ROW` window frame bound; `CURRENT DATE/TIMESTAMP/USER`.",
    "OVER": "**Window keyword** — defines a window for analytic functions (`COUNT(*) OVER (PARTITION BY x)`).",
    "PARTITION_BY": "**Window fragment** — see PARTITION BY.",
    "WINDOW": "**Keyword** — named window definitions reusable by multiple functions.",
    "OVER": "**Window keyword** — applies an analytic function over a window.",
    "PERCENT": "**Keyword** — `PERCENT` option in `TOP` (T-SQL) and percentiles.",
    "FETCH": "**Clause** (standard/PG/Oracle) — `FETCH FIRST n ROWS ONLY` limit syntax.",
    "NEXT": "**Keyword** — `FETCH NEXT` in limit clauses; sequence/cursor navigation.",
    "ONLY": "**Keyword** — completes `FETCH FIRST n ROWS ONLY`; also `ONLY` for inheritance-restricted table scans (PostgreSQL).",
    "TIES": "**Keyword** — `FETCH ... WITH TIES`: include peers of the last sorted row.",
    "FOR": "**Clause** — `FOR UPDATE`/`FOR SHARE` row locking; `FOR` loops in procedural dialects.",
    "UPDATE": "**Keyword** — also the locking mode in `SELECT ... FOR UPDATE`.",
    "NOWAIT": "**Lock option** — fail immediately when rows are locked (`FOR UPDATE NOWAIT`).",
    "SKIP": "**Lock option** — `SKIP LOCKED`: ignore locked rows (queue-style workloads).",
    "LOCKED": "**Keyword fragment** — completes `SKIP LOCKED`.",
    "REPLACE": "**Statement/Function** (MySQL) — `REPLACE INTO`: delete+insert upsert; also string replacement function.",
    "DUPLICATE_KEY": "**Keyword fragment** (MySQL) — part of `ON DUPLICATE KEY UPDATE`.",
    "OPTIMIZE": "**Statement** (MySQL) — defragments/rebuilds table and index storage.",
    "ANALYZE": "**Statement/keyword** — refreshes planner statistics (`ANALYZE TABLE`, PostgreSQL `ANALYZE`).",
    "FLUSH": "**Statement** (MySQL) — reloads caches/logs/status (`FLUSH TABLES`, `FLUSH PRIVILEGES`).",
    "REPAIR": "**Statement** (MySQL, MyISAM) — repairs corrupted tables.",
    "CHECKSUM": "**Keyword** (MySQL) — table checksum verification.",
    "VACUUM": "**Statement** (PostgreSQL) — reclaims dead-tuple space; `VACUUM FULL` rewrites the table.",
    "CLUSTER": "**Statement** (PostgreSQL) — physically reorders a table by an index.",
    "REINDEX": "**Statement** (PostgreSQL) — rebuilds indexes.",
    "SCHEMA": "**Keyword** — namespace container (`CREATE SCHEMA`, `search_path`).",
    "USER": "**Keyword** — account/identity object (`CREATE USER`, `CURRENT_USER`).",
    "ROLE": "**Keyword** — security role object (PostgreSQL: users are roles).",
    "PRIVILEGES": "**Keyword** — completes `GRANT/REVOKE ... PRIVILEGES`.",
    "PASSWORD": "**Keyword** — account authentication clause (MySQL `IDENTIFIED BY`, PG `PASSWORD '...'`).",
    "IDENTIFIED": "**Keyword** (MySQL) — `CREATE USER ... IDENTIFIED BY 'pw'`.",
    "RENAME": "**Statement/keyword** — `RENAME TABLE`, `ALTER TABLE ... RENAME TO`.",
    "RENAME": "**Statement/keyword** — renames objects without recreating them.",
    "TO": "**Keyword** — rename target (`RENAME TO`), grantee (`GRANT ... TO`), cast target in some dialects.",
    "IF_EXISTS": "**DDL fragment** — see IF EXISTS.",
    "EXISTS": "**Operator** — sub-query row-presence test; `NOT EXISTS` anti-join idiom.",
    "GENERATED": "**Column keyword** — `GENERATED ALWAYS/ BY DEFAULT AS IDENTITY` (standard auto-increment) and generated columns.",
    "IDENTITY": "**Column keyword** — auto-increment sequence attached to the column (standard/PG10+).",
    "ALWAYS": "**Column keyword** — `GENERATED ALWAYS`: application-supplied values rejected.",
    "COLLATION": "**Keyword** — names a collation for a column/domain (standard spelling).",
    "PRECISION": "**Type keyword** — `DOUBLE PRECISION`, `TIMESTAMP(p)` scale specifiers.",
    "VARYING": "**Type keyword** — `CHARACTER VARYING` = VARCHAR; `BIT VARYING`.",
    "NATIONAL": "**Type keyword** — `NATIONAL CHARACTER` (NCHAR) family.",
    "NCHAR": "**Data type** — fixed-length national (Unicode) character string.",
    "NVARCHAR": "**Data type** — variable-length national character string (T-SQL/MySQL-utf8 conventions).",
    "UNSIGNED": "**Type modifier** (MySQL) — non-negative numeric constraint doubling positive range.",
    "COMMENT": "**Keyword** — inline object documentation (MySQL); PostgreSQL uses `COMMENT ON` statements.",
    "COMMENT_ON": "**Statement** (PostgreSQL) — attaches documentation to catalog objects.",
    "CASCADE": "**Referential action** — propagate deletes/updates to referencing rows.",
    "SET_NULL": "**Referential action** — sets referencing column to NULL on parent delete (see SET NULL).",
    "RESTRICT": "**Referential action** — block parent change when children exist.",
}

# NOTE: some keys intentionally shadow T1 entries (kept in T2 for reference);
# the merge order below guarantees T1 wins.

# --------------------------------------------------------------------------
# Vendor links per keyword (dialect-aware hover footer)
# --------------------------------------------------------------------------

VENDOR_LABELS = {
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "tsql": "T-SQL (Microsoft)",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery (Google)",
    "trino": "Trino",
    "flink": "Flink SQL",
    "hive": "HiveQL",
    "spark": "Spark SQL",
    "redshift": "Redshift (AWS)",
    "singlestore": "SingleStore",
    "couchbase": "N1QL (Couchbase)",
    "db2": "SQL PL (IBM DB2)",
}

# Vendor links not already present in the T1 text footers.
# Canonical, stable documentation pages only.
LINKS_EXTRA = {
    "SELECT": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/select.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/select-transact-sql",
    },
    "FROM": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/select-transact-sql",
    },
    "WHERE": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/where-transact-sql",
    },
    "GROUP BY": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/select-group-by-transact-sql",
    },
    "HAVING": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/select-having-transact-sql",
    },
    "ORDER BY": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/select.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-transact-sql",
    },
    "LIMIT": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/top-transact-sql",
    },
    "INSERT": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/insert.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/insert-transact-sql",
    },
    "INTO": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/insert.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/insert-transact-sql",
    },
    "UPDATE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/update.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/update-transact-sql",
    },
    "SET": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/set-variable.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statements-transact-sql",
    },
    "DELETE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/delete.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/delete-transact-sql",
    },
    "CREATE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/create-table.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql",
    },
    "TABLE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/create-table.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql",
    },
    "ALTER": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/alter-table.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-table-transact-sql",
    },
    "DROP": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/drop-table.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/drop-table-transact-sql",
    },
    "VIEW": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/create-view.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql",
    },
    "INDEX": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/create-index.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/create-index-transact-sql",
    },
    "DATABASE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/create-database.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/create-database-transact-sql",
    },
    "TRUNCATE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/truncate-table.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql",
    },
    "MERGE": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql",
    },
    "VALUES": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/queries/table-value-constructor-transact-sql",
    },
    "JOIN": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/join.html",
    },
    "GRANT": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/grant.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-transact-sql",
    },
    "REVOKE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/revoke.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/statements/revoke-transact-sql",
    },
    "EXPLAIN": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/explain.html",
    },
    "WITH": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/with.html",
    },
    "BEGIN": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/commit.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/begin-transaction-transact-sql",
    },
    "COMMIT": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/commit.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/commit-transaction-transact-sql",
    },
    "ROLLBACK": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/commit.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/rollback-transaction-transact-sql",
    },
    "CASE": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/case-transact-sql",
    },
    "WHEN": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/case-transact-sql",
    },
    "THEN": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/case-transact-sql",
    },
    "ELSE": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/case-transact-sql",
    },
    "END": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/case-transact-sql",
    },
    "CAST": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/cast-functions.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/functions/cast-and-convert-transact-sql",
    },
    "LIKE": {
        "mysql": "https://dev.mysql.com/doc/refman/8.0/en/string-comparison-functions.html",
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/like-transact-sql",
    },
    "IN": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/in-transact-sql",
    },
    "EXISTS": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/exists-transact-sql",
    },
    "UNION": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/set-operators-union-transact-sql",
    },
    "SAVEPOINT": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/save-transaction-transact-sql",
    },
    "TRANSACTION": {
        "tsql": "https://learn.microsoft.com/en-us/sql/t-sql/language-elements/begin-transaction-transact-sql",
    },
}

# --------------------------------------------------------------------------
# Per-vendor link tables for the remaining dialects. Only canonical pages
# on the vendor's official documentation site; URLs verified with HTTP
# HEAD requests (see scripts/check-links.py).
# --------------------------------------------------------------------------

SQLITE_URL = "https://www.sqlite.org/"
ORACLE_URL = "https://docs.oracle.com/en/database/oracle/oracle-database/19/"
SNOWFLAKE_URL = "https://docs.snowflake.com/en/sql-reference/"
BQ_URL = "https://cloud.google.com/bigquery/docs/reference/standard-sql/"
TRINO_URL = "https://trino.io/docs/current/sql/"
FLINK_URL = "https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/sql/"
HIVE_URL = "https://cwiki.apache.org/confluence/display/Hive/"
SPARK_URL = "https://spark.apache.org/docs/latest/"
REDSHIFT_URL = "https://docs.aws.amazon.com/redshift/latest/dg/"
SINGLESTORE_URL = "https://docs.singlestore.com/db/v8.7/reference/"
COUCHBASE_URL = "https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/"
DB2_URL = "https://www.ibm.com/docs/en/db2/11.5.0"

LINKS_SQLITE = {
    kw: SQLITE_URL + page
    for kw, page in {
        "SELECT": "lang_select.html", "FROM": "lang_select.html",
        "WHERE": "lang_expr.html", "JOIN": "lang_select.html",
        "ON": "lang_select.html", "USING": "lang_select.html",
        "GROUP BY": "lang_select.html", "ORDER BY": "lang_select.html",
        "LIMIT": "lang_select.html", "OFFSET": "lang_select.html",
        "WITH": "lang_with.html", "AS": "lang_select.html",
        "DISTINCT": "lang_select.html", "CREATE": "lang_createtable.html",
        "TABLE": "lang_createtable.html", "VIEW": "lang_createview.html",
        "INDEX": "lang_createindex.html", "TRIGGER": "lang_createtrigger.html",
        "INSERT": "lang_insert.html", "INTO": "lang_insert.html",
        "UPDATE": "lang_update.html", "DELETE": "lang_delete.html",
        "ALTER": "lang_altertable.html", "DROP": "lang_droptable.html",
        "VIRTUAL": "lang_createvtab.html", "PRAGMA": "pragma.html",
        "CAST": "lang_expr.html", "CASE": "lang_expr.html",
        "WHEN": "lang_expr.html", "THEN": "lang_expr.html",
        "ELSE": "lang_expr.html", "END": "lang_expr.html",
        "LIKE": "lang_expr.html", "IN": "lang_expr.html",
        "BETWEEN": "lang_expr.html", "IS": "lang_expr.html",
        "BEGIN": "lang_transaction.html", "COMMIT": "lang_transaction.html",
        "ROLLBACK": "lang_transaction.html", "SAVEPOINT": "lang_savepoint.html",
        "VACUUM": "lang_vacuum.html", "ANALYZE": "lang_analyze.html",
        "REINDEX": "lang_reindex.html", "ATTACH": "lang_attach.html",
        "AUTOINCREMENT": "lang_createtable.html", "PRIMARY": "lang_createtable.html",
        "FOREIGN": "foreignkeys.html", "REFERENCES": "foreignkeys.html",
        "CONSTRAINT": "lang_createtable.html", "DEFAULT": "lang_createtable.html",
        "CHECK": "lang_createtable.html", "UNIQUE": "lang_createtable.html",
        "COLLATE": "lang_createtable.html",
    }.items()
}

LINKS_ORACLE = {
    kw: ORACLE_URL + path
    for kw, path in {
        "SELECT": "sqlrf/SELECT.html", "INSERT": "sqlrf/INSERT.html",
        "UPDATE": "sqlrf/UPDATE.html", "DELETE": "sqlrf/DELETE.html",
        "MERGE": "sqlrf/MERGE.html", "COMMIT": "sqlrf/COMMIT.html",
        "ROLLBACK": "sqlrf/ROLLBACK.html", "SAVEPOINT": "sqlrf/SAVEPOINT.html",
        "GRANT": "sqlrf/GRANT.html", "REVOKE": "sqlrf/REVOKE.html",
        "EXPLAIN": "sqlrf/EXPLAIN-PLAN.html", "ANALYZE": "sqlrf/ANALYZE.html",
        "CREATE": "sqlrf/CREATE-TABLE.html", "TABLE": "sqlrf/CREATE-TABLE.html",
        "ALTER": "sqlrf/ALTER-TABLE.html", "DROP": "sqlrf/DROP-TABLE.html",
        "VIEW": "sqlrf/CREATE-VIEW.html", "INDEX": "sqlrf/CREATE-INDEX.html",
        "DATABASE": "sqlrf/CREATE-DATABASE.html",
        "PROCEDURE": "lnpls/CREATE-PROCEDURE-statement.html",
        "TRIGGER": "lnpls/CREATE-TRIGGER-statement.html",
        "WHILE": "lnpls/WHILE-LOOP-statement.html",
        "FOR": "lnpls/FOR-LOOP-statement.html",
        "CASE": "lnpls/CASE-statement.html", "WHEN": "lnpls/CASE-statement.html",
        "THEN": "lnpls/CASE-statement.html", "ELSE": "lnpls/CASE-statement.html",
        "END": "lnpls/CASE-statement.html",
    }.items()
}

LINKS_SNOWFLAKE = {
    kw: SNOWFLAKE_URL + page
    for kw, page in {
        "SELECT": "sql/select", "INSERT": "sql/insert",
        "UPDATE": "sql/update", "DELETE": "sql/delete",
        "MERGE": "sql/merge", "CREATE": "sql/create-table",
        "TABLE": "sql/create-table",
        "ALTER": "sql/alter-table",
        "DROP": "sql/drop-table",
        "VIEW": "sql/create-view",
        "GRANT": "sql/grant-role", "REVOKE": "sql/revoke-role",
        "EXPLAIN": "sql/explain", "SHOW": "sql/show",
        "USE": "sql/use",
        "DESCRIBE": "sql/desc-table",
        "COPY": "sql/copy-into-table",
        "TASK": "sql/create-task",
        "STAGE": "sql/create-stage",
        "WAREHOUSE": "sql/create-warehouse",
        "QUALIFY": "constructs/qualify",
        "LIMIT": "sql/select",
    }.items()
}

LINKS_BIGQUERY = {
    kw: BQ_URL + page
    for kw, page in {
        "SELECT": "query-syntax.html", "FROM": "query-syntax.html",
        "WHERE": "query-syntax.html", "GROUP BY": "query-syntax.html",
        "HAVING": "query-syntax.html", "ORDER BY": "query-syntax.html",
        "LIMIT": "query-syntax.html", "OFFSET": "query-syntax.html",
        "JOIN": "query-syntax.html", "ON": "query-syntax.html",
        "USING": "query-syntax.html", "AS": "query-syntax.html",
        "WITH": "query-syntax.html", "INSERT": "dml-syntax.html",
        "DELETE": "dml-syntax.html", "UPDATE": "dml-syntax.html",
        "MERGE": "dml-syntax.html", "CREATE": "data-definition-language.html",
        "TABLE": "data-definition-language.html",
        "VIEW": "data-definition-language.html",
        "ALTER": "data-definition-language.html",
        "DROP": "data-definition-language.html",
        "CAST": "conversion_functions",
        "CASE": "conditional_expressions.html",
        "WHEN": "conditional_expressions.html",
        "THEN": "conditional_expressions.html",
        "ELSE": "conditional_expressions.html",
        "END": "conditional_expressions.html",
        "DECLARE": "scripting.html", "SET": "scripting.html",
        "IF": "scripting.html",
    }.items()
}

LINKS_TRINO = {
    kw: TRINO_URL + page
    for kw, page in {
        "SELECT": "select.html", "FROM": "select.html",
        "WHERE": "select.html", "GROUP BY": "select.html",
        "HAVING": "select.html", "ORDER BY": "select.html",
        "LIMIT": "select.html", "OFFSET": "select.html",
        "FETCH": "select.html", "JOIN": "select.html",
        "ON": "select.html", "USING": "select.html",
        "INSERT": "insert.html", "INTO": "insert.html",
        "UPDATE": "update.html", "DELETE": "delete.html",
        "MERGE": "merge.html", "CREATE": "create-table.html",
        "TABLE": "create-table.html", "VIEW": "create-view.html",
        "ALTER": "alter-table.html", "DROP": "drop-table.html",
        "GRANT": "grant.html", "REVOKE": "revoke.html",
        "EXPLAIN": "explain.html", "ANALYZE": "analyze.html",
        "PREPARE": "prepare.html", "EXECUTE": "execute.html",
        "SHOW": "show-tables.html", "DESCRIBE": "describe.html",
        "VALUES": "values.html",
    }.items()
}

LINKS_FLINK = {
    kw: FLINK_URL + page
    for kw, page in {
        "SELECT": "queries/", "INSERT": "insert/",
        "INTO": "insert/", "CREATE": "create/",
        "TABLE": "create/", "ALTER": "alter/",
        "DROP": "drop/",
        "WHERE": "queries/", "GROUP BY": "queries/",
        "ORDER BY": "queries/", "LIMIT": "queries/",
        "HAVING": "queries/", "JOIN": "queries/",
        "ON": "queries/", "AS": "queries/",
        "WITH": "queries/", "FROM": "queries/",
    }.items()
}

LINKS_HIVE = {
    kw: HIVE_URL + page
    for kw, page in {
        "SELECT": "LanguageManual+Select", "FROM": "LanguageManual+Select",
        "WHERE": "LanguageManual+Select", "JOIN": "LanguageManual+Select",
        "ON": "LanguageManual+Select", "GROUP BY": "LanguageManual+Select",
        "HAVING": "LanguageManual+Select", "ORDER BY": "LanguageManual+Select",
        "SORT BY": "LanguageManual+Select", "LIMIT": "LanguageManual+Select",
        "RLIKE": "LanguageManual+Select", "REGEXP": "LanguageManual+Select",
        "INSERT": "LanguageManual+DML", "INTO": "LanguageManual+DML",
        "UPDATE": "LanguageManual+DML", "DELETE": "LanguageManual+DML",
        "LOAD": "LanguageManual+DML", "PARTITION": "LanguageManual+DDL",
        "PARTITIONS": "LanguageManual+DDL", "EXTERNAL": "LanguageManual+DDL",
        "OVERWRITE": "LanguageManual+DML",
        "CREATE": "LanguageManual+DDL", "TABLE": "LanguageManual+DDL",
        "ALTER": "LanguageManual+DDL", "DROP": "LanguageManual+DDL",
        "VIEW": "LanguageManual+DDL", "INDEX": "LanguageManual+DDL",
        "SHOW": "LanguageManual+DDL", "DESCRIBE": "LanguageManual+DDL",
        "STORED": "LanguageManual+DDL", "ORC": "LanguageManual+DDL",
        "PARQUET": "LanguageManual+DDL", "ROW": "LanguageManual+DDL",
        "FORMAT": "LanguageManual+DDL", "DELIMITED": "LanguageManual+DDL",
    }.items()
}

LINKS_SPARK = {
    kw: SPARK_URL + page
    for kw, page in {
        "SELECT": "sql-ref-syntax-qry-select.html",
        "FROM": "sql-ref-syntax-qry-select.html",
        "WHERE": "sql-ref-syntax-qry-select.html",
        "GROUP BY": "sql-ref-syntax-qry-select.html",
        "HAVING": "sql-ref-syntax-qry-select.html",
        "ORDER BY": "sql-ref-syntax-qry-select.html",
        "LIMIT": "sql-ref-syntax-qry-select.html",
        "OFFSET": "sql-ref-syntax-qry-select-offset.html",
        "JOIN": "sql-ref-syntax-qry-select-join.html",
        "ON": "sql-ref-syntax-qry-select-join.html",
        "INSERT": "sql-ref-syntax-dml-insert-table.html",
        "INTO": "sql-ref-syntax-dml-insert-table.html",
        "CREATE": "sql-ref-syntax-ddl-create-table.html",
        "TABLE": "sql-ref-syntax-ddl-create-table.html",
        "VIEW": "sql-ref-syntax-ddl-create-view.html",
        "ALTER": "sql-ref-syntax-ddl-alter-table.html",
        "DROP": "sql-ref-syntax-ddl-drop-table.html",
        "EXPLAIN": "sql-ref-syntax-qry-explain.html",
        "CACHE": "sql-ref-syntax-aux-cache-cache-table.html",
        "UNCACHE": "sql-ref-syntax-aux-cache-uncache-table.html",
        "REFRESH": "sql-ref-syntax-aux-cache-refresh-table.html",
        "SET": "sql-ref-syntax-aux-conf-mgmt-set.html",
        "USING": "sql-ref-syntax-ddl-create-table.html",
        "PARTITIONED": "sql-ref-syntax-ddl-create-table.html",
        "STORED": "sql-ref-syntax-ddl-create-table.html",
        "ANALYZE": "sql-ref-syntax-aux-analyze-table.html",
        "DESCRIBE": "sql-ref-syntax-aux-describe-table.html",
        "SHOW": "sql-ref-syntax-aux-show-tables.html",
        "TRUNCATE": "sql-ref-syntax-ddl-truncate-table.html",
    }.items()
}

LINKS_SINGLESTORE = {
    kw: {"singlestore": SINGLESTORE_URL + "sql-reference/"}
    for kw in (
        "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "TABLE", "ALTER",
        "DROP", "TRUNCATE", "GRANT", "REVOKE", "EXPLAIN", "SHOW", "USE",
        "RLIKE", "REGEXP", "SPLIT", "TABLETS", "INCLUDE",
        "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET",
        "JOIN", "ON", "AS", "WITH", "DEFINER", "PROCEDURE", "WHILE",
    )
}

LINKS_COUCHBASE = {
    kw: COUCHBASE_URL + page
    for kw, page in {
        "SELECT": "select.html", "FROM": "select.html",
        "WHERE": "select.html", "GROUP BY": "select.html",
        "HAVING": "select.html", "ORDER BY": "select.html",
        "LIMIT": "select.html", "OFFSET": "select.html",
        "INSERT": "insert.html", "INTO": "insert.html",
        "UPDATE": "update.html", "DELETE": "delete.html",
        "MERGE": "merge.html", "RETURNING": "update.html",
        "EXPLAIN": "explain.html",
        "USE": "use-index-clauses.html", "INDEX": "createindex.html",
        "KEY": "insert.html", "VALUE": "insert.html",
        "ANY": "anyandevery.html", "EVERY": "anyandevery.html",
        "SATISFIES": "anyandevery.html", "RAW": "select.html",
        "META": "functions/meta.html",
    }.items()
}

LINKS_REDSHIFT = {
    kw: {"redshift": REDSHIFT_URL + "c_SQL_commands.html"}
    for kw in (
        "SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "TABLE",
        "ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE", "ANALYZE", "VACUUM",
        "EXPLAIN", "UNLOAD", "COPY", "VIEW", "INDEX", "DISTKEY", "SORTKEY",
        "DISTSTYLE", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
        "OFFSET", "JOIN", "ON", "AS", "WITH",
    )
}

MARIADB_URL = "https://mariadb.com/kb/en/"

LINKS_MARIADB = {
    kw: MARIADB_URL + page
    for kw, page in {
        "SELECT": "select/", "FROM": "select/",
        "WHERE": "select/", "JOIN": "join/",
        "ON": "join/", "USING": "join/",
        "GROUP BY": "group-by/", "ORDER BY": "order-by/",
        "HAVING": "having/", "LIMIT": "limit/",
        "OFFSET": "limit/", "AS": "as/",
        "DISTINCT": "select/", "INSERT": "insert/",
        "INTO": "insert/", "UPDATE": "update/",
        "DELETE": "delete/", "CREATE": "create-table/",
        "TABLE": "create-table/", "ALTER": "alter-table/",
        "DROP": "drop-table/", "TRUNCATE": "truncate-table/",
        "VIEW": "create-view/", "INDEX": "create-index/",
        "DATABASE": "create-database/", "SHOW": "show/",
        "USE": "use/", "DESCRIBE": "describe/",
        "RLIKE": "rlike/", "REGEXP": "regexp/",
        "WHILE": "while/", "PROCEDURE": "create-procedure/",
        "DEFINER": "create-procedure/",
        "BEGIN": "begin-end/", "CASE": "case-operator/",
        "WHEN": "case-operator/", "THEN": "case-operator/",
        "ELSE": "case-operator/", "END": "case-operator/",
        "VALUES": "values/", "WITH": "with/",
        "ENGINE": "create-table/", "AUTO_INCREMENT": "auto_increment/",
        "DELIMITER": "delimiter/",
    }.items()
}

LINKS_DB2 = {
    kw: {"db2": DB2_URL + "?topic=statements-sql-select-statement" if kw == "SELECT" else DB2_URL}
    for kw in (
        "SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "TABLE",
        "ALTER", "DROP", "GRANT", "REVOKE", "EXPLAIN", "CALL", "PROCEDURE",
        "FUNCTION", "DECLARE", "CURSOR", "OPEN", "FETCH", "CLOSE",
        "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET",
        "JOIN", "ON", "AS", "WITH", "WHILE", "RETURNING", "TRUNCATE",
    )
}

# NOTE: LINKS_* tables are merged vendor-wise in main() so that keywords
# shared across dialects keep every curated vendor (e.g. SELECT keeps
# PostgreSQL + MySQL + T-SQL + SQLite + ... links). Tables may use either
# {kw: {vendor: url}} or the flat {kw: url} form; flat tables are tagged
# with the dialect's vendor below.
LINKS_BY_DIALECT = [
    ("sqlite", LINKS_SQLITE), ("oracle", LINKS_ORACLE),
    ("mariadb", LINKS_MARIADB),
    ("snowflake", LINKS_SNOWFLAKE), ("bigquery", LINKS_BIGQUERY),
    ("trino", LINKS_TRINO), ("flink", LINKS_FLINK),
    ("hive", LINKS_HIVE), ("spark", LINKS_SPARK),
    ("redshift", LINKS_REDSHIFT), ("singlestore", LINKS_SINGLESTORE),
    ("couchbase", LINKS_COUCHBASE), ("db2", LINKS_DB2),
]

FOOTER_RE = re.compile(r"\n\nDocs: .*$", re.S)


def extract_links_from_t1(text):
    """Split the curated 'Docs:' footer off T1 entries into a links dict."""
    m = FOOTER_RE.search(text)
    if not m:
        return text, {}
    footer = m.group(0)
    text = text[: m.start()]

    links = {}
    for label, url in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", footer):
        vendor = label.split(":")[0].strip().lower()
        vendor_map = {"postgresql": "postgres", "mysql": "mysql"}
        vendor = vendor_map.get(vendor, vendor)
        links[vendor] = url
    return text, links

CLASS_STATEMENT = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "CALL", "EXECUTE", "EXEC",
    "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME", "COMMENT", "ANALYZE",
    "EXPLAIN", "GRANT", "REVOKE", "USE", "SHOW", "DESCRIBE", "DESC", "SET",
    "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "START",
    "VACUUM", "CLUSTER", "REINDEX", "OPTIMIZE", "FLUSH", "REPAIR", "CHECKSUM",
    "LOCK", "UNLOCK", "KILL", "LOAD", "HANDLER", "DO", "HELP", "PURGE",
    "RESET", "STOP", "START", "BACKUP", "RESTORE", "REFRESH", "SPLIT",
    "REFRESH_MATERIALIZED", "MAINTAIN",
}
CLASS_CLAUSE = {
    "FROM", "WHERE", "INTO", "VALUES", "HAVING", "LIMIT", "OFFSET", "FETCH",
    "FOR", "USING", "RETURNING", "WITH", "RECURSIVE", "OVER", "WINDOW",
    "PARTITION", "SELECT", "GROUP", "ORDER", "BY", "TOP", "FIRST", "NEXT",
    "TIES", "ONLY", "AS", "DISTINCT", "DUPLICATE", "IGNORE", "WHEN", "THEN",
    "ELSE", "END", "CASE", "IF", "ON", "JOIN", "STRAIGHT_JOIN", "USE",
}
CLASS_OPERATOR = {
    "AND", "OR", "NOT", "XOR", "IN", "NOT_IN", "LIKE", "NOT_LIKE", "ILIKE",
    "RLIKE", "REGEXP", "NOT_REGEXP", "BETWEEN", "NOT_BETWEEN", "IS", "NULL",
    "EXISTS", "ANY", "ALL", "SOME", "UNION", "EXCEPT", "INTERSECT", "MINUS",
    "COLLATE", "BINARY", "DIV", "MOD", "ISNULL", "OPERATOR",
}
CLASS_TYPE = {
    "INT", "INTEGER", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT", "FLOAT",
    "DOUBLE", "REAL", "DECIMAL", "NUMERIC", "CHAR", "VARCHAR", "TEXT",
    "TINYTEXT", "MEDIUMTEXT", "LONGTEXT", "BLOB", "TINYBLOB", "MEDIUMBLOB",
    "LONGBLOB", "BINARY", "VARBINARY", "DATE", "DATETIME", "TIMESTAMP",
    "TIME", "YEAR", "BOOLEAN", "BOOL", "ENUM", "JSON", "BIT", "UUID",
    "SERIAL", "MONEY", "CLOB", "NCLOB", "NCHAR", "NVARCHAR", "INTERVAL",
    "ARRAY", "MAP", "STRUCT", "GEOMETRY", "POINT", "LINESTRING", "POLYGON",
    "MULTIPOINT", "MULTILINESTRING", "MULTIPOLYGON", "GEOMETRYCOLLECTION",
    "BYTEA", "XML", "CURSOR", "TABLE_TYPE", "SMALLDATETIME", "DATETIME2",
    "UNIQUEIDENTIFIER", "ROWVERSION", "SQL_VARIANT", "BOX", "CIDR", "INET",
    "MACADDR", "TSVECTOR", "TSQUERY",
}
CLASS_FUNCTION = {
    "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "CEIL", "CEILING", "FLOOR",
    "ROUND", "TRUNCATE", "MOD", "POW", "POWER", "SQRT", "EXP", "LN", "LOG",
    "PI", "RAND", "RANDOM", "COALESCE", "NULLIF", "IFNULL", "ISNULL", "IF",
    "CONCAT", "SUBSTRING", "SUBSTR", "LENGTH", "CHAR_LENGTH", "LOWER",
    "UPPER", "TRIM", "REPLACE", "LEFT", "RIGHT", "LOCATE", "POSITION",
    "INSTR", "FORMAT", "DATE_FORMAT", "DATEDIFF", "DATE_ADD", "DATE_SUB",
    "TIMESTAMPDIFF", "EXTRACT", "CAST", "CONVERT", "NOW", "CURDATE",
    "CURTIME", "UNIX_TIMESTAMP", "MD5", "SHA1", "SHA2", "UUID_SHORT",
    "HEX", "UNHEX", "ORD", "ASCII", "LPAD", "RPAD", "REVERSE", "SPACE",
    "REPEAT", "STRCMP", "FIND_IN_SET", "FIELD", "ELT", "EXPORT_SET",
    "GROUP_CONCAT", "STRING_AGG", "ARRAY_AGG", "BOOL_AND", "BOOL_OR",
    "EVERY", "STDDEV", "VARIANCE", "MEDIAN", "PERCENTILE_CONT",
    "PERCENTILE_DISC", "RANK", "DENSE_RANK", "ROW_NUMBER", "NTILE",
    "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE", "NTH_VALUE",
    "GENERATE_SERIES", "SESSION_USER", "SYSTEM_USER", "USER",
}
CLASS_LITERAL = {
    "NULL", "TRUE", "FALSE", "UNKNOWN", "CURRENT_DATE", "CURRENT_TIME",
    "CURRENT_TIMESTAMP", "CURRENT_USER", "SESSION_USER", "CURRENT_ROLE",
    "CURRENT_CATALOG", "CURRENT_SCHEMA", "LOCALTIME", "LOCALTIMESTAMP",
    "SQLCODE", "SQLSTATE", "SQLWARNING", "SQLEXCEPTION",
}
CLASS_MODIFIER = {
    "PRIMARY", "FOREIGN", "KEY", "REFERENCES", "CONSTRAINT", "DEFAULT",
    "CHECK", "UNIQUE", "NOT_NULL", "UNSIGNED", "SIGNED", "ZEROFILL",
    "AUTO_INCREMENT", "AUTOINCREMENT", "CASCADE", "RESTRICT", "NO_ACTION",
    "ACTION", "DEFERRABLE", "DEFERRED", "IMMEDIATE", "INITIALLY", "COLLATE",
    "CHARSET", "CHARACTER", "ENGINE", "COMMENT", "ENCRYPTED", "OWNER",
    "REPLICATION", "LEAKPROOF", "IMMUTABLE", "STABLE", "VOLATILE",
    "PARALLEL_SAFE", "UNLOGGED", "TEMPORARY", "TEMP", "GLOBAL", "LOCAL",
    "MATERIALIZED", "VIRTUAL", "STORED", "GENERATED", "IDENTITY", "ALWAYS",
    "SPARSE", "ROWGUIDCOL", "PERSISTED", "COMPUTED",
}

# Multiword phrases (hover text joined with spaces)
T1_MULTI = {k: v for k, v in T1.items() if " " not in k}
T1_SINGLE = {k: v for k, v in T1.items() if " " not in k}

# Grammar-vocabulary words absent from sqls' dialect tables (tree-sitter
# parser knows them; the sqls lexer does not). Merged into the keyword
# universe so hover + completions cover every word the extension parses.
EXTRA_KEYWORDS = {
    "AVRO": "**Storage format** (Hive/Spark) — Avro-backed table storage for `STORED AS AVRO`.",
    "BIGSERIAL": "**Data type** (PostgreSQL) — auto-incrementing 8-byte integer (`BIGINT` + sequence default).",
    "BIN_PACK": "**Storage parameter** (SingleStore) — columnar bin-packing layout option.",
    "BOX2D": "**Data type** (PostGIS) — 2D bounding box geometry.",
    "BOX3D": "**Data type** (PostGIS) — 3D bounding box geometry.",
    "BRIN": "**Index method** (PostgreSQL) — Block Range Index; compact index for large append-only tables.",
    "CACHED": "**Table option** (Impala) — table data cached in memory.",
    "DATETIME2": "**Data type** (T-SQL) — higher-precision `DATETIME` variant.",
    "DATETIMEOFFSET": "**Data type** (T-SQL) — `DATETIME2` plus UTC time-zone offset.",
    "FOLLOWS": "**Trigger clause** (MariaDB) — fires the trigger after the named one.",
    "FORCE_NOT_NULL": "**COPY option** (PostgreSQL) — CSV: never read listed columns as NULL.",
    "FORCE_NULL": "**COPY option** (PostgreSQL) — CSV: always read listed columns as NULL when empty/quoted.",
    "FORCE_QUOTE": "**COPY option** (PostgreSQL) — CSV: quote all non-NULL values in listed columns.",
    "FORMATTED": "**DESCRIBE modifier** (Hive) — extended, formatted output for `DESCRIBE FORMATTED`.",
    "GEOGRAPHY": "**Data type** — WGS84 spheroidal spatial data (PostGIS, Redshift, BigQuery).",
    "GEOMETRY": "**Data type** — planar spatial data (PostGIS, MySQL, Redshift).",
    "GIN": "**Index method** (PostgreSQL) — inverted index for composite values (arrays, JSONB, full text).",
    "GIST": "**Index method** (PostgreSQL) — Generalized Search Tree; basis for spatial/exclusion indexes.",
    "HASH": "**Index/join method** — hash-based index or join algorithm option.",
    "IMAGE": "**Data type** (T-SQL, deprecated) — binary large object; use `VARBINARY(MAX)`.",
    "INCREMENTAL": "**Statistics/refresh mode** — process only changed data.",
    "INET": "**Data type** (PostgreSQL) — IPv4/IPv6 host address.",
    "INPATH": "**LOAD clause** (Hive) — source path for `LOAD DATA INPATH`.",
    "JSONB": "**Data type** (PostgreSQL) — binary JSON with indexing support.",
    "JSONFILE": "**Storage format** (Impala) — JSON document files.",
    "MAIN": "**Table option** (Impala/HBase) — main storage designation.",
    "MEDIUMINT": "**Data type** (MySQL family) — 3-byte integer.",
    "METADATA": "**Clause** — metadata-only operations (e.g. `ALTER TABLE … ALTER COLUMN … SET DATA TYPE` variants, Snowflake `SHOW` scopes).",
    "MONEY": "**Data type** — currency amount with fixed scale (PostgreSQL, T-SQL).",
    "NOSCAN": "**Table option** (Hive) — skip scanning the table during `ANALYZE`.",
    "OBJECT_ID": "**Function** (T-SQL) — returns the database object ID for a schema-scoped name.",
    "OID": "**Data type** (PostgreSQL) — object identifier, an internal system type.",
    "PERMISSIVE": "**RLS policy clause** (PostgreSQL) — policy grants access by default; filters or adds rows.",
    "PLAIN": "**TOAST storage strategy** (PostgreSQL) — inline uncompressed storage.",
    "RCFILE": "**Storage format** (Hive) — Record Columnar File.",
    "REGNAMESPACE": "**Data type** (PostgreSQL) — cast of a schema name to its OID.",
    "REGPROC": "**Data type** (PostgreSQL) — cast of a function name to its OID.",
    "REGTYPE": "**Data type** (PostgreSQL) — cast of a type name to its OID.",
    "RESTRICTED": "**RLS policy clause** (PostgreSQL) — policy restricts access by default.",
    "RESTRICTIVE": "**RLS policy clause** (PostgreSQL) — all restrictive policies must pass for a row.",
    "REWRITE": "**Clause** (PostgreSQL) — `REFRESH MATERIALIZED VIEW … WITH/WITHOUT DATA` controls whether materialized data is rewritten.",
    "SAFE": "**Function modifier** (BigQuery) — `SAFE.` prefix returns NULL instead of erroring.",
    "SEQUENCEFILE": "**Storage format** (Hive) — compressed sequence file storage.",
    "SERIAL2": "**Data type** (PostgreSQL) — auto-incrementing 2-byte integer (`SMALLSERIAL`).",
    "SERIAL4": "**Data type** (PostgreSQL) — auto-incrementing 4-byte integer (`SERIAL`).",
    "SERIAL8": "**Data type** (PostgreSQL) — auto-incrementing 8-byte integer (`BIGSERIAL`).",
    "SMALLDATETIME": "**Data type** (T-SQL) — `DATETIME` with minute precision.",
    "SMALLMONEY": "**Data type** (T-SQL) — currency amount, 4 bytes.",
    "SMALLSERIAL": "**Data type** (PostgreSQL) — auto-incrementing 2-byte integer.",
    "SORT": "**Clause** (Impala/Hive) — `SORT BY` ordering within partitions.",
    "SPGIST": "**Index method** (PostgreSQL) — Space-partitioned GiST for non-balanced data (points, text).",
    "STATS": "**Clause** (Impala) — `COMPUTE STATS` table statistics.",
    "TBLPROPERTIES": "**Table option** (Hive/Spark) — arbitrary key-value table properties.",
    "TEXTFILE": "**Storage format** (Hive) — default delimited text storage.",
    "TIMESTAMPTZ": "**Data type** (PostgreSQL) — timestamp stored in UTC, rendered per zone.",
    "TINYINT": "**Data type** — 1-byte integer (MySQL family, Hive).",
    "UNCACHED": "**Table option** (Impala) — table data not cached in memory.",
    "UNSAFE": "**Function attribute** (PostgreSQL) — marks a support function as unsafe for parallelism.",
    "VOLATILE": "**Function attribute** (PostgreSQL) — value can change within a scan; no optimization.",
    "COMPOUND": "**Sort key modifier** (Redshift) — `COMPOUND SORTKEY`: keys applied in order, prefix queries still prune.",
    "ENCODE": "**Column option** (Redshift) — column compression encoding (`ENCODE AUTO` or `ENCODE ZSTD`).",
    "EVEN": "**Dist style** (Redshift) — `DISTSTYLE EVEN`: rows round-robin across nodes.",
    "GO": "**Batch separator** (T-SQL) — signals the end of a batch to `sqlcmd`/SSMS; not part of the SQL language itself.",
    "INTERLEAVED": "**Sort key modifier** (Redshift) — `INTERLEAVED SORTKEY`: keys weighted equally, good for equality filters on any column.",
}

TEMPLATES = {
    "statement": "**SQL statement keyword.** Starts or governs a statement.",
    "clause": "**SQL clause keyword.** Structures queries (filtering, grouping, sorting, targeting).",
    "operator": "**SQL operator keyword.** Combines or compares expressions.",
    "type": "**Data type keyword.** Declares a column type or cast target.",
    "function": "**Built-in SQL function.** Computes a value from its arguments.",
    "literal": "**SQL literal keyword.** Denotes a fixed value or context constant.",
    "modifier": "**DDL modifier keyword.** Adjusts columns, constraints or object behavior.",
    "matched": "**Reserved SQL keyword.** Part of the SQL grammar.",
    "keyword": "**SQL keyword.** Recognized by this dialect's grammar.",
    "ddl": "**DDL keyword.** Used in schema (data definition) statements.",
    "dml": "**DML keyword.** Used in data manipulation statements.",
}


def classify(kw, kind):
    """Return a one-line doc for keywords without curated content."""
    if kw in CLASS_TYPE:
        return TEMPLATES["type"]
    if kw in CLASS_FUNCTION:
        return TEMPLATES["function"]
    if kw in CLASS_OPERATOR:
        return TEMPLATES["operator"]
    if kw in CLASS_LITERAL:
        return TEMPLATES["literal"]
    if kw in CLASS_MODIFIER:
        return TEMPLATES["modifier"]
    if kw in CLASS_STATEMENT:
        return TEMPLATES["statement"]
    if kw in CLASS_CLAUSE:
        return TEMPLATES["clause"]
    if kind == "FUNCTION":
        return TEMPLATES["function"]
    if kind == "DDL":
        return TEMPLATES["ddl"]
    if kind == "DML":
        return TEMPLATES["dml"]
    return TEMPLATES["matched"]


def go_str(s):
    """Emit a Go interpreted string literal (safe for docs with backticks)."""
    out = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{out}"'


def main():
    if len(sys.argv) != 2:
        print("usage: gen-keyword-docs.py <path-to-sqls-source>", file=sys.stderr)
        sys.exit(1)

    src_root = Path(sys.argv[1])
    keyword_go = (src_root / "dialect" / "keyword.go").read_text()

    # sqls' authoritative keyword universe = the core keyword table
    # ("KW": Kind, map entries) PLUS every dialect-specific table in
    # dialect/*.go (list-style `var x = []string{...}` — dialect-only
    # words like RLIKE live there, not in the core map).
    pairs = re.findall(r'"([A-Z_0-9]+)":\s+(\w+),', keyword_go)
    keywords = {kw: kind for kw, kind in pairs}
    for extra_kw, extra_doc in EXTRA_KEYWORDS.items():
        if extra_kw not in keywords:
            keywords[extra_kw] = "KEYWORD"
    if not keywords:
        print("error: no keywords parsed from dialect/keyword.go", file=sys.stderr)
        sys.exit(1)

    for f in sorted((src_root / "dialect").glob("*.go")):
        src = f.read_text()
        for name, body in re.findall(r"var (\w+) = \[\]string\{(.*?)\n\}", src, re.S):
            low = name.lower()
            if "function" in low:
                kind = "FUNCTION"
            elif "keyword" in low:
                kind = "KEYWORD"
            else:
                continue
            for kw in re.findall(r'"([A-Z_0-9]+)"', body):
                cur = keywords.get(kw)
                if cur is None:
                    keywords[kw] = kind
                elif cur == "FUNCTION" and kind == "KEYWORD":
                    # Same word in both tables: keyword classification wins
                    # (e.g. RLIKE lives in MySQL keyword AND function lists).
                    keywords[kw] = "KEYWORD"

    docs = {}
    links = {}

    # T1 wins, then T2, then generated. T1 'Docs:' footers are split off
    # into per-vendor links so hover can filter them by dialect.
    for kw, kind in sorted(keywords.items()):
        if kw in T1_SINGLE:
            text, kw_links = extract_links_from_t1(T1_SINGLE[kw])
            docs[kw] = text
            if kw_links:
                links[kw] = kw_links
        elif kw in T2:
            docs[kw] = T2[kw]
        elif kw in EXTRA_KEYWORDS:
            docs[kw] = EXTRA_KEYWORDS[kw]
        else:
            docs[kw] = classify(kw, kind)

    # Manual link additions (MySQL / T-SQL canonical pages).
    for kw, vendors in LINKS_EXTRA.items():
        existing = links.setdefault(kw, {})
        existing.update(vendors)

    # Per-dialect vendor tables: vendor-wise merge, never clobber.
    for vendor, table in LINKS_BY_DIALECT:
        for kw, val in table.items():
            entry = val if isinstance(val, dict) else {vendor: val}
            existing = links.setdefault(kw, {})
            for v, url in entry.items():
                existing.setdefault(v, url)

    rich = sum(1 for kw in docs if kw in T1_SINGLE)
    oneline = sum(1 for kw in docs if kw not in T1_SINGLE and kw in T2)
    auto = len(docs) - rich - oneline

    # Multiword phrase docs (hover matches the whole phrase first)
    multi = {k: v for k, v in T1.items() if " " in k}
    for kw, text in multi.items():
        docs[kw], kw_links = extract_links_from_t1(text)
        if kw_links:
            links[kw] = kw_links
    rich += len(multi)

    lines = [
        "// Code generated by scripts/gen-keyword-docs.py. DO NOT EDIT.",
        "// Sources: curated dataset in this repository + sqls dialect/keyword.go.",
        "package handler",
        "",
        "// keywordDocs maps uppercase SQL keywords (single words and common",
        "// multiword phrases) to Markdown hover documentation.",
        "var keywordDocs = map[string]string{",
    ]
    for kw in sorted(docs):
        lines.append(f"\t{go_str(kw)}: {go_str(docs[kw])},")
    lines.append("}")
    lines.append("")

    lines += [
        "// keywordLinks maps keywords to per-vendor documentation URLs.",
        "// The hover footer shows only the links matching the document's",
        "// dialect (languageId); generic/unknown dialects show all.",
        "// NOTE: the generated file must stay in sync with keyword_hover.go",
        "// patches; hover parses these maps. Data values only, no logic.",
        "var keywordLinks = map[string]map[string]string{",
    ]
    for kw in sorted(links):
        lines.append(f"\t{go_str(kw)}: {{")
        for vendor in sorted(links[kw]):
            lines.append(
                f"\t\t{go_str(vendor)}: {go_str(links[kw][vendor])},"
            )
        lines.append("\t},")
    lines.append("}")
    lines.append("")

    # Words recognized by dialect-specific list-style tables (e.g. RLIKE
    # in dialect/mysql.go function AND keyword lists). Used by the hover
    # patch to treat dialect-specific keyword identifiers as keywords —
    # but only when no database is connected, so real columns keep DB
    # hover.
    dialect_kw = sorted(
        kw for kw, kind in keywords.items() if kind in ("KEYWORD", "FUNCTION")
    )
    lines += [
        "// dialectKeywords: words from dialect-specific keyword lists",
        "// (not the core table). Generated by scripts/gen-keyword-docs.py.",
        "var dialectKeywords = map[string]bool{",
    ]
    for kw in dialect_kw:
        lines.append(f"\t{go_str(kw)}: true,")
    lines.append("}")
    lines.append("")

    # coreKeywords: the core keyword table only. Used by the completion
    # handler as the fallback keyword list for documents whose dialect has
    # no sqls driver (generic/cloud dialects) — instead of the sqlite list
    # DataBaseKeywords() defaults to.
    core_kw = sorted({kw for kw, _ in pairs})
    lines += [
        "// coreKeywords: sqls' core keyword table (dialect/keyword.go).",
        "// Generated by scripts/gen-keyword-docs.py.",
        "var coreKeywords = []string{",
    ]
    for kw in core_kw:
        lines.append(f"\t{go_str(kw)},")
    lines.append("}")
    lines.append("")

    out = "\n".join(lines)
    sys.stdout.write(out)

    print(
        f"generated {len(docs)} entries "
        f"({rich} rich, {oneline} one-line, {auto} auto-classified, "
        f"{len(multi)} multiword, {len(links)} with links)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
