BEGIN TRANSACTION;

CREATE TABLE "question_answer_BKP" (
    "basemodel_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "question_basemodel" ("id"),
    "question_id" integer NOT NULL REFERENCES "question_question" ("basemodel_ptr_id"),
    "image" varchar(100) NOT NULL,
    "note" varchar(255),
    "is_nsfw" bool NOT NULL,
    "is_anonymouse" bool NOT NULL,
    "status" smallint unsigned NOT NULL,
    "like_count" int);

INSERT INTO question_answer_BKP select * from question_answer;

DROP TABLE "question_answer";

CREATE TABLE "question_answer" (
    "basemodel_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "question_basemodel" ("id"),
    "question_id" integer NOT NULL REFERENCES "question_question" ("basemodel_ptr_id"),
    "image" varchar(100) NOT NULL,
    "note" varchar(255),
    "is_nsfw" bool NOT NULL,
    "is_anonymouse" bool NOT NULL,
    "status" smallint unsigned NOT NULL);

INSERT INTO question_answer select basemodel_ptr_id, question_id, image, note, is_nsfw, is_anonymouse, status from question_answer_BKP;

DROP TABLE "question_answer_BKP";

COMMIT;
