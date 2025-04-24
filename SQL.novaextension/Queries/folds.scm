;; Fold full BEGIN ... END procedure blocks
(transaction) @subtree
(#set! role block)
(#set! scope.byLine)

;; Fold blocks inside procedures (e.g., nested BEGIN ... END)
(block) @subtree
(#set! role block)
(#set! scope.byLine)

;; Fold individual statements inside transactions or blocks
(transaction (statement) @subtree)
(#set! role block)
(#set! scope.byLine)

(block (statement) @subtree)
(#set! role block)
(#set! scope.byLine)

;; Fold SQL constructs
(select) @subtree
(#set! role block)
(#set! scope.byLine)

(update) @subtree
(#set! role block)
(#set! scope.byLine)

(insert) @subtree
(#set! role block)
(#set! scope.byLine)

(case) @subtree
(#set! role block)
(#set! scope.byLine)

(subquery) @subtree
(#set! role block)
(#set! scope.byLine)

(cte) @subtree
(#set! role block)
(#set! scope.byLine)

;; Fallback for any multiline SQL statement
(statement) @subtree
(#set! scope.byLine)
