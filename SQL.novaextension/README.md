# SQL Language Extension for Nova

Provides advanced SQL support for Nova — syntax highlighting, code folding,
document outline, completions and a bundled language server
(keyword hover, schema intelligence) for 16 SQL dialects, powered by
[Tree-sitter SQL](https://github.com/DerekStride/tree-sitter-sql).

## Tree-sitter Parser

This extension uses the [Tree-sitter SQL parser](https://github.com/DerekStride/tree-sitter-sql)
by [Derek Stride](https://github.com/DerekStride) for precise and performant
syntax highlighting, code folding and the document outline shown in Nova's
sidebar.

## Supported SQL Dialects

- Generic SQL
- MySQL
- MariaDB
- PostgreSQL
- SQLite
- T-SQL
- PL/SQL
- SQL PL (DB2)
- N1QL
- Trino
- Redshift
- SingleStore
- Snowflake
- SparkSQL
- BigQuery
- HiveQL
- FlinkSQL

## Recognized File Extensions

The extension automatically recognizes files with these extensions:

```text
.sql, .ddl, .tsql, .psql, .pgsql, .mysql, .hqsql, .hql, .q,
.pls, .bdy, .fnc, .pck, .pkb, .pks, .plb, .plsql, .prc, .spc, .tpb, .tps, .trg, .vw,
.db2, .db2i, .cql, .inc, .tab, .udf, .viw,
.sqlite, .sqlite3, .bq, .bigquery,
.sf.sql, .rs.sql, .trino.sql, .singlestore.sql,
.spark.sql, .flink.sql, .flinksql, .n1ql, .mariadb.sql
```

This ensures seamless integration with your existing SQL files without additional
configuration.

> **Note:** compound extensions (`.sf.sql` and friends) are matched against
> everything after the _first_ dot in the filename. Keep the part before the
> extension dot-free — `report.sf.sql` detects as Snowflake, while
> `my.report.sf.sql` falls back to generic SQL. Use hyphens instead of dots
> for prefixed names (`my-report.sf.sql`).

Ambiguous files can also declare their dialect in the first line with a
hint comment: `-- @mariadb` (or `-- syntax:mariadb`). A plain `.sql` file
with such a hint detects as MariaDB. The same works for every supported
dialect except generic SQL — available hints:

```text
@mysql, @mariadb, @postgresql, @tsql, @plsql, @sqlite, @bigquery,
@flinksql, @hiveql, @n1ql, @redshift, @singlestore, @snowflake,
@sparksql, @sqlpl
```

## Language Server

The extension bundles the [sqls](https://github.com/sqls-server/sqls)
language server (a universal, Developer ID–signed binary — no runtime
dependencies). When enabled (default), it provides:

- **Keyword hover documentation** — hovering `SELECT`, `WHERE`, `RLIKE`,
  … explains the keyword: ~1600 keywords covered. Reference links in the
  footer match the open file's dialect — PostgreSQL docs in PostgreSQL
  files, MySQL docs in MySQL files, MariaDB Knowledge Base in MariaDB
  files, Microsoft Learn in T-SQL files, and so on for all supported
  dialects. Generic SQL documents show the description only, since no
  canonical standard-SQL reference exists
- **Hover documentation** for tables, columns and sub-queries when a
  database connection is configured
- **Schema-aware completions** — tables, columns and JOIN suggestions when
  a database connection is configured
- **Signature help** for function calls

Everything works without a database too, but hover on table/column names
becomes much richer with one. Configure connections in
`~/.config/sqls/config.yml`, e.g.:

```yaml
lowercaseKeywords: false
connections:
  - driver: "postgresql"
    dataSourceName: "host=127.0.0.1 port=5432 user=postgres dbname=mydb sslmode=disable"
```

Or set a custom binary path / disable the server entirely in
Extension Preferences. Commands: **Restart Language Server** and
**Language Server Info** (Extensions menu).

The bundled binary is a **modified sqls** (keyword hover feature, added
via `patches/sqls/` in the extension repository and rebuilt with
`scripts/build-sqls.sh`). sqls is MIT-licensed by its authors.
