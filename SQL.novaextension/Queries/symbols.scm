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
; Common Table Expressions (WITH … AS …)
; ——————————————————————————————
(
  (cte
     (identifier) @name
  ) @subtree
  (#set! role struct)
)
