SET search_path TO chess_assistant;

CREATE OR REPLACE FUNCTION sync_analysis_to_dataset()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE dataset
    SET inaccuracy_cnt = NEW.inaccuracy_cnt,
        mistake_cnt    = NEW.mistake_cnt,
        blunder_cnt    = NEW.blunder_cnt,
        acpl           = NEW.acpl,
        accuracy       = NEW.accuracy
    FROM game
    WHERE game.id = NEW.game_id
      AND dataset.match_id = game.match_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_sync_analysis_to_dataset
AFTER INSERT OR UPDATE ON game_analysis
FOR EACH ROW
EXECUTE FUNCTION sync_analysis_to_dataset();
