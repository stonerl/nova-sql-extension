-- IBM SQL PL / DB2 test file (syntax: sqlpl)
-- also: .db2i, .cql, .inc, .tab, .udf, .viw
CREATE TABLE EMPLOYEE (
  EMPNO CHAR(6) NOT NULL,
  FIRSTNME VARCHAR(12) NOT NULL,
  WORKDEPT CHAR(3),
  SALARY DECIMAL(9, 2)
) IN DSN8D81P;

CREATE PROCEDURE raise_salary (IN p_empno CHAR(6), INOUT p_salary DECIMAL(9, 2)) DYNAMIC RESULT SETS 1 BEGIN
DECLARE v_dept CHAR(3);

DECLARE c1 CURSOR
WITH
RETURN FOR
SELECT
  deptname
FROM
  department
WHERE
  deptno = v_dept;

SELECT
  salary
INTO
  p_salary
FROM
  employee
WHERE
  empno = p_empno;

SET
  v_dept = 'D11';

WHILE (p_salary < 50000) DO
SET
  p_salary = p_salary + 1000;

END
WHILE;

OPEN c1;

END;

CREATE FUNCTION get_bonus (p_empno CHAR(6)) RETURNS DECIMAL(9, 2) BEGIN
DECLARE v_bonus DECIMAL(9, 2);

SET
  v_bonus = (
    SELECT
      salary * 0.1
    FROM
      employee
    WHERE
      empno = p_empno
  );

RETURN v_bonus;

END;

WITH
  cte AS (
    SELECT
      empno,
      salary
    FROM
      employee
    WHERE
      salary > 40000
  )
SELECT
  *
FROM
  cte
ORDER BY
  salary DESC;

CALL get_bonus ('000010', ?);
