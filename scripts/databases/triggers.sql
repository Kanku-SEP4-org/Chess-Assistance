SET search_path TO chess_assistant;

-- ============================================================
-- Trigger: update_opening_stats
-- Fires after INSERT on game. Updates per-player opening
-- statistics (win/loss/draw counts by eco_code).
-- ============================================================

CREATE OR REPLACE FUNCTION fn_update_opening_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_player_id INTEGER;
BEGIN
    SET search_path TO chess_assistant;

    SELECT player_id INTO v_player_id
      FROM match
     WHERE id = NEW.match_id;

    RAISE NOTICE 'game %: updating opening stats for player %, eco=%', NEW.id, v_player_id, NEW.eco_code;

    INSERT INTO player_opening_stat (player_id, eco_code, opening_name,
        player_as_white, player_as_black,
        player_wins, player_losses, player_draws,
        opp_as_white, opp_as_black,
        opp_wins, opp_losses)
    VALUES (
        v_player_id,
        NEW.eco_code,
        NEW.opening_name,
        CASE WHEN NOT NEW.is_player_piece_black THEN 1 ELSE 0 END,
        CASE WHEN NEW.is_player_piece_black THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'win'  THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'loss' THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'draw' THEN 1 ELSE 0 END,
        CASE WHEN NEW.is_player_piece_black THEN 1 ELSE 0 END,
        CASE WHEN NOT NEW.is_player_piece_black THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'loss' THEN 1 ELSE 0 END,
        CASE WHEN NEW.result = 'win'  THEN 1 ELSE 0 END
    )
    ON CONFLICT (player_id, eco_code) DO UPDATE SET
        opening_name   = COALESCE(EXCLUDED.opening_name, player_opening_stat.opening_name),
        player_as_white = player_opening_stat.player_as_white + EXCLUDED.player_as_white,
        player_as_black = player_opening_stat.player_as_black + EXCLUDED.player_as_black,
        player_wins    = player_opening_stat.player_wins    + EXCLUDED.player_wins,
        player_losses  = player_opening_stat.player_losses  + EXCLUDED.player_losses,
        player_draws   = player_opening_stat.player_draws   + EXCLUDED.player_draws,
        opp_as_white   = player_opening_stat.opp_as_white   + EXCLUDED.opp_as_white,
        opp_as_black   = player_opening_stat.opp_as_black   + EXCLUDED.opp_as_black,
        opp_wins       = player_opening_stat.opp_wins       + EXCLUDED.opp_wins,
        opp_losses     = player_opening_stat.opp_losses     + EXCLUDED.opp_losses;

    RAISE NOTICE 'Opening stats updated for player % eco=%', v_player_id, NEW.eco_code;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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

CREATE TRIGGER trg_sync_analysis_to_dataset
AFTER INSERT OR UPDATE ON game_analysis
FOR EACH ROW
EXECUTE FUNCTION sync_analysis_to_dataset();


CREATE TRIGGER trg_update_opening_stats
    AFTER INSERT ON game
    FOR EACH ROW
    WHEN (NEW.eco_code IS NOT NULL)
    EXECUTE FUNCTION fn_update_opening_stats();
