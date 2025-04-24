; 0. SQL Comments
((comment) @comment.line)           ; captures “-- comment” style node-types.json](file-service://file-8SxEekpqK4LVQEtdRcXCKL)
((comment) @comment.block)          ; captures “/* comment */” style node-types.json](file-service://file-8SxEekpqK4LVQEtdRcXCKL)

;; 1. Function invocations → map to function identifiers
(invocation
  (object_reference
    name: (identifier) @identifier.function))

;; 2. Low-level “index/array” functions treated as function identifiers
[
  (keyword_gist)
  (keyword_btree)
  (keyword_hash)
  (keyword_spgist)
  (keyword_gin)
  (keyword_brin)
  (keyword_array)
] @identifier.function

;; 3. Schema-qualified and unqualified object references
(object_reference
  schema: (identifier) @identifier.type
  "." @operator)

(object_reference
  name: (identifier) @identifier.type)

;; 4. Column definitions and shorthand
(column_definition
  name: (identifier) @identifier.property)

(column
  (identifier) @identifier.property)

;; 5. Table/relation aliasing
(relation
  alias: (identifier) @identifier.variable)

(field
  name: (identifier) @identifier.property)

(term
  alias: (identifier) @identifier.variable)

;; 6. In-term CAST expressions
((term
   value: (cast
     name: (keyword_cast) @identifier.function
     parameter: [(literal)]?)))

;; 7. Table‐level options (name/value pairs)
(table_option
  name: (identifier) @identifier.property)

(table_option
  value: (identifier) @identifier.variable)

(table_option
  value: (identifier) @value.number
    (#match? @value.number "^[-+]?\\d+$"))

(table_option
  value: (identifier) @value.number
    (#match? @value.number "^[-+]?\\d*\\.\\d*$"))

;; 8. CREATE / DROP / ALTER … (<entity>) → typed identifiers
(create_database (identifier) @identifier.type)
(create_role     (identifier) @identifier.type)
(create_schema   (identifier) @identifier.type)

(drop_database   (identifier) @identifier.type)
(drop_role       (identifier) @identifier.type)
(drop_schema     (identifier) @identifier.type)

(alter_database  (identifier) @identifier.type)
(alter_role      (identifier) @identifier.type)
(alter_schema    (identifier) @identifier.type)

;; 9. String literals, comments, and marginalia
(literal)    @string
(comment)    @comment
(marginalia) @comment

;; 10. Numeric literals: integers & floats
((literal) @value.number
   (#match? @value.number "^[-+]?\\d+$"))

((literal) @value.number
  (#match? @value.number "^[-+]?\\d*\\.\\d*$"))

;; 11. Parameter placeholders
(parameter) @parameter

;; 12. Boolean literals
[
 (keyword_true)
 (keyword_false)
] @value.boolean

;; 13. Keyword modifiers (ASC, DESC, UNSIGNED, etc.)
[
 (keyword_asc)
 (keyword_desc)
 (keyword_terminated)
 (keyword_escaped)
 (keyword_unsigned)
 (keyword_nulls)
 (keyword_last)
 (keyword_delimited)
 (keyword_replication)
 (keyword_auto_increment)
 (keyword_default)
 (keyword_collate)
 (keyword_concurrently)
 (keyword_engine)
 (keyword_always)
 (keyword_generated)
 (keyword_preceding)
 (keyword_following)
 (keyword_first)
 (keyword_current_timestamp)
 (keyword_immutable)
 (keyword_atomic)
 (keyword_parallel)
 (keyword_leakproof)
 (keyword_safe)
 (keyword_cost)
 (keyword_strict)
] @keyword.modifier

;; 14. Conditional keywords (CASE…WHEN…THEN…ELSE)
[
 (keyword_case)
 (keyword_when)
 (keyword_then)
 (keyword_else)
] @keyword.condition

;; 15. Core SQL keywords (SELECT, FROM, JOIN, etc.)
[
  (keyword_select)
  (keyword_from)
  (keyword_where)
  (keyword_index)
  (keyword_join)
  (keyword_primary)
  (keyword_delete)
  (keyword_create)
  (keyword_insert)
  (keyword_merge)
  (keyword_distinct)
  (keyword_replace)
  (keyword_update)
  (keyword_into)
  (keyword_overwrite)
  (keyword_matched)
  (keyword_values)
  (keyword_value)
  (keyword_attribute)
  (keyword_set)
  (keyword_left)
  (keyword_right)
  (keyword_outer)
  (keyword_inner)
  (keyword_full)
  (keyword_order)
  (keyword_partition)
  (keyword_group)
  (keyword_with)
  (keyword_without)
  (keyword_as)
  (keyword_having)
  (keyword_limit)
  (keyword_offset)
  (keyword_table)
  (keyword_tables)
  (keyword_key)
  (keyword_references)
  (keyword_foreign)
  (keyword_constraint)
  (keyword_force)
  (keyword_use)
  (keyword_for)
  (keyword_if)
  (keyword_exists)
  (keyword_column)
  (keyword_columns)
  (keyword_cross)
  (keyword_lateral)
  (keyword_natural)
  (keyword_alter)
  (keyword_drop)
  (keyword_add)
  (keyword_view)
  (keyword_end)
  (keyword_is)
  (keyword_using)
  (keyword_between)
  (keyword_window)
  (keyword_no)
  (keyword_data)
  (keyword_type)
  (keyword_rename)
  (keyword_to)
  (keyword_schema)
  (keyword_owner)
  (keyword_authorization)
  (keyword_all)
  (keyword_any)
  (keyword_some)
  (keyword_returning)
  (keyword_begin)
  (keyword_commit)
  (keyword_rollback)
  (keyword_transaction)
  (keyword_only)
  (keyword_like)
  (keyword_similar)
  (keyword_over)
  (keyword_change)
  (keyword_modify)
  (keyword_after)
  (keyword_before)
  (keyword_range)
  (keyword_rows)
  (keyword_groups)
  (keyword_exclude)
  (keyword_current)
  (keyword_ties)
  (keyword_others)
  (keyword_zerofill)
  (keyword_format)
  (keyword_fields)
  (keyword_row)
  (keyword_sort)
  (keyword_compute)
  (keyword_comment)
  (keyword_location)
  (keyword_cached)
  (keyword_uncached)
  (keyword_lines)
  (keyword_stored)
  (keyword_virtual)
  (keyword_partitioned)
  (keyword_analyze)
  (keyword_explain)
  (keyword_verbose)
  (keyword_truncate)
  (keyword_rewrite)
  (keyword_optimize)
  (keyword_vacuum)
  (keyword_cache)
  (keyword_language)
  (keyword_called)
  (keyword_conflict)
  (keyword_declare)
  (keyword_filter)
  (keyword_function)
  (keyword_input)
  (keyword_name)
  (keyword_oid)
  (keyword_regclass)
  (keyword_regnamespace)
  (keyword_regproc)
  (keyword_regtype)
  (keyword_return)
  (keyword_returns)
  (keyword_setof)
  (keyword_stable)
  (keyword_support)
  (keyword_trigger)
  (keyword_unsafe)
  (keyword_admin)
  (keyword_connection)
  (keyword_cycle)
  (keyword_database)
  (keyword_encrypted)
  (keyword_increment)
  (keyword_logged)
  (keyword_none)
  (keyword_owned)
  (keyword_password)
  (keyword_reset)
  (keyword_role)
  (keyword_sequence)
  (keyword_start)
  (keyword_restart)
  (keyword_tablespace)
  (keyword_until)
  (keyword_user)
  (keyword_valid)
  (keyword_action)
  (keyword_definer)
  (keyword_version)
  (keyword_out)
  (keyword_inout)
  (keyword_variadic)
  (keyword_session)
  (keyword_isolation)
  (keyword_level)
  (keyword_serializable)
  (keyword_repeatable)
  (keyword_read)
  (keyword_write)
  (keyword_committed)
  (keyword_uncommitted)
  (keyword_deferrable)
  (keyword_names)
  (keyword_zone)
  (keyword_immediate)
  (keyword_deferred)
  (keyword_constraints)
  (keyword_snapshot)
  (keyword_characteristics)
  (keyword_off)
  (keyword_follows)
  (keyword_precedes)
  (keyword_each)
  (keyword_instead)
  (keyword_of)
  (keyword_initially)
  (keyword_old)
  (keyword_new)
  (keyword_referencing)
  (keyword_statement)
  (keyword_execute)
  (keyword_procedure)
] @keyword

;; 16. Restrictive modifiers (RESTRICT, UNIQUE, CASCADE, etc.)
[
 (keyword_restrict)
 (keyword_unbounded)
 (keyword_unique)
 (keyword_cascade)
 (keyword_delayed)
 (keyword_high_priority)
 (keyword_low_priority)
 (keyword_ignore)
 (keyword_nothing)
 (keyword_check)
 (keyword_option)
 (keyword_local)
 (keyword_cascaded)
 (keyword_wait)
 (keyword_nowait)
 (keyword_incremental)
 (keyword_noscan)
 (keyword_statistics)
 (keyword_maxvalue)
 (keyword_minvalue)
] @keyword.modifier

;; 17. Built-in storage/data-type keywords
[
  (keyword_int)
  (keyword_null)
  (keyword_boolean)
  (keyword_binary)
  (keyword_varbinary)
  (keyword_image)
  (keyword_bit)
  (keyword_inet)
  (keyword_character)
  (keyword_smallserial)
  (keyword_serial)
  (keyword_bigserial)
  (keyword_smallint)
  (keyword_mediumint)
  (keyword_bigint)
  (keyword_tinyint)
  (keyword_decimal)
  (keyword_float)
  (keyword_double)
  (keyword_numeric)
  (keyword_real)
  (keyword_money)
  (keyword_smallmoney)
  (keyword_char)
  (keyword_nchar)
  (keyword_varchar)
  (keyword_nvarchar)
  (keyword_varying)
  (keyword_text)
  (keyword_string)
  (keyword_uuid)
  (keyword_json)
  (keyword_jsonb)
  (keyword_xml)
  (keyword_bytea)
  (keyword_enum)
  (keyword_date)
  (keyword_datetime)
  (keyword_time)
  (keyword_datetime2)
  (keyword_datetimeoffset)
  (keyword_smalldatetime)
  (keyword_timestamp)
  (keyword_timestamptz)
  (keyword_geometry)
  (keyword_geography)
  (keyword_box2d)
  (keyword_box3d)
  (keyword_interval)
] @identifier.type.builtin

;; 18. Logical/set operators as keywords
[
  (keyword_in)
  (keyword_and)
  (keyword_or)
  (keyword_not)
  (keyword_by)
  (keyword_on)
  (keyword_do)
  (keyword_union)
  (keyword_except)
  (keyword_intersect)
] @keyword

;; 19. Arithmetic & comparison operators
[
  "+"
  "-"
  "*"
  "/"
  "%"
  "^"
  ":="
  "="
  "<"
  "<="
  "!="
  ">="
  ">"
  "<>"
  (op_other)
  (op_unary_other)
] @operator

;; 20. Bracket characters
[
  "("
  ")"
] @bracket

;; 21. Statement delimiters (semicolon, comma, dot)
[
  ";"
  ","
  "."
] @punctuation.delimiter

;; 22. Infix/binary expressions
(binary_expression) @operator

;; 23. BETWEEN … AND …
(between_expression) @operator

;; 24. CASE … WHEN … THEN … ELSE … END
(case) @keyword

;; 25. CAST(…) AS …
(cast
  name: (keyword_cast) @support.function)

;; 26. EXISTS(subquery)
(exists) @keyword

;; 27. INTERVAL literals
(interval) @storage.type

;; 28. Parenthesized & subquery expressions
(parenthesized_expression) @punctuation.bracket
(subquery)              @punctuation.bracket

;; 29. Array subscripts & constructors
(subscript) @punctuation.bracket
(array)     @punctuation.bracket

;; 30. Unary expressions (prefix operators)
(unary_expression) @operator

;; 31. Window functions
(window_function) @support.function

;; 32. Comma-separated lists
(list) @punctuation.delimiter

;; 33. Other operators (e.g. bitwise, concatenation)
[(op_other) (op_unary_other)] @operator.other

;; 99. Fallback: generic identifiers & literals
(identifier) @text
(literal)    @string
(parameter)  @constant
