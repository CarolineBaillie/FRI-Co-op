-- SQLite

CREATE TABLE user
(
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT,
    host INTEGER
);

CREATE TABLE profile
(
    id INTEGER,
    name TEXT,
    username TEXT,
    bio TEXT,
    race TEXT,
    age TEXT,
    location TEXT,
    phone TEXT,
    email TEXT,
    info TEXT
);

CREATE TABLE events
(
    id INTEGER,
    eventName TEXT,
    description TEXT,
    date TEXT,
    time TEXT,
    location TEXT,
    contact TEXT,
    info TEXT
);

CREATE TABLE friends
(
    username1 TEXT,
    username2 TEXT
);

CREATE TABLE stories
(
    id INTEGER,
    username TEXT,
    story TEXT
);

DROP TABLE user;
DROP TABLE profile;
DROP TABLE events;
DROP TABLE friends;
DROP TABLE stories;

SELECT * FROM user;
SELECT *
FROM profile;

SELECT *
FROM friends;

DELETE FROM profile WHERE id=1;
DELETE FROM user WHERE id=1;


INSERT INTO profile
    (id,username,story)
VALUES
    (1, "test2", "This is a test to see if it works, which hopefully it does we shall see though.");

UPDATE profile
SET id = 1 WHERE username="JennyE";