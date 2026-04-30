-- Example subjects that are inserted automatically when the database has no subjects.

INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('School Trip Destination', 'Choose where the class should go on the next school trip.', 1, NULL);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Oslo' FROM subjects WHERE title = 'School Trip Destination';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Bergen' FROM subjects WHERE title = 'School Trip Destination';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Trondheim' FROM subjects WHERE title = 'School Trip Destination';

INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('New Cafeteria Menu Item', 'Vote for the food item you want to see added to the cafeteria menu.', 0, NULL);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Tacos' FROM subjects WHERE title = 'New Cafeteria Menu Item';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Pasta Bake' FROM subjects WHERE title = 'New Cafeteria Menu Item';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Chicken Wrap' FROM subjects WHERE title = 'New Cafeteria Menu Item';

INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('Best Day for a Coding Workshop', 'Pick the day that works best for an extra coding workshop after school.', 1, NULL);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Monday' FROM subjects WHERE title = 'Best Day for a Coding Workshop';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Wednesday' FROM subjects WHERE title = 'Best Day for a Coding Workshop';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Friday' FROM subjects WHERE title = 'Best Day for a Coding Workshop';
