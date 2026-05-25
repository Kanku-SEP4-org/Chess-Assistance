SET search_path TO chess_assistant;

ALTER TABLE game ALTER COLUMN lichess_game_id TYPE VARCHAR(16);