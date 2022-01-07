-- Create Tables
CREATE TABLE IF NOT EXISTS user (
    username VARCHAR(90) PRIMARY KEY,
    role INTEGER NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    creator VARCHAR(90) NOT NULL,
    assignee VARCHAR(90),
    category_id INTEGER,

    CONSTRAINT ticket_creator_fk FOREIGN KEY (creator) REFERENCES user(username),
    CONSTRAINT ticket_assignee_fk FOREIGN KEY (assignee) REFERENCES user(username),
    CONSTRAINT ticket_category_fk FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE IF NOT EXISTS category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,

    CONSTRAINT category_name_unique_constraint UNIQUE (name)
);

-- Populate Categories

INSERT INTO category (name) VALUES ('bug');
INSERT INTO category (name) VALUES ('architecture');
INSERT INTO category (name) VALUES ('minor');
INSERT INTO category (name) VALUES ('major');
INSERT INTO category (name) VALUES ('critical');