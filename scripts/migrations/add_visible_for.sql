ALTER TABLE question_answer ADD COLUMN visible_for int;
CREATE TABLE "question_answer_visible_for_users" (
    "id" integer NOT NULL PRIMARY KEY,
    "answer_id" integer NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    UNIQUE ("answer_id", "user_id")
)
;
