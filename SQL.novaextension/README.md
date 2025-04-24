# SQL Language Extension for Nova

Provides advanced SQL syntax highlighting and editing support in Nova using
[Tree-sitter SQL](https://github.com/DerekStride/tree-sitter-sql).

## Tree-sitter Parser

This extension uses the [Tree-sitter SQL parser](https://github.com/DerekStride/tree-sitter-sql)
by [Derek Stride](https://github.com/DerekStride) for precise and performant syntax
highlighting and code folding.

## Supported SQL Dialects

- Generic SQL
- MySQL / MariaDB
- PostgreSQL
- SQLite
- T-SQL
- PL/SQL
- N1QL
- Trino
- Redshift
- SingleStore
- Snowflake
- SparkSQL

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
