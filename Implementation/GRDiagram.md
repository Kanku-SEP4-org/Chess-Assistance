@startuml GRDiagram

skinparam linetype ortho
skinparam defaultTextAlignment center
skinparam shadowing false
skinparam roundCorner 0

skinparam ranksep 130
skinparam nodesep 160
skinparam minClassWidth 220
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
  * <u>id</u> : serial             <<PK>>
  --
  ~ lichess_id : varchar(50)       <<CK>>
  ~ username : varchar(255)        <<CK>>
}

entity "health_record" as health_record {
  * <u>id</u> : serial             <<PK>>
  --
  # player_id : integer            <<FK>>
  ~ confirmed_at : timestamp       <<CK>>
  sleep_time : timestamp
  awaken_time : timestamp
  sleep_duration : interval
  awake_duration : interval
  water_intake_ml : integer
}

entity "player_preference" as player_preference {
  * <u>id</u> : serial             <<PK>>
  --
  # ~ player_id : integer          <<FK>> <<CK>>
  daily_game_limit : integer
  daily_play_time_limit_min : integer
  break_interval_limit : integer
  recommend_rest_min : integer
}

entity "player_opening_stat" as player_opening_stat {
  * <u>id</u> : serial             <<PK>>
  --
  # player_id : integer            <<FK>>
  ~ eco_code : varchar(3)          <<CK>>
  opening_name : varchar(100)
  player_as_white : integer
  player_as_black : integer
  player_wins : integer
  player_losses : integer
  player_draws : integer
  opp_as_white : integer
  opp_as_black : integer
  opp_wins : integer
  opp_losses : integer
  total_games : integer
}

entity "room" as room {
  * <u>id</u> : serial             <<PK>>
  --
  # player_id : integer            <<FK>>
  perimeter : numeric(10,2)
}

entity "sensor" as sensor {
  * <u>id</u> : serial             <<PK>>
  --
  # room_id : integer              <<FK>>
  type : varchar(20)
  value : double precision
  time_stamp : timestamp
}

entity "session" as session {
  * <u>id</u> : serial             <<PK>>
  --
  # player_id : integer            <<FK>>
  # health_record_id : integer     <<FK>>
  started_at : timestamp
  ended_at : timestamp
  total_duration : interval
  total_water_ml : integer
  game_count : integer
}

entity "match" as match_t {
  * <u>id</u> : serial             <<PK>>
  --
  # session_id : integer           <<FK>>
  # player_id : integer            <<FK>>
  match_date : date
  duration_from_prev_match : interval
}

entity "game" as game {
  * <u>id</u> : serial             <<PK>>
  --
  # ~ match_id : integer           <<FK>> <<CK>>
  lichess_game_id : varchar(8)
  time_control : time_control_type
  is_time_increase : boolean
  time_increase_sec : integer
  is_rated : boolean
  is_berserk : boolean
  source : varchar(50)
  eco_code : varchar(3)
  opening_name : varchar(100)
  total_ply : integer
  opening_ply : integer
  player_move_count : integer
  opponent_move_count : integer
  user_rating : integer
  opp_rating : integer
  rating_diff : integer
  is_player_piece_black : boolean
  result : game_result_type
  termination_type : varchar(50)
  started_at : timestamp
  ended_at : timestamp
  duration_min : integer
}

entity "game_analysis" as game_analysis {
  * <u>id</u> : serial             <<PK>>
  --
  # ~ game_id : integer            <<FK>> <<CK>>
  inaccuracy_cnt : integer
  mistake_cnt : integer
  blunder_cnt : integer
  acpl : integer
  accuracy : integer
}

entity "dataset" as dataset {
  * <u>id</u> : serial             <<PK>>
  --
  # ~ match_id : integer           <<FK>> <<CK>>
  avg_lux : numeric(6,2)
  avg_celsius : numeric(6,2)
  avg_ppm : numeric(6,2)
  water_intake_ml : integer
  sleep_duration : interval
  awake_duration : interval
  eco_code : varchar(3)
  opening_name : varchar(100)
  is_rated : boolean
  total_ply : integer
  opening_ply : integer
  player_move_count : integer
  opponent_move_count : integer
  time_control : time_control_type
  is_time_increase : boolean
  time_increase_sec : integer
  is_berserk : boolean
  duration_min : integer
  user_rating : integer
  opp_rating : integer
  rating_diff : integer
  is_player_piece_black : boolean
  termination_type : varchar(50)
  result : game_result_type
  player_opening_win_rate : numeric(5,2)
  player_opening_game_count : integer
  inaccuracy_cnt : integer
  mistake_cnt : integer
  blunder_cnt : integer
  acpl : integer
  accuracy : integer
  consecutive_losses_pregame : integer
  avg_tpm_seconds : numeric(10,6)
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
