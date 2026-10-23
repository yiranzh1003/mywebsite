SELECT c.person_id AS child_id, p.person_id AS father_id
FROM people AS c
JOIN people AS p ON c.father_family_id = p.family_id
 AND c.father_person_no = p.person_no
WHERE c.sex = 1 AND p.sex = 1
 AND c.father_family_id > 0 AND c.father_person_no > 0;