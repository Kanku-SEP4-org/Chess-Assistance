CREATE SCHEMA chess_assistant;
SET search_path TO chess_assistant;

-- Enums
CREATE TYPE time_control_type AS ENUM ('bullet', 'blitz', 'rapid', 'classical');
CREATE TYPE game_result_type  AS ENUM ('win', 'loss', 'draw');

CREATE TABLE player (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL
);

CREATE TABLE room (
    id        SERIAL PRIMARY KEY,
    perimeter NUMERIC(10,2),
    player_id INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

-- "session" replaces the old "play_block" table
CREATE TABLE session (
    id             SERIAL PRIMARY KEY,
    started_at     TIMESTAMP NOT NULL,
    ended_at       TIMESTAMP,
    total_duration INTERVAL GENERATED ALWAYS AS (ended_at - started_at) STORED,
    game_count     INTEGER DEFAULT 0,
    total_water_ml INTEGER DEFAULT 0,
    player_id      INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE UNIQUE INDEX uq_one_active_session
ON session (player_id)
WHERE ended_at IS NULL;

CREATE TABLE player_preference (
    id                        SERIAL PRIMARY KEY,
    daily_game_limit          INTEGER,
    daily_play_time_limit_min INTEGER,
    break_interval_limit      INTEGER,
    recommend_rest_min        INTEGER,
    player_id                 INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

-- "match" replaces the old "session" table
CREATE TABLE match (
    id                       SERIAL PRIMARY KEY,
    match_date               DATE NOT NULL,
    duration_from_prev_match INTERVAL,
    session_id               INTEGER NOT NULL,
    player_id                INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(id),
    FOREIGN KEY (player_id)  REFERENCES player(id)
);

CREATE TABLE sensor (
    id         SERIAL PRIMARY KEY,
    room_id    INTEGER NOT NULL,
    type       VARCHAR(20) NOT NULL,
    value      DOUBLE PRECISION NOT NULL,
    time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES room(id)
);

CREATE INDEX idx_sensor_room_timestamp ON sensor (room_id, time_stamp);

CREATE TABLE game (
    id                    SERIAL PRIMARY KEY,
    lichess_game_id       VARCHAR(8),
    time_control          time_control_type NOT NULL,
    is_time_increase      BOOLEAN,
    time_increase_sec     INTEGER,
    is_rated              BOOLEAN,
    is_berserk            BOOLEAN,
    source                VARCHAR(50),
    eco_code              VARCHAR(3),
    opening_name          VARCHAR(100),
    total_ply             INTEGER,
    opening_ply           INTEGER,
    player_move_count     INTEGER,
    opponent_move_count   INTEGER,
    user_rating           INTEGER,
    opp_rating            INTEGER,
    rating_diff           INTEGER,
    is_player_piece_black BOOLEAN,
    result                game_result_type NOT NULL,
    termination_type      VARCHAR(50),
    started_at            TIMESTAMP,
    ended_at              TIMESTAMP,
    duration_min          INTEGER,
    match_id              INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (match_id) REFERENCES match(id)
);

CREATE TABLE sleep_record (
    id              SERIAL PRIMARY KEY,
    sleep_time      TIMESTAMP NOT NULL,
    awaken_time     TIMESTAMP NOT NULL,
    sleep_duration  INTERVAL GENERATED ALWAYS AS (awaken_time - sleep_time) STORED,
    confirmed_at    TIMESTAMP NOT NULL,
    awake_duration  INTERVAL GENERATED ALWAYS AS (confirmed_at - awaken_time) STORED,
    water_intake_ml INTEGER,
    record_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id      INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (session_id) REFERENCES session(id),
    CONSTRAINT chk_sleep_order CHECK (awaken_time > sleep_time),
    CONSTRAINT chk_awake_order CHECK (confirmed_at > awaken_time)
);

CREATE TABLE player_opening_stat (
    id             SERIAL PRIMARY KEY,
    player_id      INTEGER NOT NULL,
    eco_code       VARCHAR(3) NOT NULL,
    opening_name   VARCHAR(100),
    player_as_white INTEGER DEFAULT 0,
    player_as_black INTEGER DEFAULT 0,
    player_wins    INTEGER DEFAULT 0,
    player_losses  INTEGER DEFAULT 0,
    player_draws   INTEGER DEFAULT 0,
    opp_as_white   INTEGER DEFAULT 0,
    opp_as_black   INTEGER DEFAULT 0,
    opp_wins       INTEGER DEFAULT 0,
    opp_losses     INTEGER DEFAULT 0,
    total_games    INTEGER GENERATED ALWAYS AS (player_as_white + player_as_black) STORED,
    FOREIGN KEY (player_id) REFERENCES player(id),
    CONSTRAINT uq_player_opening UNIQUE (player_id, eco_code)
);

CREATE TABLE dataset (
    id                         SERIAL PRIMARY KEY,
    match_id                   INTEGER NOT NULL UNIQUE,
    avg_lux                    NUMERIC(6,2),
    avg_celsius                NUMERIC(6,2),
    avg_ppm                    NUMERIC(6,2),
    water_intake_ml            INTEGER,
    sleep_duration             INTERVAL,
    awake_duration             INTERVAL,
    eco_code                   VARCHAR(3),
    opening_name               VARCHAR(100),
    is_rated                   BOOLEAN,
    total_ply                  INTEGER,
    opening_ply                INTEGER,
    player_move_count          INTEGER,
    opponent_move_count        INTEGER,
    time_control               time_control_type,
    is_time_increase           BOOLEAN,
    time_increase_sec          INTEGER,
    is_berserk                 BOOLEAN,
    duration_min               INTEGER,
    user_rating                INTEGER,
    opp_rating                 INTEGER,
    rating_diff                INTEGER,
    is_player_piece_black      BOOLEAN,
    termination_type           VARCHAR(50),
    result                     game_result_type,
    player_opening_win_rate    NUMERIC(5,2),
    player_opening_game_count  INTEGER,
    FOREIGN KEY (match_id) REFERENCES match(id)
);
