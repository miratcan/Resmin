DROP TABLE IF EXISTS question_question_bkp;

ALTER TABLE question_question RENAME TO question_question_bkp;

CREATE TABLE "question_question" (
    "id" integer NOT NULL PRIMARY KEY,
    "owner_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "created_at" datetime NOT NULL,
    "text" varchar(512) NOT NULL,
    "is_anonymouse" bool NOT NULL,
    "updated_at" datetime NOT NULL,
    "is_featured" bool NOT NULL,
    "merged_to_id" integer
);

INSERT INTO "question_question" select id, owner_id, created_at, text, is_anonymouse, updated_at, is_featured, null from question_question_bkp;