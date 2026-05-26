@startuml EER

skinparam linetype ortho
skinparam defaultTextAlignment center
skinparam shadowing false
skinparam roundCorner 0

skinparam ranksep 130
skinparam nodesep 160
skinparam minClassWidth 180
skinparam padding 12
skinparam dpi 180

skinparam defaultFontName "Helvetica"
skinparam defaultFontSize 11

skinparam ArrowColor #333333
skinparam ArrowThickness 1.2
skinparam ArrowFontColor #333333
skinparam ArrowFontSize 10

skinparam classAttributeIconSize 0

skinparam entity {
  BackgroundColor #FFFFFF
  BorderColor #333333
  FontColor #111111
  FontSize 12
  FontStyle bold
  HeaderBackgroundColor #FFFFFF
  AttributeFontColor #333333
  AttributeFontSize 10
  BorderThickness 1.2
}

' ── Entities ──────────────────────────────────────────────────────────

entity "player" as player {
  <u>id</u>
  --
  lichess_id
  username
}

entity "health_record" as health_record {
  <u>id</u>
  --
  sleep_time
  awaken_time
  sleep_duration
  confirmed_at
  awake_duration
  water_intake_ml
}

entity "player_preference" as player_preference {
  <u>id</u>
  --
  daily_game_limit
  daily_play_time_limit_min
  break_interval_limit
  recommend_rest_min
}

entity "player_opening_stat" as player_opening_stat {
  <u>id</u>
  --
  eco_code
  opening_name
  player_as_white
  player_as_black
  player_wins
  player_losses
  player_draws
  opp_as_white
  opp_as_black
  opp_wins
  opp_losses
  total_games
}

entity "room" as room {
  <u>id</u>
  --
  perimeter
}

entity "sensor" as sensor {
  <u>id</u>
  --
  type
  value
  time_stamp
}

entity "session" as session {
  <u>id</u>
  --
  started_at
  ended_at
  total_duration
  total_water_ml
  game_count
}

entity "match" as match_t {
  <u>id</u>
  --
  match_date
  duration_from_prev_match
}

entity "game" as game {
  <u>id</u>
  --
  lichess_game_id
  time_control
  is_time_increase
  time_increase_sec
  is_rated
  is_berserk
  source
  eco_code
  opening_name
  total_ply
  opening_ply
  player_move_count
  opponent_move_count
  user_rating
  opp_rating
  rating_diff
  is_player_piece_black
  result
  termination_type
  started_at
  ended_at
  duration_min
}

entity "game_analysis" as game_analysis {
  <u>id</u>
  --
  inaccuracy_cnt
  mistake_cnt
  blunder_cnt
  acpl
  accuracy
}

entity "dataset" as dataset {
  <u>id</u>
  --
  avg_lux
  avg_celsius
  avg_ppm
  water_intake_ml
  sleep_duration
  awake_duration
  eco_code
  opening_name
  is_rated
  total_ply
  opening_ply
  player_move_count
  opponent_move_count
  time_control
  is_time_increase
  time_increase_sec
  is_berserk
  duration_min
  user_rating
  opp_rating
  rating_diff
  is_player_piece_black
  termination_type
  result
  player_opening_win_rate
  player_opening_game_count
  inaccuracy_cnt
  mistake_cnt
  blunder_cnt
  acpl
  accuracy
  consecutive_losses_pregame
  avg_tpm_seconds
}

' ── Layout Skeleton ───────────────────────────────────────────────────
player_opening_stat  -[hidden]-> player
player               -[hidden]-> session
session              -[hidden]-> match_t
match_t              -[hidden]-> game
game                 -[hidden]-> game_analysis
player               -[hidden]-> health_record
health_record        -[hidden]-> player_preference
player               -[hidden]-> room
room                 -[hidden]-> sensor
match_t              -[hidden]-> dataset

' ── Relationships ─────────────────────────────────────────────────────
player         "1"    -->  "0..*"  player_opening_stat  : tracks >
player         "1"    -->  "0..*"  session              : has >
player         "1"    -->  "0..*"  health_record        : has >
player         "1"    -->  "0..1"  player_preference    : has >
player         "1"    -->  "0..1"  room                 : owns >

health_record  "1"    -->  "0..*"  session              : linked to >

session        "1"    -->  "0..*"  match_t              : contains >

match_t        "1"    -->  "1"     game                 : has >
match_t        "1"    -->  "0..1"  dataset              : produces >

game           "1"    -->  "0..1"  game_analysis        : analysed by >

room           "1"    -->  "0..*"  sensor               : contains >

@enduml
