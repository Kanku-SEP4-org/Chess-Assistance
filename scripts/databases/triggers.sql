SET search_path TO chess_assistant;

-- ============================================================
-- Trigger 4: update_opening_stats
-- Must be defined BEFORE trigger 2 so that on game INSERT the
-- opening stats are updated first, then when match status
-- transitions to 'complete' the dataset snapshot reflects
-- pre-game history.
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

CREATE TRIGGER trg_update_opening_stats
    AFTER INSERT ON game
    FOR EACH ROW
    WHEN (NEW.eco_code IS NOT NULL)
    EXECUTE FUNCTION fn_update_opening_stats();


-- ============================================================
-- Trigger 1: try_complete_match
-- Fires after INSERT on sensor tables or game.
-- When all required data is present for a match, marks it
-- 'complete'.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_try_complete_match()
RETURNS TRIGGER AS $$
DECLARE
    v_match_id        INTEGER;
    v_session_id      INTEGER;
    v_has_light       BOOLEAN;
    v_has_temperature BOOLEAN;
    v_has_water       BOOLEAN;
    v_has_co2         BOOLEAN;
    v_has_game        BOOLEAN;
    v_has_sleep       BOOLEAN;
BEGIN
    SET search_path TO chess_assistant;

    v_match_id := NEW.match_id;

    SELECT session_id INTO v_session_id FROM match WHERE id = v_match_id;

    SELECT EXISTS (SELECT 1 FROM light_sensor       WHERE match_id = v_match_id) INTO v_has_light;
    SELECT EXISTS (SELECT 1 FROM temperature_sensor  WHERE match_id = v_match_id) INTO v_has_temperature;
    SELECT EXISTS (SELECT 1 FROM water_sensor        WHERE match_id = v_match_id) INTO v_has_water;
    SELECT EXISTS (SELECT 1 FROM co2_sensor          WHERE match_id = v_match_id) INTO v_has_co2;
    SELECT EXISTS (SELECT 1 FROM game                WHERE match_id = v_match_id) INTO v_has_game;
    SELECT EXISTS (SELECT 1 FROM sleep_record        WHERE session_id = v_session_id) INTO v_has_sleep;

    IF v_has_light AND v_has_temperature AND v_has_water AND v_has_co2 AND v_has_game AND v_has_sleep THEN
        UPDATE match SET status = 'complete' WHERE id = v_match_id;
        RAISE NOTICE 'match % marked complete — all data present', v_match_id;
    ELSE
        RAISE NOTICE 'match % still pending — light=%, temp=%, water=%, co2=%, game=%, sleep=%',
            v_match_id, v_has_light, v_has_temperature, v_has_water, v_has_co2, v_has_game, v_has_sleep;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_complete_match_on_light
    AFTER INSERT ON light_sensor
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_match();

CREATE TRIGGER trg_complete_match_on_temperature
    AFTER INSERT ON temperature_sensor
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_match();

CREATE TRIGGER trg_complete_match_on_water
    AFTER INSERT ON water_sensor
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_match();

CREATE TRIGGER trg_complete_match_on_co2
    AFTER INSERT ON co2_sensor
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_match();

CREATE TRIGGER trg_complete_match_on_game
    AFTER INSERT ON game
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_match();


-- ============================================================
-- Trigger 1b: try_complete_matches_on_sleep
-- Fires after INSERT on sleep_record. Since sleep_record
-- references session (not match), this iterates over all
-- pending matches in the session and checks completeness.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_try_complete_matches_on_sleep()
RETURNS TRIGGER AS $$
DECLARE
    v_match RECORD;
    v_has_light       BOOLEAN;
    v_has_temperature BOOLEAN;
    v_has_water       BOOLEAN;
    v_has_co2         BOOLEAN;
    v_has_game        BOOLEAN;
BEGIN
    SET search_path TO chess_assistant;

    FOR v_match IN
        SELECT id FROM match
         WHERE session_id = NEW.session_id
           AND status = 'pending'
    LOOP
        SELECT EXISTS (SELECT 1 FROM light_sensor       WHERE match_id = v_match.id) INTO v_has_light;
        SELECT EXISTS (SELECT 1 FROM temperature_sensor  WHERE match_id = v_match.id) INTO v_has_temperature;
        SELECT EXISTS (SELECT 1 FROM water_sensor        WHERE match_id = v_match.id) INTO v_has_water;
        SELECT EXISTS (SELECT 1 FROM co2_sensor          WHERE match_id = v_match.id) INTO v_has_co2;
        SELECT EXISTS (SELECT 1 FROM game                WHERE match_id = v_match.id) INTO v_has_game;

        IF v_has_light AND v_has_temperature AND v_has_water AND v_has_co2 AND v_has_game THEN
            UPDATE match SET status = 'complete' WHERE id = v_match.id;
            RAISE NOTICE 'match % marked complete — all data present (triggered by sleep_record)', v_match.id;
        ELSE
            RAISE NOTICE 'match % still pending — light=%, temp=%, water=%, co2=%, game=%',
                v_match.id, v_has_light, v_has_temperature, v_has_water, v_has_co2, v_has_game;
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_complete_match_on_sleep
    AFTER INSERT ON sleep_record
    FOR EACH ROW EXECUTE FUNCTION fn_try_complete_matches_on_sleep();


