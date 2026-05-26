SET search_path TO chess_assistant;

CREATE OR REPLACE FUNCTION sync_analysis_to_dataset()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chess_assistant.dataset
    SET inaccuracy_cnt = NEW.inaccuracy_cnt,
        mistake_cnt    = NEW.mistake_cnt,
        blunder_cnt    = NEW.blunder_cnt,
        acpl           = NEW.acpl,
        accuracy       = NEW.accuracy
    FROM chess_assistant.game
    WHERE game.id = NEW.game_id
      AND dataset.match_id = game.match_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_analysis_to_dataset ON game_analysis;

CREATE TRIGGER trg_sync_analysis_to_dataset
AFTER INSERT OR UPDATE ON game_analysis
FOR EACH ROW
EXECUTE FUNCTION sync_analysis_to_dataset();
