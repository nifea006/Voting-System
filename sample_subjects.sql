-- INSERT 10 USERS --
-- Example logins use username/email plus the passwords shown below.
INSERT INTO users (username, password_hash, email, phone, is_admin) VALUES
('Erik',   'erik123',   'erik@osloskolen.no',   '48291022', 0),
('Ingrid', 'ingrid123', 'ingrid@osloskolen.no', '59301844', 0),
('Lars',   'lars123',   'lars@osloskolen.no',   '92844710', 0),
('Astrid', 'astrid123', 'astrid@osloskolen.no', '70129388', 0),
('Soren',  'soren123',  'soren@osloskolen.no',  '88421039', 0),
('Freja',  'freja123',  'freja@osloskolen.no',  '55019283', 0),
('Mikkel', 'mikkel123', 'mikkel@osloskolen.no', '67409211', 0),
('Hanna',  'hanna123',  'hanna@osloskolen.no',  '33281940', 0),
('Bjorn',  'bjorn123',  'bjorn@osloskolen.no',  '99821055', 0),
('Ole',    'ole123',    'ole@osloskolen.no',    '44820119', 0);


-- SUBJECT A --
INSERT INTO subjects (title, description, is_anonymous, allow_vote_changes, allowed_chart_types, created_by)
VALUES ('A: Foretrukket Gymaktivitet', 'Stem på den gymaktiviteten elevene liker best.', 0, 1, 'bar,line,radar', 1);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Fotball' FROM subjects WHERE title='A: Foretrukket Gymaktivitet';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Gymnastikk' FROM subjects WHERE title='A: Foretrukket Gymaktivitet';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Svømming' FROM subjects WHERE title='A: Foretrukket Gymaktivitet';


-- SUBJECT B --
INSERT INTO subjects (title, description, is_anonymous, allow_vote_changes, allowed_chart_types, created_by)
VALUES ('B: Favoritt Nordisk Rett', 'Velg den mest ikoniske nordiske matretten.', 1, 0, 'doughnut,polarArea', 5);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Smørrebrød' FROM subjects WHERE title='B: Favoritt Nordisk Rett';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Kjøttkaker' FROM subjects WHERE title='B: Favoritt Nordisk Rett';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Räksmörgås' FROM subjects WHERE title='B: Favoritt Nordisk Rett';


-- SUBJECT C --
INSERT INTO subjects (title, description, is_anonymous, allow_vote_changes, allowed_chart_types, created_by)
VALUES ('C: Hvilken Sport Bør Skolen Legge Til?', 'Velg hvilken sport skolen bør tilby.', 0, 0, 'bar,polarArea', 8);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Basketball' FROM subjects WHERE title='C: Hvilken Sport Bør Skolen Legge Til?';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Volleyball' FROM subjects WHERE title='C: Hvilken Sport Bør Skolen Legge Til?';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Håndball' FROM subjects WHERE title='C: Hvilken Sport Bør Skolen Legge Til?';


-- SUBJECT D --
INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('D: Skolens Turmål', 'Velg hvor klassen skal dra på skoletur.', 1, 10);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Oslo' FROM subjects WHERE title='D: Skolens Turmål';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Bergen' FROM subjects WHERE title='D: Skolens Turmål';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Trondheim' FROM subjects WHERE title='D: Skolens Turmål';


-- SUBJECT E --
INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('E: Nytt Menyvalg i Kantinen', 'Stem på hvilken matrett som bør legges til i kantinen.', 0, 3);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Taco' FROM subjects WHERE title='E: Nytt Menyvalg i Kantinen';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Pastaform' FROM subjects WHERE title='E: Nytt Menyvalg i Kantinen';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Kyllingwrap' FROM subjects WHERE title='E: Nytt Menyvalg i Kantinen';


-- SUBJECT F --
INSERT INTO subjects (title, description, is_anonymous, created_by)
VALUES ('F: Beste Dag for Kodeverksted', 'Velg dagen som passer best for et kodeverksted etter skolen.', 1, NULL);

INSERT INTO subject_options (subject_id, label)
SELECT id, 'Mandag' FROM subjects WHERE title='F: Beste Dag for Kodeverksted';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Onsdag' FROM subjects WHERE title='F: Beste Dag for Kodeverksted';
INSERT INTO subject_options (subject_id, label)
SELECT id, 'Fredag' FROM subjects WHERE title='F: Beste Dag for Kodeverksted';


-- INSERT VOTES --
INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'A: Foretrukket Gymaktivitet'
  AND (
        (u.id % 3 = 1 AND o.label = 'Fotball') OR
        (u.id % 3 = 2 AND o.label = 'Gymnastikk') OR
        (u.id % 3 = 0 AND o.label = 'Svømming')
      );

INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'B: Favoritt Nordisk Rett'
  AND (
        (u.id % 3 = 1 AND o.label = 'Smørrebrød') OR
        (u.id % 3 = 2 AND o.label = 'Kjøttkaker') OR
        (u.id % 3 = 0 AND o.label = 'Räksmörgås')
      );

INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'C: Hvilken Sport Bør Skolen Legge Til?'
  AND (
        (u.id % 3 = 1 AND o.label = 'Basketball') OR
        (u.id % 3 = 2 AND o.label = 'Volleyball') OR
        (u.id % 3 = 0 AND o.label = 'Håndball')
      );

INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'D: Skolens Turmål'
  AND (
        (u.id % 3 = 1 AND o.label = 'Oslo') OR
        (u.id % 3 = 2 AND o.label = 'Bergen') OR
        (u.id % 3 = 0 AND o.label = 'Trondheim')
      );

INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'E: Nytt Menyvalg i Kantinen'
  AND (
        (u.id % 3 = 1 AND o.label = 'Taco') OR
        (u.id % 3 = 2 AND o.label = 'Pastaform') OR
        (u.id % 3 = 0 AND o.label = 'Kyllingwrap')
      );

INSERT INTO votes (subject_id, user_id, option_id)
SELECT s.id, u.id, o.id
FROM subjects s
JOIN users u
JOIN subject_options o ON o.subject_id = s.id
WHERE s.title = 'F: Beste Dag for Kodeverksted'
  AND (
        (u.id % 3 = 1 AND o.label = 'Mandag') OR
        (u.id % 3 = 2 AND o.label = 'Onsdag') OR
        (u.id % 3 = 0 AND o.label = 'Fredag')
      );
