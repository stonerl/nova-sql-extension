; ——————————————————————————————
; Tables
; ——————————————————————————————
(
  (create_table
     (object_reference) @name
  ) @subtree
  (#set! role type)
)

; ——————————————————————————————
; Views
; ——————————————————————————————
(
  (create_materialized_view
     (object_reference) @name
  ) @subtree
  (#set! role type)
)

(
  (create_view
     (object_reference) @name
  ) @subtree
  (#set! role type)
)

; ——————————————————————————————
; Indexes
; ——————————————————————————————
(
  (create_index
     (identifier) @name
  ) @subtree
  (#set! role property)
)

; ——————————————————————————————
; Functions & Stored Procedures
; ——————————————————————————————
(
  (create_function
     (object_reference) @name
  ) @subtree
  (#set! role function)
)

; ——————————————————————————————
; Triggers
; ——————————————————————————————
(
  (create_trigger
     (identifier) @name
  ) @subtree
  (#set! role function)
)

; ——————————————————————————————
; Stored Procedures (v0.3.11)
; ——————————————————————————————
(
  (create_procedure
     (object_reference) @name
  ) @subtree
  (#set! role function)
)

; ——————————————————————————————
; Row-Level Security Policies (v0.3.11)
; ——————————————————————————————
(
  (create_policy
     (object_reference) @name
  ) @subtree
  (#set! role type)
)

; ——————————————————————————————
; Common Table Expressions (WITH … AS …)
; ——————————————————————————————
(
  (cte
     (identifier) @name
  ) @subtree
  (#set! role struct)
)

(
  (select
     (keyword_select) @name
  ) @subtree
  (#set! role enum-member)
)
