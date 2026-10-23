WITH father AS (
 SELECT person_id, AVG(earnings) AS father_mean, COUNT(*) AS father_n,
 AVG(age) AS father_age
 FROM income WHERE age BETWEEN 35 AND 44
 GROUP BY person_id HAVING COUNT(*) >= 3
), young AS (
 SELECT person_id, AVG(earnings) AS young_mean, COUNT(*) AS young_n,
 AVG(age) AS young_age, AVG(income_year-age) AS birth_year
 FROM income WHERE age BETWEEN 25 AND 29
 GROUP BY person_id HAVING COUNT(*) >= 2
), middle AS (
 SELECT person_id, AVG(earnings) AS middle_mean, COUNT(*) AS middle_n,
 AVG(age) AS middle_age
 FROM income WHERE age BETWEEN 40 AND 44
 GROUP BY person_id HAVING COUNT(*) >= 2
)
SELECT p.*, f.father_mean, f.father_n, f.father_age,
 y.young_mean, y.young_n, y.young_age, y.birth_year,
 m.middle_mean, m.middle_n, m.middle_age
FROM pairs AS p
JOIN father AS f ON p.father_id=f.person_id
JOIN young AS y ON p.child_id=y.person_id
JOIN middle AS m ON p.child_id=m.person_id;