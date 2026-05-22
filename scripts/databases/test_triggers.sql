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

    RAISE NOTICE '=== TEST: insert match ===';
    INSERT INTO match (match_date, session_id, player_id)
    VALUES ('2026-05-12', v_session_id, v_player_id)
    RETURNING id INTO v_match_id;

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

    RAISE NOTICE '=== VERIFY: player_opening_stat ===';
    PERFORM 1 FROM player_opening_stat WHERE player_id = v_player_id AND eco_code = 'B02';
    IF FOUND THEN
        RAISE NOTICE 'OK — opening stat exists for player % eco=B02', v_player_id;
    ELSE
        RAISE NOTICE 'FAIL — no opening stat for player % eco=B02', v_player_id;
    END IF;

    RAISE NOTICE '=== ALL CHECKS DONE ===';
END;
$$;

ROLLBACK;
