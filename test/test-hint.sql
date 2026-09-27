-- @mariadb
-- This file has a .sql extension but declares MariaDB as its dialect.
-- Nova should detect the `mariadb` syntax from the first-line hint.
CREATE TABLE `hint_demo` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100),
  PRIMARY KEY (`id`)
);

INSERT INTO
  `hint_demo` (`name`)
VALUES
  ('Ada');

SELECT
  *
FROM
  `hint_demo`
WHERE
  `name` RLIKE '^A';
