ALTER TABLE question_question RENAME TO question_question_bkp;
ALTER TABLE question_answer RENAME TO question_answer_bkp;

CREATE TABLE "question_question" (
    "id" integer NOT NULL PRIMARY KEY,
    "owner_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "created_at" datetime NOT NULL,
    "text" varchar(512) NOT NULL,
    "is_anonymouse" bool NOT NULL,
    "updated_at" datetime NOT NULL,
    "is_featured" bool NOT NULL
 );

CREATE TABLE "question_answer" (
    "id" integer NOT NULL PRIMARY KEY,
    "owner_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "created_at" datetime NOT NULL,
    "question_id" integer NOT NULL REFERENCES "question_question" ("id"),
    "image" varchar(100) NOT NULL,
    "note" varchar(255),
    "is_nsfw" bool NOT NULL,
    "is_anonymouse" bool NOT NULL,
    "status" smallint unsigned NOT NULL
);

INSERT INTO question_question 
SELECT "question_basemodel"."id", 
       "question_basemodel"."owner_id", 
       "question_basemodel"."created_at", 
       "question_question_bkp"."text", 
       "question_question_bkp"."is_anonymouse", 
       "question_question_bkp"."updated_at", 
       "question_question_bkp"."is_featured" 
FROM   "question_question_bkp" 
INNER JOIN "question_basemodel" 
ON ("question_question_bkp"."basemodel_ptr_id" = "question_basemodel"."id" );

INSERT INTO question_answer 
SELECT "question_basemodel"."id", 
       "question_basemodel"."owner_id", 
       "question_basemodel"."created_at", 
       "question_answer_bkp"."question_id", 
       "question_answer_bkp"."image", 
       "question_answer_bkp"."note", 
       "question_answer_bkp"."is_nsfw", 
       "question_answer_bkp"."is_anonymouse", 
       "question_answer_bkp"."status" 
FROM   "question_answer_bkp" 
INNER JOIN "question_basemodel" 
ON ( "question_answer_bkp"."basemodel_ptr_id" = "question_basemodel"."id" ); 