
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS joke;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    nickname TEXT NOT NULL UNIQUE,
    joke_balance INTEGER DEFAULT 0,
    role TEXT DEFAULT 'User'
);

CREATE TABLE joke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    rating REAL DEFAULT 0,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    UNIQUE (user_id, title)
);
