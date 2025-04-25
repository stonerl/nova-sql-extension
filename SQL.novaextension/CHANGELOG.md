## 1.2.0 – 2025-04-25

### Added

- **Dialect-aware completions**: split SQL completion into a pure ANSI-generic provider plus per-dialect providers for SQLite, HiveQL, BigQuery, Snowflake, Redshift, Trino, SingleStore, SparkSQL, FlinkSQL and N1QL
- **Vendor-specific sets**: extracted all non-ANSI keywords, data types and functions into their own `<set>` blocks
- **Syntax-triggered loading**: each provider now only fires for its `<syntax>` (e.g. `mysql`, `postgresql`, `tsql`, etc.)

### Changed

- Renamed generic provider to `sql-generic` and pruned it to true ANSI-SQL (SQL:2016) only
- Removed MySQL/PostgreSQL/Oracle extras from ANSI core sets

### Fixed

- Ensured `WHEN`, `THEN`, `ELSE` and other ANSI CASE keywords are available in generic completions

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
