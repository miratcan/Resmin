CREATE VIRTUAL TABLE IF NOT EXISTS question_cache USING fts3(id, text);

CREATE TRIGGER IF NOT EXISTS question_inserted AFTER INSERT ON question_question
BEGIN
   INSERT INTO question_cache(id, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS question_deleted AFTER DELETE ON question_question
BEGIN
    DELETE question_cache WHERE id=old.id;
END;

CREATE TRIGGER IF NOT EXISTS question_updated AFTER UPDATE ON question_question
BEGIN
    DELETE question_cache WHERE id=old.id;
END;

CREATE TRIGGER IF NOT EXISTS trigger_name AFTER UPDATE OF text ON question_question
BEGIN
    UPDATE question_cache SET text=new.text WHERE id = old.id;
END;