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
