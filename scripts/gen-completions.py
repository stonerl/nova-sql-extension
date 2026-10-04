#!/usr/bin/env python3
"""Generate dialect completion sets for SQL.novaextension/Completions/SQL.xml.

Sources:
  1. sqls' dialect/*.go keyword + function lists (authoritative for the
     driver-backed dialects: MySQL, PostgreSQL, T-SQL, SQLite, Oracle) —
     the same universe the keyword-hover patch documents.
  2. Hand-curated per-dialect lists below for the cloud/embedded dialects
     sqls has no driver for.

Existing curated entries are never dropped: generated content is merged
(union) into the current <set> blocks, so re-running after editing the XML
by hand is safe and idempotent.

Usage: python3 gen-completions.py <path-to-sqls-source> [path-to-SQL.xml]
"""

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Hand-curated per-dialect lists (dialects without an sqls driver, plus
# driver dialects where sqls has no function list).
# --------------------------------------------------------------------------

HAND = {
    "sql.keywords": [
        # reserved-ish words the grammar parses but the curated set lacked
        "GRANT", "REVOKE", "PRIVILEGES", "USAGE", "EXEC", "EXECUTE", "CALL",
        "DESCRIBE", "DESC", "LOCK", "UNLOCK", "KILL", "CHECKPOINT", "LOAD",
        "SHOW", "TEMP", "TEMPORARY", "MATERIALIZED", "RECURSIVE", "MATCH",
        "INVOKER", "SECURITY", "OWNERSHIP", "QUALIFY", "OPTIONS", "UNNEST",
        "WITHIN", "GROUPING", "DISTKEY", "SORTKEY", "DISTSTYLE", "ENCODE",
        "EVEN", "COMPOUND", "INTERLEAVED", "GO", "AUTOINCREMENT", "IDENTITY",
        "TRUNCATE", "VACUUM", "ANALYZE", "SAVEPOINT", "RELEASE",
    ],
    "sql.functions": [
        "COALESCE", "NULLIF", "NVL", "IIF", "IFNULL", "DECODE", "CONCAT_WS",
        "STRING_AGG", "GROUP_CONCAT", "LISTAGG", "ARRAY_AGG", "JSON_AGG",
        "ROW_NUMBER", "RANK", "DENSE_RANK", "NTILE", "LAG", "LEAD",
        "FIRST_VALUE", "LAST_VALUE", "TRUNC", "TO_CHAR", "TO_DATE",
        "TO_NUMBER", "TO_TIMESTAMP", "DATE_TRUNC", "DATEADD", "DATEDIFF",
        "DATE_PART", "LAST_DAY", "REGEXP_REPLACE", "REGEXP_SUBSTR",
        "REGEXP_LIKE", "SPLIT_PART", "LPAD", "RPAD", "INITCAP",
    ],
    "sql.datatypes": [
        "INTEGER", "SMALLINT", "BIGINT", "DECIMAL", "NUMERIC", "REAL",
        "DOUBLE PRECISION", "CHAR", "VARCHAR", "TEXT", "BOOLEAN", "DATE",
        "TIME", "TIMESTAMP", "INTERVAL", "BLOB", "CLOB", "UUID", "JSON",
        "JSONB", "BYTEA",
    ],
    "sql.mysql_keywords": [
        # MariaDB-specific extras served by the shared MySQL provider
        "RETURNING", "INTERSECT", "EXCEPT", "SEQUENCE", "VECTOR", "NOWAIT",
    ],
    "sql.mysql_datatypes": [
        "SERIAL", "JSON", "VECTOR", "SET", "BIT", "YEAR", "TIME",
        "TIMESTAMP", "DATETIME", "DATE", "GEOMETRY", "POINT", "LINESTRING",
        "POLYGON", "TINYBLOB", "MEDIUMBLOB", "LONGBLOB", "TINYTEXT",
        "MEDIUMTEXT", "LONGTEXT",
    ],
    "sql.pg_keywords": [
        "CONCURRENTLY", "OWNED", "NOCREATEDB", "NOCREATEROLE", "NOLOGIN",
        "NOREPLICATION", "NOSUPERUSER", "CREATEDB", "CREATEROLE", "LOGIN",
        "REPLICATION", "SUPERUSER", "UNLOGGED", "VALID", "CONFLICT",
        "RETURNING", "GROUPING", "CUBE", "ROLLUP", "ONLY", "VERBOSE",
        "OIDS", "FREEZE", "STDIN", "PROGRAM", "ORDINALITY",
    ],
    "sql.pg_datatypes": [
        "SERIAL", "BIGSERIAL", "SMALLSERIAL", "UUID", "JSONB", "JSON",
        "BYTEA", "INET", "CIDR", "MACADDR", "MONEY", "NAME", "OID",
        "REGCLASS", "REGNAMESPACE", "REGPROC", "REGTYPE", "TSVECTOR",
        "TSQUERY", "XML", "POINT", "LINE", "LSEG", "BOX", "PATH", "POLYGON",
        "CIRCLE", "VARBIT", "BIT VARYING", "CHARACTER VARYING", "TIME WITH TIME ZONE",
        "TIMESTAMP WITH TIME ZONE",
    ],
    "sql.pg_functions": [
        "ARRAY_AGG", "STRING_AGG", "JSON_AGG", "JSONB_AGG", "JSONB_BUILD_OBJECT",
        "JSONB_BUILD_ARRAY", "JSONB_SET", "JSON_EXTRACT_PATH", "JSONB_EXTRACT_PATH",
        "GENERATE_SERIES", "UNNEST", "ARRAY_TO_STRING", "STRING_TO_ARRAY",
        "ARRAY_APPEND", "ARRAY_PREPEND", "ARRAY_LENGTH", "ARRAY_UPPER",
        "ARRAY_LOWER", "SPLIT_PART", "OVERLAY", "BTRIM", "AGE", "DATE_TRUNC",
        "DATE_PART", "TO_CHAR", "TO_DATE", "TO_NUMBER", "TO_TIMESTAMP",
        "CLOCK_TIMESTAMP", "REGEXP_MATCHES", "REGEXP_REPLACE",
        "REGEXP_SPLIT_TO_ARRAY", "MD5", "RANDOM", "SETSEED", "PG_SLEEP",
        "PG_BACKEND_PID", "TXID_CURRENT", "NEXTVAL", "CURRVAL", "SETVAL",
        "ROW_TO_JSON", "JSON_BUILD_OBJECT", "ARRAY_POSITION",
    ],
    "sql.tsql_keywords": [
        "IDENTITY", "IDENTITY_INSERT", "NOCOUNT", "QUOTED_IDENTIFIER",
        "ANSI_NULLS", "XACT_ABORT", "ARITHABORT", "TRANCOUNT", "CROSS APPLY",
        "OUTER APPLY", "PIVOT", "UNPIVOT", "OUTPUT", "THROW", "RAISERROR",
        "TRY", "CATCH", "MAXDOP", "TABLOCK", "ROWLOCK", "NOLOCK",
        "HOLDLOCK", "READCOMMITTED", "REPEATABLEREAD", "SERIALIZABLE",
        "SCHEMABINDING", "RETURNS NULL ON NULL INPUT", "CALLED",
        "OBJECT_ID", "OBJECT_NAME", "DB_NAME", "PROC",
    ],
    "sql.tsql_datatypes": [
        "NVARCHAR", "NCHAR", "NTEXT", "TEXT", "IMAGE", "UNIQUEIDENTIFIER",
        "ROWVERSION", "SQL_VARIANT", "HIERARCHYID", "GEOGRAPHY", "GEOMETRY",
        "DATETIME2", "DATETIMEOFFSET", "SMALLDATETIME", "SMALLMONEY",
        "MONEY", "VARBINARY", "BINARY", "XML",
    ],
    "sql.tsql_functions": [
        "ISNULL", "COALESCE", "NULLIF", "GETDATE", "GETUTCDATE",
        "SYSDATETIME", "DATEADD", "DATEDIFF", "DATEPART", "DATENAME",
        "CONVERT", "CAST", "TRY_CAST", "TRY_CONVERT", "LEN", "SUBSTRING",
        "REPLACE", "STUFF", "LTRIM", "RTRIM", "TRIM", "UPPER", "LOWER",
        "CHARINDEX", "PATINDEX", "CONCAT", "CONCAT_WS", "FORMAT",
        "ROW_NUMBER", "RANK", "DENSE_RANK", "NTILE", "LAG", "LEAD",
        "FIRST_VALUE", "LAST_VALUE", "STRING_AGG", "STRING_SPLIT", "IIF",
        "CHOOSE", "NEWID", "NEWSEQUENTIALID", "HASHBYTES", "PARSENAME",
    ],
    "sql.oracle_keywords": [
        # PL/SQL + SQL*Plus vocabulary beyond sqls' oracle lists
        "ROWNUM", "ROWID", "DUAL", "CONNECT BY", "START WITH", "PRIOR",
        "LEVEL", "NOCYCLE", "BULK COLLECT", "FORALL", "NEXTVAL", "CURRVAL",
        "REF CURSOR", "NOCOMPRESS", "PARALLEL", "NOPARALLEL", "NOLOGGING",
        "LOGGING", "CASCADE", "INVALIDATE", "ONLINE", "SKIP LOCKED",
        "NOMINVALUE", "NOMAXVALUE", "NOCACHE", "CYCLE", "KEEP SEQUENCE",
    ],
    "sql.oracle_datatypes": [
        "NUMBER", "VARCHAR2", "NVARCHAR2", "CHAR", "NCHAR", "CLOB", "NCLOB",
        "BLOB", "BFILE", "RAW", "LONG RAW", "LONG", "DATE", "TIMESTAMP",
        "TIMESTAMP WITH TIME ZONE", "TIMESTAMP WITH LOCAL TIME ZONE",
        "INTERVAL YEAR TO MONTH", "INTERVAL DAY TO SECOND", "FLOAT",
        "BINARY_FLOAT", "BINARY_DOUBLE", "UROWID", "ROWID", "XMLTYPE",
        "JSON",
    ],
    "sql.oracle_functions": [
        "NVL", "NVL2", "DECODE", "COALESCE", "NULLIF", "TO_CHAR", "TO_DATE",
        "TO_NUMBER", "TO_TIMESTAMP", "ADD_MONTHS", "MONTHS_BETWEEN",
        "LAST_DAY", "NEXT_DAY", "TRUNC", "ROUND", "SYSDATE", "SYSTIMESTAMP",
        "EXTRACT", "SUBSTR", "INSTR", "LPAD", "RPAD", "LTRIM", "RTRIM",
        "TRIM", "REPLACE", "TRANSLATE", "UPPER", "LOWER", "INITCAP",
        "CONCAT", "LENGTH", "LISTAGG", "REGEXP_SUBSTR", "REGEXP_REPLACE",
        "REGEXP_INSTR", "REGEXP_LIKE", "ABS", "MOD", "POWER", "SQRT",
        "FLOOR", "CEIL", "GREATEST", "LEAST", "USERENV",
    ],
    "sql.db2_keywords": [
        "SET SCHEMA", "SET CURRENT SCHEMA", "SET CURRENT PATH", "DECLARE",
        "DECLARE GLOBAL TEMPORARY TABLE", "OPEN", "FETCH", "CLOSE",
        "SIGNAL", "RESIGNAL", "GET DIAGNOSTICS", "LEAVE", "ITERATE",
        "REPEAT", "ELSEIF", "RETURN", "SPECIFIC", "DYNAMIC RESULT SETS",
        "LANGUAGE SQL", "MODIFIES SQL DATA", "READS SQL DATA",
        "CONTAINS SQL", "NOT ATOMIC", "SAVEPOINT", "RELEASE SAVEPOINT",
        "LOCK TABLE", "IN EXCLUSIVE MODE", "IN SHARE MODE", "FOR UPDATE",
        "FOR READ ONLY", "OPTIMIZE FOR", "FETCH FIRST", "ROWS ONLY",
        "NEXT VALUE FOR", "PREVIOUS VALUE FOR", "WITH UR", "WITH CS",
        "WITH RS", "WITH RR",
    ],
    "sql.db2_datatypes": [
        "SMALLINT", "INTEGER", "BIGINT", "DECIMAL", "NUMERIC", "DECFLOAT",
        "REAL", "DOUBLE", "CHAR", "VARCHAR", "CLOB", "DBCLOB", "GRAPHIC",
        "VARGRAPHIC", "BINARY", "VARBINARY", "BLOB", "DATE", "TIME",
        "TIMESTAMP", "XML", "BOOLEAN", "ROWID",
    ],
    "sql.db2_functions": [
        "COALESCE", "VALUE", "NULLIF", "DECODE", "SUBSTR", "SUBSTRING",
        "CONCAT", "STRIP", "TRIM", "LTRIM", "RTRIM", "UPPER", "LOWER",
        "LENGTH", "LOCATE", "POSSTR", "REPLACE", "TRANSLATE", "ROUND",
        "TRUNCATE", "ABS", "MOD", "POWER", "SQRT", "RAND", "DAYS",
        "DAYOFWEEK", "DAYNAME", "MONTHNAME", "TIMESTAMPDIFF",
        "VARCHAR_FORMAT", "TIMESTAMP_FORMAT", "DIGITS", "HEX", "CHR",
        "SPACE", "REPEAT", "LPAD", "RPAD", "LISTAGG", "IDENTITY_VAL_LOCAL",
        "CURRENT DATE", "CURRENT TIME", "CURRENT TIMESTAMP",
        "CURRENT SCHEMA", "CURRENT USER",
    ],
    "sql.sqlite_keywords": [
        "AUTOINCREMENT", "PRAGMA", "VACUUM", "ATTACH DATABASE",
        "DETACH DATABASE", "SAVEPOINT", "RELEASE", "REINDEX", "GLOB",
        "ISNULL", "NOTNULL", "ESCAPE", "IF NOT EXISTS", "WITHOUT ROWID",
        "STRICT", "GENERATED ALWAYS", "RETURNING", "DO NOTHING",
        "DO UPDATE", "CONFLICT", "ABORT", "FAIL", "IGNORE",
    ],
    "sql.sqlite_datatypes": [
        "INTEGER", "TEXT", "BLOB", "REAL", "NUMERIC",
    ],
    "sql.sqlite_functions": [
        "DATE", "TIME", "DATETIME", "STRFTIME", "JULIANDAY", "UNIXEPOCH",
        "COALESCE", "IFNULL", "NULLIF", "IIF", "LENGTH", "SUBSTR",
        "REPLACE", "TRIM", "LTRIM", "RTRIM", "UPPER", "LOWER", "INSTR",
        "PRINTF", "HEX", "RANDOM", "ABS", "ROUND", "TYPEOF",
        "LAST_INSERT_ROWID", "CHANGES", "TOTAL_CHANGES", "JSON",
        "JSON_EXTRACT", "JSON_OBJECT", "JSON_ARRAY", "GROUP_CONCAT",
        "CHAR", "SIGN", "EXP", "LOG", "POWER", "MOD", "FLOOR", "CEIL",
        "CONCAT",
    ],
    "sql.hiveql_keywords": [
        "LATERAL VIEW", "LATERAL VIEW OUTER", "TRANSFORM", "MAPJOIN",
        "CLUSTER BY", "DISTRIBUTE BY", "SORT BY", "SERDE",
        "ROW FORMAT", "STORED AS", "PARTITIONED BY", "EXTERNAL",
        "OVERWRITE", "LOAD DATA", "INPATH", "TBLPROPERTIES", "LOCATION",
        "IF NOT EXISTS", "MSCK REPAIR TABLE", "ANALYZE TABLE",
        "COMPUTE STATISTICS", "SHOW PARTITIONS", "SHOW FUNCTIONS",
        "SHOW CREATE TABLE", "DESCRIBE FORMATTED", "DESCRIBE EXTENDED",
        "DROP TABLE IF EXISTS", "IS NOT NULL", "IS NULL", "RLIKE", "REGEXP",
    ],
    "sql.hiveql_datatypes": [
        "STRING", "TINYINT", "SMALLINT", "INT", "BIGINT", "FLOAT", "DOUBLE",
        "DECIMAL", "TIMESTAMP", "DATE", "INTERVAL", "BINARY", "BOOLEAN",
        "ARRAY", "MAP", "STRUCT", "UNIONTYPE", "CHAR", "VARCHAR",
    ],
    "sql.hiveql_functions": [
        "UNIX_TIMESTAMP", "FROM_UNIXTIME", "DATE_FORMAT", "TO_DATE",
        "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND", "WEEKOFYEAR",
        "DATEDIFF", "DATE_ADD", "DATE_SUB", "EXPLODE", "POSEXPLODE",
        "SIZE", "MAP_KEYS", "MAP_VALUES", "ARRAY_CONTAINS", "SORT_ARRAY",
        "NVL", "COALESCE", "IF", "NULLIF", "ASSERT_TRUE", "CONCAT_WS",
        "SPLIT", "SUBSTR", "INSTR", "LPAD", "RPAD", "REGEXP_EXTRACT",
        "REGEXP_REPLACE", "GET_JSON_OBJECT", "FROM_JSON", "TO_JSON",
        "COLLECT_LIST", "COLLECT_SET", "PERCENTILE_APPROX", "MD5", "SHA2",
        "HASH", "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
        "FIRST_VALUE", "LAST_VALUE",
    ],
    "sql.bigquery_keywords": [
        "OPTIONS", "UNNEST", "QUALIFY", "SAFE_CAST", "EXPORT DATA",
        "LOAD DATA", "PIVOT", "UNPIVOT", "ROLLUP", "CUBE", "GROUPING SETS",
        "PARTITION BY", "CLUSTER BY", "FOR SYSTEM_TIME AS OF", "ASSERT",
        "EXCEPT", "REPLACE", "SAFE_PREFIX", "SAFE_OFFSET", "SAFE_ORDINAL",
        "CREATE OR REPLACE TABLE", "CREATE OR REPLACE VIEW",
        "INSERT INTO", "NOT EXISTS", "IS NOT NULL", "ANY_VALUE",
    ],
    "sql.bigquery_datatypes": [
        "INT64", "FLOAT64", "NUMERIC", "BIGNUMERIC", "BOOL", "STRING",
        "BYTES", "DATE", "DATETIME", "TIME", "TIMESTAMP", "INTERVAL",
        "JSON", "GEOGRAPHY", "STRUCT", "ARRAY",
    ],
    "sql.bigquery_functions": [
        "ARRAY_AGG", "ARRAY_LENGTH", "ARRAY_TO_STRING", "GENERATE_ARRAY",
        "GENERATE_DATE_ARRAY", "GENERATE_UUID", "JSON_VALUE", "JSON_QUERY",
        "TO_JSON", "PARSE_JSON", "SAFE_CAST", "SAFE_DIVIDE", "COALESCE",
        "IF", "IFNULL", "NULLIF", "ERROR", "PARSE_DATE", "PARSE_DATETIME",
        "PARSE_TIMESTAMP", "FORMAT_DATE", "FORMAT_TIMESTAMP", "DATE_ADD",
        "DATE_SUB", "DATE_DIFF", "TIMESTAMP_ADD", "TIMESTAMP_DIFF",
        "EXTRACT", "CURRENT_DATE", "CURRENT_DATETIME", "CURRENT_TIMESTAMP",
        "STRING_AGG", "COUNTIF", "LOG", "EXP", "POW", "SQRT", "ABS", "MOD",
        "DIV", "ROUND", "FLOOR", "CEIL", "REGEXP_CONTAINS",
        "REGEXP_EXTRACT", "REGEXP_REPLACE", "SPLIT", "CONCAT", "SUBSTR",
        "TRIM", "UPPER", "LOWER", "LENGTH", "STARTS_WITH", "ENDS_WITH",
        "CONTAINS_SUBSTR", "NORMALIZE", "ST_GEOGPOINT", "ST_DISTANCE",
        "ST_AREA", "ST_DWITHIN",
    ],
    "sql.snowflake_keywords": [
        "USE WAREHOUSE", "USE ROLE", "USE DATABASE", "USE SCHEMA",
        "SHOW TABLES", "SHOW DATABASES", "SHOW SCHEMAS", "SHOW VIEWS",
        "SHOW WAREHOUSES", "SHOW GRANTS", "DESCRIBE TABLE", "DESCRIBE VIEW",
        "COPY INTO", "CREATE STREAM", "CREATE TASK", "CREATE PIPE",
        "CREATE STAGE", "CREATE FILE FORMAT", "CREATE SEQUENCE",
        "CREATE MASKING POLICY", "CREATE ROW ACCESS POLICY", "CLONE",
        "STAGE", "FILE FORMAT", "MASKING POLICY", "ROW ACCESS POLICY",
        "TAG", "WAREHOUSE", "STREAM", "TASK", "PIPE", "SHARE", "TRANSIENT",
        "ALTER SESSION", "PUT", "GET", "LIST", "REMOVE", "QUALIFY",
        "LATERAL FLATTEN", "CLUSTER BY", "SECURE VIEW", "GRANT", "REVOKE",
        "SAMPLE", "TABLESAMPLE", "GROUP BY ALL", "ORDER BY ALL",
        "EXCLUDE", "RENAME", "EXECUTE TASK", "ALTER PIPELINE", "IF NOT EXISTS",
    ],
    "sql.snowflake_datatypes": [
        "NUMBER", "DECIMAL", "NUMERIC", "INT", "INTEGER", "BIGINT",
        "SMALLINT", "TINYINT", "BYTEINT", "FLOAT", "FLOAT4", "FLOAT8",
        "DOUBLE", "REAL", "VARCHAR", "CHAR", "CHARACTER", "STRING", "TEXT",
        "BINARY", "VARBINARY", "BOOLEAN", "DATE", "DATETIME", "TIME",
        "TIMESTAMP", "TIMESTAMP_LTZ", "TIMESTAMP_NTZ", "TIMESTAMP_TZ",
        "VARIANT", "OBJECT", "ARRAY", "GEOGRAPHY", "GEOMETRY",
    ],
    "sql.snowflake_functions": [
        "FLATTEN", "OBJECT_CONSTRUCT", "ARRAY_CONSTRUCT", "ARRAY_AGG",
        "TO_VARIANT", "TO_OBJECT", "TO_ARRAY", "TO_JSON", "PARSE_JSON",
        "TRY_PARSE_JSON", "IFF", "NULLIF", "ZEROIFNULL", "NVL", "NVL2",
        "DECODE", "COALESCE", "DATE_TRUNC", "DATEADD", "DATEDIFF",
        "DATE_PART", "LAST_DAY", "NEXT_DAY", "ADD_MONTHS", "TRUNC",
        "TO_DATE", "TO_TIMESTAMP", "TO_CHAR", "TO_NUMBER", "LISTAGG",
        "SPLIT", "SPLIT_PART", "STRTOK", "REGEXP_SUBSTR", "REGEXP_REPLACE",
        "REGEXP_LIKE", "CONTAINS", "STARTSWITH", "ENDSWITH", "POSITION",
        "CHARINDEX", "LENGTH", "UPPER", "LOWER", "INITCAP", "HASH",
        "UUID_STRING", "CURRENT_USER", "CURRENT_ROLE", "CURRENT_WAREHOUSE",
        "CURRENT_DATABASE", "CURRENT_SCHEMA", "CURRENT_TIMESTAMP",
        "GENERATOR", "MEDIAN", "PERCENTILE_CONT", "STDDEV", "VARIANCE",
        "CORR", "BOOLOR_AGG", "BOOLAND_AGG", "ARRAY_SIZE", "OBJECT_KEYS",
    ],
    "sql.redshift_keywords": [
        "DISTKEY", "SORTKEY", "DISTSTYLE", "COMPOUND", "INTERLEAVED",
        "ENCODE", "COPY", "UNLOAD", "VACUUM", "ANALYZE", "EVEN", "QUALIFY",
        "CREATE EXTERNAL TABLE", "CREATE EXTERNAL SCHEMA", "IAM_ROLE",
        "DELIMITER", "REMOVEQUOTES", "FIXEDWIDTH", "GZIP", "BZIP2", "ZSTD",
        "ACCEPTANYDATE", "TRUNCATECOLUMNS", "COMPUPDATE", "STATUPDATE",
        "MANIFEST", "DESTROY", "PAUSE", "RESUME", "ABORT", "DEALLOCATE",
        "PREPARE", "EXECUTE", "REFRESH", "RESET",
    ],
    "sql.redshift_datatypes": [
        "SUPER", "VARCHAR", "CHARACTER VARYING", "CHAR", "INTEGER",
        "BIGINT", "SMALLINT", "DECIMAL", "REAL", "DOUBLE PRECISION",
        "BOOLEAN", "DATE", "TIMESTAMP", "TIMESTAMPTZ", "TIME", "TIMETZ",
        "GEOMETRY", "GEOGRAPHY", "VARBYTE",
    ],
    "sql.redshift_functions": [
        "LISTAGG", "MEDIAN", "PERCENTILE_CONT", "APPROXIMATE PERCENTILE_DISC",
        "DATEADD", "DATEDIFF", "DATE_TRUNC", "EXTRACT", "TO_CHAR",
        "TO_DATE", "TO_TIMESTAMP", "TO_NUMBER", "GETDATE", "SYSDATE",
        "NVL", "NVL2", "DECODE", "COALESCE", "NULLIF", "LAG", "LEAD",
        "FIRST_VALUE", "LAST_VALUE", "NTILE", "ROW_NUMBER", "RANK",
        "DENSE_RANK", "REGEXP_SUBSTR", "REGEXP_REPLACE", "REGEXP_INSTR",
        "REGEXP_COUNT", "SPLIT_PART", "POSITION", "STRPOS", "LEN", "LEFT",
        "RIGHT", "SUBSTRING", "TRIM", "CONCAT", "JSON_PARSE",
        "JSON_EXTRACT_PATH_TEXT", "LOG", "POWER", "SQRT", "RANDOM",
    ],
    "sql.trino_keywords": [
        "SHOW TABLES", "SHOW SCHEMAS", "SHOW CATALOGS", "SHOW COLUMNS",
        "SHOW FUNCTIONS", "USE", "EXPLAIN", "ANALYZE", "DESCRIBE",
        "TABLESAMPLE", "OFFSET", "FETCH FIRST", "QUALIFY", "GROUP BY ALL",
        "ORDER BY ALL", "CREATE TABLE AS", "COMMENT ON", "REFRESH",
        "RESET SESSION", "SET SESSION", "WITH RECURSIVE", "VALUES",
        "IF NOT EXISTS", "IS NOT NULL", "NOT EXISTS",
    ],
    "sql.trino_datatypes": [
        "BOOLEAN", "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "REAL",
        "DOUBLE", "DECIMAL", "VARCHAR", "CHAR", "VARBINARY", "JSON",
        "DATE", "TIME", "TIMESTAMP", "TIME WITH TIME ZONE",
        "TIMESTAMP WITH TIME ZONE", "INTERVAL DAY TO SECOND",
        "INTERVAL YEAR TO MONTH", "ARRAY", "MAP", "ROW", "IPADDRESS",
        "UUID", "HYPERLOGLOG", "P4HYPERLOGLOG", "QDIGEST", "TDIGEST",
        "GEOMETRY", "BINGTILE",
    ],
    "sql.trino_functions": [
        "ARRAY_AGG", "ARBITRARY", "ANY_VALUE", "APPROX_DISTINCT",
        "APPROX_PERCENTILE", "CARDINALITY", "CONTAINS", "ELEMENT_AT",
        "ARRAY_JOIN", "SPLIT", "SPLIT_TO_MAP", "SEQUENCE", "MAP_KEYS",
        "MAP_VALUES", "MAP_ENTRIES", "MAP_FROM_ENTRIES", "JSON_FORMAT",
        "JSON_PARSE", "JSON_EXTRACT", "TRY", "COALESCE", "IF", "NULLIF",
        "DATE_TRUNC", "DATE_ADD", "DATE_DIFF", "DATE_PARSE", "DATE_FORMAT",
        "FROM_UNIXTIME", "TO_UNIXTIME", "NOW", "CURRENT_DATE",
        "CURRENT_TIMESTAMP", "REGEXP_EXTRACT", "REGEXP_EXTRACT_ALL",
        "REGEXP_REPLACE", "REGEXP_LIKE", "ROUND", "ABS", "MOD", "LOG",
        "LN", "POWER", "SQRT", "MD5", "SHA256", "TO_HEX", "FROM_HEX",
        "UUID", "REVERSE", "STRPOS", "REPLACE", "CONCAT", "LENGTH", "CHR",
        "CODEPOINT", "TRIM", "LOWER", "UPPER", "FORMAT", "ROW_NUMBER",
        "RANK", "DENSE_RANK", "NTILE", "LAG", "LEAD", "FIRST_VALUE",
        "LAST_VALUE",
    ],
    "sql.sparksql_keywords": [
        "LATERAL VIEW", "LATERAL VIEW OUTER", "CLUSTER BY", "DISTRIBUTE BY",
        "SORT BY", "STORED AS", "USING", "OPTIONS", "TBLPROPERTIES",
        "PARTITIONED BY", "OVERWRITE", "INSERT OVERWRITE",
        "CREATE OR REPLACE TABLE", "CREATE OR REPLACE TEMPORARY VIEW",
        "GLOBAL TEMPORARY", "EXPLAIN", "CACHE TABLE", "CACHE LAZY TABLE",
        "UNCACHE TABLE", "CLEAR CACHE", "REFRESH TABLE", "SHOW TABLES",
        "SHOW PARTITIONS", "SHOW FUNCTIONS", "SHOW CREATE TABLE",
        "DESCRIBE TABLE", "ADD JAR", "ADD FILE", "FOR VERSION AS OF",
        "FOR TIMESTAMP AS OF", "IF NOT EXISTS", "IS NOT NULL",
    ],
    "sql.sparksql_datatypes": [
        "STRING", "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
        "FLOAT", "DOUBLE", "DECIMAL", "BOOLEAN", "DATE", "TIMESTAMP",
        "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "INTERVAL", "BINARY", "ARRAY",
        "MAP", "STRUCT", "VOID", "CHAR", "VARCHAR",
    ],
    "sql.sparksql_functions": [
        "EXPLODE", "POSEXPLODE", "SIZE", "ARRAY", "MAP", "STRUCT",
        "NAMED_STRUCT", "MAP_FROM_ARRAYS", "ARRAY_CONTAINS", "ARRAY_DISTINCT",
        "ARRAY_INTERSECT", "ARRAY_UNION", "ARRAY_EXCEPT", "ARRAY_SORT",
        "ARRAY_JOIN", "SLICE", "CONCAT", "CONCAT_WS", "SPLIT", "SUBSTRING",
        "REGEXP_EXTRACT", "REGEXP_REPLACE", "INSTR", "LOCATE", "POSITION",
        "LPAD", "RPAD", "TRIM", "LTRIM", "RTRIM", "UPPER", "LOWER",
        "INITCAP", "REVERSE", "REPEAT", "DATE_FORMAT", "TO_DATE",
        "TO_TIMESTAMP", "UNIX_TIMESTAMP", "FROM_UNIXTIME", "DATEDIFF",
        "DATE_ADD", "DATE_SUB", "ADD_MONTHS", "MONTHS_BETWEEN", "LAST_DAY",
        "NEXT_DAY", "TRUNC", "DATE_TRUNC", "CURRENT_DATE",
        "CURRENT_TIMESTAMP", "COALESCE", "NULLIF", "NVL", "NVL2", "IF",
        "IFNULL", "GET_JSON_OBJECT", "FROM_JSON", "TO_JSON",
        "SCHEMA_OF_JSON", "SHA2", "MD5", "CRC32", "HASH", "UUID",
        "MONOTONICALLY_INCREASING_ID", "SPARK_PARTITION_ID",
        "COLLECT_LIST", "COLLECT_SET", "FIRST", "LAST", "ROW_NUMBER",
        "RANK", "DENSE_RANK", "LAG", "LEAD", "PERCENTILE_APPROX",
    ],
    "sql.flinksql_keywords": [
        "WATERMARK", "FOR SYSTEM_TIME AS OF", "MATCH_RECOGNIZE", "PATTERN",
        "DEFINE", "MEASURES", "WITHIN", "EMIT", "EXECUTE STATEMENT SET",
        "EXECUTE INSERT INTO", "USE CATALOG", "USE", "SHOW DATABASES",
        "SHOW TABLES", "SHOW CATALOGS", "SHOW MODULES", "SHOW JARS",
        "SET", "RESET", "ADD JAR", "REMOVE JAR", "IF NOT EXISTS",
        "PARTITIONED BY", "PRIMARY KEY NOT ENFORCED", "COMMENT",
        "INSERT OVERWRITE", "IS NOT NULL", "NOT EXISTS",
    ],
    "sql.flinksql_datatypes": [
        "STRING", "BOOLEAN", "TINYINT", "SMALLINT", "INT", "BIGINT",
        "FLOAT", "DOUBLE", "DECIMAL", "DATE", "TIME", "TIMESTAMP",
        "TIMESTAMP_LTZ", "BYTES", "BINARY", "VARBINARY", "ARRAY", "MAP",
        "ROW", "MULTISET", "RAW", "CHAR", "VARCHAR",
    ],
    "sql.flinksql_functions": [
        "TUMBLE", "HOP", "CUMULATE", "LISTAGG", "JSON_VALUE", "JSON_STRING",
        "JSON_OBJECT", "JSON_ARRAY", "JSON_EXISTS", "COALESCE", "IF",
        "CONCAT", "CONCAT_WS", "SUBSTRING", "TRIM", "LTRIM", "RTRIM",
        "REPLACE", "REGEXP_EXTRACT", "REGEXP_REPLACE", "LOCATE",
        "POSITION", "CHAR_LENGTH", "CHARACTER_LENGTH", "UPPER", "LOWER",
        "INITCAP", "OVERLAY", "FROM_UNIXTIME", "UNIX_TIMESTAMP", "TO_DATE",
        "TO_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIMESTAMP",
        "CURRENT_WATERMARK", "LOCALTIMESTAMP", "PROCTIME", "ROW_NUMBER",
        "RANK", "DENSE_RANK", "LAG", "LEAD", "NTILE", "FIRST_VALUE",
        "LAST_VALUE", "STDDEV_POP", "STDDEV_SAMP", "VAR_POP", "VAR_SAMP",
        "COLLECT", "ARRAY_CONTAINS", "CARDINALITY", "ELEMENT",
    ],
    "sql.singlestore_keywords": [
        "SHARD KEY", "BTREE", "HASH", "PIPELINE", "CREATE PIPELINE",
        "START PIPELINE", "STOP PIPELINE", "DROP PIPELINE", "ALTER PIPELINE",
        "SHOW LEAVES", "SHOW AGGREGATORS", "GLOBAL", "UNIFORM", "LINEARIZABLE",
        "SELECT INTO OUTFILE", "LOAD DATA", "COMPUTE POOL", "SKIP LIST",
        "STRONG", "EVENTUAL", "IF NOT EXISTS", "IS NOT NULL",
    ],
    "sql.singlestore_datatypes": [
        "TINYINT", "SMALLINT", "MEDIUMINT", "INT", "INTEGER", "BIGINT",
        "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL", "BOOL", "BIT",
        "DATE", "TIME", "DATETIME", "TIMESTAMP", "YEAR", "CHAR", "VARCHAR",
        "TINYTEXT", "TEXT", "MEDIUMTEXT", "LONGTEXT", "TINYBLOB", "BLOB",
        "MEDIUMBLOB", "LONGBLOB", "VARBINARY", "BINARY", "JSON", "VECTOR",
        "GEOGRAPHY", "GEOGRAPHYPOINT", "ENUM",
    ],
    "sql.singlestore_functions": [
        "LAST_INSERT_ID", "GROUP_CONCAT", "MD5", "SHA1", "SHA2", "UUID",
        "NOW", "UTC_TIMESTAMP", "UNIX_TIMESTAMP", "FROM_UNIXTIME",
        "DATE_FORMAT", "DATEDIFF", "DATE_ADD", "DATE_SUB", "CURDATE",
        "CURTIME", "DATABASE", "SCHEMA", "USER", "VERSION", "COALESCE",
        "IFNULL", "NULLIF", "JSON_EXTRACT_JSON", "JSON_EXTRACT_STRING",
        "JSON_EXTRACT_BIGINT", "JSON_EXTRACT_DOUBLE", "JSON_BUILD_OBJECT",
        "GEOGRAPHY_POINT", "GEOGRAPHY_AREA", "GEOGRAPHY_DISTANCE",
        "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE",
        "LAST_VALUE", "REGEXP_REPLACE", "REGEXP_LIKE", "SUBSTR", "INSTR",
        "LPAD", "RPAD", "TRIM", "CONCAT_WS", "HEX", "UNHEX", "ABS", "MOD",
        "POW", "SQRT", "FLOOR", "CEIL", "ROUND",
    ],
    "sql.n1ql_keywords": [
        "USE KEYS", "NEST", "UNNEST", "LET", "LETTING", "MISSING",
        "SATISFIES", "EVERY", "RAW", "ADVISE", "EXPLAIN", "INFER",
        "PREPARE", "EXECUTE", "BUILD INDEX", "CREATE PRIMARY INDEX",
        "RETURNING", "ON KEY", "ON PRIMARY KEY", "WITHIN", "FIRST",
        "ARRAY", "OBJECT", "IS VALUED", "IS NOT MISSING", "NOT EXISTS",
        "LATERAL",
    ],
    "sql.n1ql_datatypes": [
        "OBJECT", "ARRAY", "STRING", "NUMBER", "BOOLEAN", "MISSING",
    ],
    "sql.n1ql_functions": [
        "META", "BASE64", "LOWER", "UPPER", "LENGTH", "TRIM", "LTRIM",
        "RTRIM", "SUBSTR", "POSITION", "REPLACE", "REPEAT", "SPLIT",
        "CONCAT", "CONTAINS", "TOKENS", "ISVALUED", "ISARRAY", "ISOBJECT",
        "ISSTRING", "ISNUMBER", "ISBOOLEAN", "TOARRAY", "TOOBJECT",
        "TOSTRING", "TONUMBER", "TOBOOLEAN", "MILLIS", "STR_TO_MILLIS",
        "MILLIS_TO_STR", "MILLIS_TO_UTC", "NOW_MILLIS", "CLOCK_MILLIS",
        "UUID", "RANDOM", "ARRAY_AGG", "ARRAY_APPEND", "ARRAY_PREPEND",
        "ARRAY_CONCAT", "ARRAY_DISTINCT", "ARRAY_FLATTEN",
        "ARRAY_INTERSECT", "ARRAY_UNION", "ARRAY_SORT", "ARRAY_LENGTH",
        "OBJECT_ADD", "OBJECT_PUT", "OBJECT_REMOVE", "OBJECT_NAMES",
        "OBJECT_PAIRS", "OBJECT_LENGTH", "IFMISSING", "IFMISSINGORNULL",
        "IFNULL", "IFINFO", "MISSINGIF", "NULLIF", "LEAST", "GREATEST",
    ],
}

# sqls source files -> target sets (driver-backed dialects)
SQLS_MERGE = {
    "mysql8Keyword": "sql.mysql_keywords",
    "mysql8Function": "sql.mysql_functions",
    "postgresql13Keywords": "sql.pg_keywords",
    "mssqlKeywords": "sql.tsql_keywords",
    "sqliteKeywords": "sql.sqlite_keywords",
    "oracleReservedWords": "sql.oracle_keywords",
    "oracleKeyWords": "sql.oracle_keywords",
}

# sets that gain the sqls core keyword table (generic ANSI layer)
CORE_TARGET = "sql.keywords"

SET_RE = re.compile(r'([ \t]*)<set\s+name="([^"]+)"([^>]*)>(.*?)</set>', re.S)
COMPLETION_RE = re.compile(r'<completion string="([^"]*)"\s*/>')
BEHAVIOR_RE = re.compile(r'<behavior[^>]*>.*?</behavior>', re.S)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_sqls_lists(src_root: Path) -> dict:
    lists = {}
    for f in sorted((src_root / "dialect").glob("*.go")):
        src = f.read_text()
        for name, body in re.findall(r"var (\w+) = \[\]string\{(.*?)\n\}", src, re.S):
            lists[name] = re.findall(r'"([A-Z_0-9]+)"', body)
    core = re.findall(r'"([A-Z_0-9]+)":\s+\w+,', (src_root / "dialect" / "keyword.go").read_text())
    lists["__core__"] = core
    return lists


def merge_set(match, additions) -> tuple:
    indent, name, attrs, body = match.group(1), match.group(2), match.group(3), match.group(4)
    existing = COMPLETION_RE.findall(body)
    behavior = BEHAVIOR_RE.search(body)
    merged = sorted({e.strip().upper() if e.strip() == e.strip().upper() else e.strip()
                     for e in existing} | {a.upper() for a in additions})
    lines = [f'{indent}<set name="{name}"{attrs}>']
    if behavior:
        lines.append(f"  {indent}{behavior.group(0).strip()}")
    for item in merged:
        lines.append(f'  {indent}<completion string="{esc(item)}" />')
    lines.append(f"{indent}</set>")
    stats[name] = (len(existing), len(merged))
    return name, "\n".join(lines), match.start(), match.end()


stats = {}


def main():
    if len(sys.argv) < 2:
        print("usage: gen-completions.py <path-to-sqls-source> [path-to-SQL.xml]",
              file=sys.stderr)
        sys.exit(1)

    src_root = Path(sys.argv[1])
    xml_path = Path(sys.argv[2] if len(sys.argv) > 2
                    else "SQL.novaextension/Completions/SQL.xml")
    xml = xml_path.read_text()

    lists = load_sqls_lists(src_root)

    # Build additions per set name
    additions = {name: [e for e in entries if len(e) > 1]
                 for name, entries in HAND.items()}
    for src_name, target in SQLS_MERGE.items():
        additions.setdefault(target, []).extend(lists.get(src_name, []))
    additions.setdefault(CORE_TARGET, []).extend(lists.get("__core__", []))

    # Merge into existing sets (union, never drop curated entries)
    out, pos = [], 0
    seen = set()
    for m in SET_RE.finditer(xml):
        name = m.group(2)
        if name in additions:
            _, block, start, end = merge_set(m, additions[name])
            out.append(xml[pos:start])
            out.append(block)
            pos = end
            seen.add(name)
    out.append(xml[pos:])
    xml = "".join(out)

    # New set blocks (not yet present) appended before </completions>
    new_blocks = []
    for name, entries in additions.items():
        if name in seen:
            continue
        lines = [f'  <set name="{name}" symbol="keyword" case-insensitive="true">']
        for item in sorted({e.upper() for e in entries}):
            lines.append(f'    <completion string="{esc(item)}" />')
        lines.append("  </set>")
        new_blocks.append("\n".join(lines))
        stats[name] = (0, len(entries))
    if new_blocks:
        block_text = "\n\n  <!-- Generated: dialect sets that had no curated block -->\n  "
        xml = xml.replace("</completions>",
                          block_text + "\n\n  ".join(new_blocks) + "\n\n</completions>")
        # wire the new oracle keyword set into its provider
        if "sql.oracle_keywords" in stats and "<set>sql.oracle_keywords</set>" not in xml:
            xml = xml.replace(
                "<set>sql.oracle_datatypes</set>",
                "<set>sql.oracle_keywords</set>\n    <set>sql.oracle_datatypes</set>",
                1,
            )

    xml_path.write_text(xml)

    added = sum((n - o) for o, n in stats.values())
    print(f"updated {len(stats)} sets, +{added} completions")
    for name in sorted(stats):
        old, new = stats[name]
        print(f"  {name}: {old} -> {new}")


if __name__ == "__main__":
    main()
