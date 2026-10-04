## 2.1.0 – 2026-10-04

### Added

- **Object-management statements**: the tree-sitter grammar now parses
  `GRANT`, `REVOKE`, `USE`, `DESCRIBE`/`DESC`, `CALL`/`EXEC`/`EXECUTE`,
  `LOCK`/`UNLOCK TABLES`, `KILL`, `CHECKPOINT`, `GO`, `DELIMITER` and
  `LOAD DATA` (MySQL and Hive flavors), plus wider `SHOW` variants
  (`SHOW DATABASES`, `SHOW GRANTS [FOR]`, `SHOW SCHEMAS`), T-SQL `IF …
ELSE` and column options (`IDENTITY(1,1)`, SQLite `AUTOINCREMENT`,
  Redshift `DISTKEY`/`SORTKEY`/`DISTSTYLE`/`ENCODE`), `LISTAGG … WITHIN
GROUP`, Redshift `UNLOAD` options and `INSERT OVERWRITE DIRECTORY`.
- **Full keyword highlighting**: every keyword the grammar supports is now
  styled — 52 previously unstyled nodes (`SHOW`, `COPY`, `UNLOAD`,
  `MATERIALIZED`, `RECURSIVE`, Hive file formats, PostgreSQL `COPY`
  options, type aliases such as `INTEGER`/`PRECISION`, …)
- **Outline symbols** for `CREATE DATABASE`, `CREATE SCHEMA`,
  `CREATE SEQUENCE` and `CREATE ROLE/USER`
- **Exhaustive dialect completions** (`Completions/SQL.xml` grew from
  ~860 to ~4100 entries): keyword/function/datatype sets now generated
  from the sqls dialect lists (MySQL, PostgreSQL, T-SQL, SQLite, Oracle)
  and curated lists for Snowflake, BigQuery, Redshift, SparkSQL, Trino,
  HiveQL, FlinkSQL, SingleStore, N1QL and SQL PL.
- **Dialect-correct keyword completions without a database**: the bundled
  sqls now maps the document's languageId to a driver keyword list
  (MySQL/MariaDB → MySQL, T-SQL → MSSQL, PL/SQL → Oracle, …); dialects
  without an sqls driver fall back to the core SQL keyword table instead
  of the previous sqlite-only list
- **Keyword hover** for words the sqls lexer does not know but the
  grammar parses (Hive file formats, PostgreSQL index methods and `COPY`
  options, type aliases, …) — hover coverage now spans the full grammar
  vocabulary (~1650 keywords)
- `.ddl` files now detect as generic SQL (the README stated this, but
  no detector matched)

### Changed

- `scripts/lsp_probe.py` gained `--completions`, which asserts
  dialect-correct keyword completions across all languageIds without a
  database connection
- `scripts/gen-keyword-docs.py` emits `coreKeywords` (fallback keyword
  list) and merges grammar-only words into the hover universe

## 2.0.1 – 2026-09-30

### Fixed

- The language server is now stopped explicitly on extension
  deactivation, in addition to Nova's disposal of `nova.subscriptions`
- Crash detection and automatic restart for the bundled language server:
  launch failures and unexpected stops are now detected via Nova's
  `onDidStop` event and the server is relaunched with exponential
  backoff (1 s to 30 s cap; a stable run of over 60 s resets the
  backoff)

### Changed

- The _Language Server Info_ report now includes the server's live
  state (`running`/`stopped`)

## 2.0.0 – 2026-09-27

### Added

- **Language server support**: bundled the
  [sqls](https://github.com/sqls-server/sqls) v0.2.48 language server as a
  universal, Developer ID–signed binary for hover documentation,
  schema-aware completions and signature help (enabled by default;
  hover on tables/columns becomes richer with a DB connection in
  `~/.config/sqls/config.yml`)
- **Keyword hover documentation**: hovering SQL keywords (`SELECT`,
  `RLIKE`, …) now shows an explainer for ~1600 keywords. Implemented by
  patching the bundled [sqls](https://github.com/sqls-server/sqls)
  language server (MIT; modification included as
  `patches/sqls/v0.2.48/keyword-hover.patch`, rebuilt via
  `scripts/build-sqls.sh`)
- **Dialect-aware hover links**: the documentation footer links to the
  docs matching the open file's dialect (e.g. PostgreSQL docs in
  PostgreSQL files) for all supported dialects
- **MariaDB syntax**: new dedicated MariaDB document type — `.mariadb.sql`
  files report `mariadb` instead of `mysql`, with MariaDB-specific hover
  links and completions served by the MySQL provider
- New commands: **Restart Language Server**, **Language Server Info**
- New preferences: `Enable Language Server`, `Custom sqls Binary Path`

## 1.3.0 – 2026-09-27

### Added

- **Queries**: highlighted new v0.3.11 grammar keywords (`RLIKE`, `WHILE`,
  `POLICY`, `REFRESH`, `PUBLIC`, `INCLUDE`, `SPLIT`, `TABLETS`,
  `CURRENT_ROLE`, plus RLS modifiers); symbolicated stored procedures and
  row-level security policies; folded procedure bodies and `WHILE` loops
- **Completions**: RLIKE/REGEXP/DEFINER for MySQL, policy-keyword set for
  PostgreSQL, `OBJECT_ID` for T-SQL, `SPLIT TABLETS INCLUDE RLIKE` for
  SingleStore; new snippets for procedures, materialized views, RLS
  policies and `WHILE` loops

### Changed

- Updated the `tree-sitter-sql` grammar submodule (DerekStride) to the
  `gh-pages` deployment tip (v0.3.11), parser ABI 15
- Rebuilt `Syntaxes/libtree-sitter-sql.dylib` as a universal binary
  (arm64 + x86_64) linked against Nova's SyntaxKit framework; the dylib
  is now signed with a Developer ID so macOS accepts it when the
  extension is loaded on other machines
- Vendor build tooling under `scripts/` (`compile_parser.sh` + `Makefile`,
  courtesy of Panic) so the parser can be rebuilt with:
  `./scripts/compile_parser.sh tree-sitter-sql /Applications/Nova.app`

## 1.2.1 – 2025-04-26

### Fixed

- Corrected syntax name from `hivesql` -> `hiveql`

## 1.2.0 – 2025-04-25

### Added

- **Dialect-aware completions**: split SQL completion into a pure ANSI-generic
  provider plus per-dialect providers for SQLite, HiveQL, BigQuery, Snowflake,
  Redshift, Trino, SingleStore, SparkSQL, FlinkSQL and N1QL
- **Vendor-specific sets**: extracted all non-ANSI keywords, data types and
  functions into their own `<set>` blocks
- **Syntax-triggered loading**: each provider now only fires for its
  `<syntax>` (e.g. `mysql`, `postgresql`, `tsql`, etc.)

### Changed

- Renamed generic provider to `sql-generic` and pruned it to true
  ANSI-SQL (SQL:2016) only
- Removed MySQL/PostgreSQL/Oracle extras from ANSI core sets

### Fixed

- Ensured `WHEN`, `THEN`, `ELSE` and other ANSI CASE keywords are available
  in generic completions

## 1.1.1 – 2025‑04‑25

### Added

- added `WHERE` keyword to completions

## 1.1.0 – 2025‑04‑25

### Changed

- Refined injection handling for better embedded language support
- Added dialect-specific indentation rules for improved formatting consistency

Initial release

## 1.0.0 – 2025‑04‑24

Initial release
