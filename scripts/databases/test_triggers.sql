-- Test script for triggers
-- Runs inside a transaction that rolls back at the end,
-- so no test data is left in the database.
-- All verification output goes to RAISE NOTICE.
--
-- Usage:  psql -f scripts/databases/test_triggers.sql

BEGIN;
SET search_path TO chess_assistant;

DO $$
DECLARE
    v_player_id  INTEGER;
    v_room_id    INTEGER;
    v_session_id INTEGER;
    v_match_id   INTEGER;
    v_status     session_status;
    v_game_count INTEGER;
    v_game_start TIMESTAMP := '2026-05-12 10:00:00';
    v_game_end   TIMESTAMP := '2026-05-12 10:30:00';
BEGIN
    SET search_path TO chess_assistant;

    RAISE NOTICE '=== TEST: insert player & room ===';
    INSERT INTO player (username) VALUES ('test_player') RETURNING id INTO v_player_id;
    INSERT INTO room (perimeter, player_id) VALUES (25.50, v_player_id) RETURNING id INTO v_room_id;

    RAISE NOTICE '=== TEST: insert session ===';
    INSERT INTO session (started_at, player_id)
    VALUES ('2026-05-12 09:00:00', v_player_id)
    RETURNING id INTO v_session_id;

    RAISE NOTICE '=== TEST: insert match (status should be pending) ===';
    INSERT INTO match (match_date, session_id, player_id)
    VALUES ('2026-05-12', v_session_id, v_player_id)
    RETURNING id INTO v_match_id;

    SELECT status INTO v_status FROM match WHERE id = v_match_id;
    RAISE NOTICE 'match status after insert: %', v_status;

    RAISE NOTICE '=== TEST: insert game (eco_code=B02, result=win) ===';
    INSERT INTO game (
        lichess_game_id, time_control, is_time_increase, time_increase_sec,
        is_rated, source, eco_code, opening_name,
        total_ply, opening_ply, player_move_count, opponent_move_count,
        user_rating, opp_rating, rating_diff,
        is_player_piece_black, result, termination_type,
        started_at, ended_at, duration_min, match_id
    ) VALUES (
        'kAdOQKeh', 'blitz', true, 3,
        true, 'lobby', 'B02', 'Alekhine Defense',
        60, 8, 30, 30,
        1500, 1480, 20,
        false, 'win', 'resign',
        v_game_start, v_game_end, 30, v_match_id
    );

    SELECT status INTO v_status FROM match WHERE id = v_match_id;
    RAISE NOTICE 'match status after game: %', v_status;

    RAISE NOTICE '=== TEST: insert sleep_record ===';
    INSERT INTO sleep_record (sleep_time, awaken_time, session_id)
    VALUES ('2026-05-12 00:00:00', '2026-05-12 07:30:00', v_session_id);

    SELECT status INTO v_status FROM match WHERE id = v_match_id;
    RAISE NOTICE 'match status after sleep: %', v_status;

    RAISE NOTICE '=== TEST: insert sensor readings (within game window) ===';
    INSERT INTO light_sensor (time_stamp, lumen, room_id, match_id)
    VALUES ('2026-05-12 10:10:00', 15.50, v_room_id, v_match_id);

    INSERT INTO temperature_sensor (time_stamp, celsius, room_id, match_id)
    VALUES ('2026-05-12 10:10:00', 21, v_room_id, v_match_id);

    INSERT INTO water_sensor (time_stamp, ml, room_id, match_id)
    VALUES ('2026-05-12 10:15:00', 250, v_room_id, v_match_id);

    SELECT status INTO v_status FROM match WHERE id = v_match_id;
    RAISE NOTICE 'match status after 3 sensors (missing co2): %', v_status;

    -- This final sensor insert should trigger completion
    INSERT INTO co2_sensor (time_stamp, ppm, room_id, match_id)
    VALUES ('2026-05-12 10:10:00', 800, v_room_id, v_match_id);

    SELECT status INTO v_status FROM match WHERE id = v_match_id;
    RAISE NOTICE 'match status after all sensors: %', v_status;

    RAISE NOTICE '=== VERIFY: dataset row ===';
    PERFORM 1 FROM dataset WHERE match_id = v_match_id;
    IF FOUND THEN
        RAISE NOTICE 'OK — dataset row exists for match %', v_match_id;
    ELSE
        RAISE NOTICE 'FAIL — no dataset row for match %', v_match_id;
    END IF;

    RAISE NOTICE '=== VERIFY: player_opening_stat ===';
    PERFORM 1 FROM player_opening_stat WHERE player_id = v_player_id AND eco_code = 'B02';
    IF FOUND THEN
        RAISE NOTICE 'OK — opening stat exists for player % eco=B02', v_player_id;
    ELSE
        RAISE NOTICE 'FAIL — no opening stat for player % eco=B02', v_player_id;
    END IF;

    RAISE NOTICE '=== VERIFY: session.game_count ===';
    SELECT game_count INTO v_game_count FROM session WHERE id = v_session_id;
    IF v_game_count = 1 THEN
        RAISE NOTICE 'OK — session % game_count = 1', v_session_id;
    ELSE
        RAISE NOTICE 'FAIL — session % game_count = % (expected 1)', v_session_id, v_game_count;
    END IF;

    RAISE NOTICE '=== ALL CHECKS DONE ===';
END;
$$;

ROLLBACK;