-- ============================================================
-- Trigger 2: generate_dataset
-- Fires when match.status transitions pending → complete.
-- Aggregates sensor readings within the game time window and
-- snapshots opening history into the dataset table.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_generate_dataset()
RETURNS TRIGGER AS $$
DECLARE
    v_match_id    INTEGER;
    v_player_id   INTEGER;
    v_game_start  TIMESTAMP;
    v_game_end    TIMESTAMP;
    v_eco         VARCHAR(3);
    v_avg_lumen   NUMERIC(6,2);
    v_avg_celsius NUMERIC(6,2);
    v_avg_ppm     NUMERIC(6,2);
    v_avg_ml      NUMERIC(6,2);
    v_opening_win_rate   NUMERIC(5,2);
    v_opening_game_count INTEGER;
BEGIN
    SET search_path TO chess_assistant;

    v_match_id  := NEW.id;
    v_player_id := NEW.player_id;

    -- Get the game's time window and eco_code
    SELECT started_at, ended_at, eco_code
      INTO v_game_start, v_game_end, v_eco
      FROM game
     WHERE match_id = v_match_id;

    IF v_game_start IS NULL OR v_game_end IS NULL THEN
        RAISE NOTICE 'match %: game timestamps missing — skipping dataset generation', v_match_id;
        RETURN NEW;
    END IF;

    RAISE NOTICE 'match %: generating dataset for game window % to %', v_match_id, v_game_start, v_game_end;

    -- Aggregate sensor readings within the game time window only
    SELECT AVG(lumen)
      INTO v_avg_lumen
      FROM light_sensor
     WHERE match_id = v_match_id
       AND time_stamp BETWEEN v_game_start AND v_game_end;

    SELECT AVG(celsius)::NUMERIC(6,2)
      INTO v_avg_celsius
      FROM temperature_sensor
     WHERE match_id = v_match_id
       AND time_stamp BETWEEN v_game_start AND v_game_end;

    SELECT AVG(ppm)::NUMERIC(6,2)
      INTO v_avg_ppm
      FROM co2_sensor
     WHERE match_id = v_match_id
       AND time_stamp BETWEEN v_game_start AND v_game_end;

    SELECT AVG(ml)::NUMERIC(6,2)
      INTO v_avg_ml
      FROM water_sensor
     WHERE match_id = v_match_id
       AND time_stamp BETWEEN v_game_start AND v_game_end;

    -- Snapshot opening stats BEFORE this game was counted
    -- Trigger 4 already incremented, so subtract 1 from total_games
    SELECT
        CASE WHEN (total_games - 1) > 0
             THEN (player_wins::NUMERIC / (total_games - 1)) * 100
             ELSE NULL
        END,
        GREATEST(total_games - 1, 0)
      INTO v_opening_win_rate, v_opening_game_count
      FROM player_opening_stat
     WHERE player_id = v_player_id
       AND eco_code  = v_eco;

    RAISE NOTICE 'match %: opening snapshot eco=% win_rate=% game_count=%',
        v_match_id, v_eco, v_opening_win_rate, v_opening_game_count;

    INSERT INTO dataset (
        match_id,
        avg_lumen, avg_celsius, avg_ppm, avg_ml,
        sleep_duration, awake_duration,
        eco_code, total_ply, opening_ply,
        player_move_count, opponent_move_count,
        time_control, is_time_increase, time_increase_sec, is_berserk,
        duration_min,
        user_rating, opp_rating, rating_diff,
        is_player_piece_black, termination_type, result,
        player_opening_win_rate, player_opening_game_count
    )
    SELECT
        v_match_id,
        v_avg_lumen, v_avg_celsius, v_avg_ppm, v_avg_ml,
        sr.sleep_duration, sr.awake_duration,
        g.eco_code, g.total_ply, g.opening_ply,
        g.player_move_count, g.opponent_move_count,
        g.time_control, g.is_time_increase, g.time_increase_sec, g.is_berserk,
        g.duration_min,
        g.user_rating, g.opp_rating, g.rating_diff,
        g.is_player_piece_black, g.termination_type, g.result,
        v_opening_win_rate, v_opening_game_count
    FROM game g
    JOIN match m ON m.id = g.match_id
    JOIN sleep_record sr ON sr.session_id = m.session_id
    WHERE g.match_id = v_match_id
    ON CONFLICT (match_id) DO NOTHING;

    RAISE NOTICE 'match %: dataset row inserted', v_match_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_dataset
    AFTER UPDATE ON match
    FOR EACH ROW
    WHEN (NEW.status = 'complete' AND OLD.status = 'pending')
    EXECUTE FUNCTION fn_generate_dataset();


-- ============================================================
-- Trigger 3: update_game_count
-- Fires on the same pending → complete transition and
-- increments the parent session's game_count.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_update_game_count()
RETURNS TRIGGER AS $$
BEGIN
    SET search_path TO chess_assistant;

    UPDATE session
       SET game_count = game_count + 1
     WHERE id = NEW.session_id;

    RAISE NOTICE 'session %: game_count incremented', NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_game_count
    AFTER UPDATE ON match
    FOR EACH ROW
    WHEN (NEW.status = 'complete' AND OLD.status = 'pending')
    EXECUTE FUNCTION fn_update_game_count();


