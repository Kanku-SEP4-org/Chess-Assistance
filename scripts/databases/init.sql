CREATE SCHEMA chess_assistant;
SET search_path TO chess_assistant;

-- Enums
CREATE TYPE session_status AS ENUM ('pending', 'complete', 'exported');
CREATE TYPE time_control_type AS ENUM ('bullet', 'blitz', 'rapid', 'classical');
CREATE TYPE game_result_type AS ENUM ('win', 'loss', 'draw');
CREATE DOMAIN STRING AS VARCHAR(255);

CREATE TABLE player (
    id       SERIAL PRIMARY KEY,
    username STRING NOT NULL
);

CREATE TABLE room (
    id        SERIAL PRIMARY KEY,
    perimeter NUMERIC(10,2),
    player_id INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE TABLE play_block (
    id             SERIAL PRIMARY KEY,
    started_at     TIMESTAMP NOT NULL,
    ended_at       TIMESTAMP,
    total_duration INTERVAL GENERATED ALWAYS AS (ended_at - started_at) STORED,
    game_count     INTEGER DEFAULT 0,
    player_id      INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE UNIQUE INDEX uq_one_active_block
ON play_block (player_id)
WHERE ended_at IS NULL;

CREATE TABLE player_preference (
    id                       SERIAL PRIMARY KEY,
    daily_game_limit         INTEGER,
    daily_play_time_limit_min INTEGER,
    break_interval_limit     INTEGER,
    recommend_rest_min       INTEGER,
    player_id                INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE TABLE session (
    id                       SERIAL PRIMARY KEY,
    session_date             DATE NOT NULL,
    status                   session_status NOT NULL DEFAULT 'pending',
    duration_from_prev_session INTERVAL,
    play_block_id            INTEGER NOT NULL,
    player_id                INTEGER NOT NULL,
    FOREIGN KEY (play_block_id) REFERENCES play_block(id),
    FOREIGN KEY (player_id)    REFERENCES player(id),
    CONSTRAINT uq_player_session UNIQUE (player_id, session_date)
);

CREATE TABLE light_sensor (
    id         SERIAL PRIMARY KEY,
    time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lumen      NUMERIC(4,2),
    room_id    INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    FOREIGN KEY (room_id)    REFERENCES room(id),
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE temperature_sensor (
    id         SERIAL PRIMARY KEY,
    time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    celsius    INTEGER,
    room_id    INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    FOREIGN KEY (room_id)    REFERENCES room(id),
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE water_sensor (
    id         SERIAL PRIMARY KEY,
    time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ml         INTEGER,
    room_id    INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    FOREIGN KEY (room_id)    REFERENCES room(id),
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE co2_sensor (
    id         SERIAL PRIMARY KEY,
    time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ppm        INTEGER,
    room_id    INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    FOREIGN KEY (room_id)    REFERENCES room(id),
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE game (
    id                  SERIAL PRIMARY KEY,
    time_control        time_control_type NOT NULL,
    duration_min        INTEGER,
    move_count          INTEGER,
    user_rating         INTEGER,
    opp_rating          INTEGER,
    rating_diff         INTEGER GENERATED ALWAYS AS (user_rating - opp_rating),
    is_player_piece_black BOOLEAN,
    result              game_result_type NOT NULL,
    session_id          INTEGER NOT NULL UNIQUE, -- game -> session is 0..1:1
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE sleep_record (
    id             SERIAL PRIMARY KEY,
    sleep_time     TIMESTAMP NOT NULL,
    awaken_time    TIMESTAMP NOT NULL,
    record_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sleep_duration INTERVAL,
    session_id     INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (session_id) REFERENCES session(id)
);

CREATE TABLE dataset (
    id             SERIAL PRIMARY KEY,
    session_id     INTEGER NOT NULL UNIQUE,
    avg_lumen      NUMERIC(4,2),
    avg_ml         INTEGER,
    avg_celsius    INTEGER,
    avg_ppm        INTEGER,
    sleep_duration INTERVAL,
    time_control   time_control_type,
    duration_min   INTEGER,
    move_count     INTEGER,
    user_rating    INTEGER,
    opp_rating     INTEGER,
    rating_diff    INTEGER,
    result         game_result_type,
    FOREIGN KEY (session_id) REFERENCES session(id)
);