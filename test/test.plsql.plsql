-- Oracle PL/SQL test file (syntax: plsql)
CREATE
OR REPLACE PACKAGE emp_pkg AS TYPE emp_tab IS TABLE OF employees % ROWTYPE;

PROCEDURE raise_salary (p_id IN employees.id % TYPE, p_pct IN NUMBER);

FUNCTION get_name (p_id IN employees.id % TYPE) RETURN VARCHAR2;

END emp_pkg;

/ CREATE
OR REPLACE PACKAGE BODY emp_pkg AS PROCEDURE raise_salary (p_id IN employees.id % TYPE, p_pct IN NUMBER) IS v_current NUMBER;

BEGIN
SELECT
  salary INTO v_current
FROM
  employees
WHERE
  id = p_id;

UPDATE employees
SET
  salary = v_current * (1 + p_pct)
WHERE
  id = p_id;

COMMIT;

EXCEPTION WHEN NO_DATA_FOUND THEN NULL;

END raise_salary;

FUNCTION get_name (p_id IN employees.id % TYPE) RETURN VARCHAR2 IS v_name VARCHAR2(100);

BEGIN
SELECT
  name INTO v_name
FROM
  employees
WHERE
  id = p_id;

RETURN v_name;

END get_name;

END emp_pkg;

/ CREATE
OR REPLACE TRIGGER trg_audit AFTER
INSERT
  ON employees FOR EACH ROW
BEGIN
INSERT INTO
  audit_log
VALUES
  (:new.id, SYSDATE);

END;

/
SELECT
  e.name,
  d.dname
FROM
  employees e
  JOIN dept d ON e.deptno = d.deptno
WHERE
  ROWNUM <= 10
ORDER BY
  e.name;
