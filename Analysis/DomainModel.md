@startuml DomainModel

skinparam linetype ortho
skinparam defaultTextAlignment center
skinparam shadowing false
skinparam roundCorner 0

skinparam ranksep 200
skinparam nodesep 180
skinparam minClassWidth 150
skinparam padding 12
skinparam dpi 180

skinparam defaultFontName "Helvetica"
skinparam defaultFontSize 12

skinparam ArrowColor #333333
skinparam ArrowThickness 1.2
skinparam ArrowFontColor #333333
skinparam ArrowFontSize 11

skinparam classAttributeIconSize 0

skinparam class {
  BackgroundColor #FFFFFF
  BorderColor #333333
  FontColor #111111
  FontSize 12
  FontStyle bold
  HeaderBackgroundColor #FFFFFF
  AttributeFontColor #333333
  AttributeFontSize 11
  AttributeFontStyle normal
  BorderThickness 1.2
}

skinparam enum {
  BackgroundColor #FFFFFF
  BorderColor #333333
  FontColor #111111
  FontSize 12
  FontStyle bold
  HeaderBackgroundColor #F5F5F5
  BorderThickness 1.2
}

' ── Core Chess Domain ─────────────────────────────────────────────────

class Player {
  lichessId
  username
}

class Session {
  startedAt
  endedAt
  gameCount
  totalWaterMl
}

class Match {
  matchDate
}

class Game {
  lichessGameId
  timeControl
  result
  userRating
  oppRating
  openingName
  ecoCode
  isRated
}

class GameAnalysis {
  accuracy
  acpl
  blunderCount
  mistakeCount
  inaccuracyCount
}

class PlayerOpeningStat {
  ecoCode
  openingName
  totalGames
  wins
  losses
  draws
}

class Dataset {
  avgLux
  avgCelsius
  avgPpm
  waterIntakeMl
  sleepDuration
  result
  accuracy
}

' ── Health & Preferences ──────────────────────────────────────────────

class HealthRecord {
  sleepTime
  awakenTime
  waterIntakeMl
}

class PlayerPreference {
  dailyGameLimit
  dailyPlayTimeLimitMin
  breakIntervalLimit
  recommendRestMin
}

' ── IoT Domain ────────────────────────────────────────────────────────

class Room {
  perimeter
}

class Sensor {
  type
  value
  timestamp
}

' ── Enums ─────────────────────────────────────────────────────────────

enum TimeControlType {
  Bullet
  Blitz
  Rapid
  Classical
}

enum GameResultType {
  Win
  Loss
  Draw
}

enum SensorType {
  Light
  Temperature
  Co2
}

' ── Layout Skeleton ───────────────────────────────────────────────────
' Main vertical spine
Player            -[hidden]-> Session
Player            -[hidden]-> Session
Session           -[hidden]-> Match
Session           -[hidden]-> Match
Match             -[hidden]-> Game
Match             -[hidden]-> Game
Game              -[hidden]-> GameAnalysis
Game              -[hidden]-> GameAnalysis

' Health & preference column (right of Player)
Player            -[hidden]-> HealthRecord
HealthRecord      -[hidden]-> PlayerPreference

' IoT column (far right)
Player            -[hidden]-> Room
Room              -[hidden]-> Sensor

' PlayerOpeningStat (left of Player)
PlayerOpeningStat -[hidden]-> Player

' Enums — anchored at the same depth as Game, not below GameAnalysis
Dataset           -[hidden]-> TimeControlType
Dataset           -[hidden]-> GameResultType
Sensor            -[hidden]-> SensorType

' ── Relationships ─────────────────────────────────────────────────────
Player         "1"    -->  "0..*"  Session            : has >
Player         "1"    -->  "0..*"  HealthRecord       : has >
Player         "1"    -->  "0..1"  PlayerPreference   : has >
Player         "1"    -->  "0..*"  PlayerOpeningStat  : tracks >
Player         "1"    -->  "0..1"  Room               : owns >

Session        "0..*" -->  "1"     HealthRecord       : linked to >
Session        "1"    -->  "1..*"  Match              : contains >

Match          "1"    -->  "1"     Game               : has >
Match          "1"    -->  "0..1"  Dataset            : produces >

Game           "1"    -->  "0..1"  GameAnalysis       : analysed by >
Game                  ..>          TimeControlType    : uses >
Game                  ..>          GameResultType     : uses >

Room           "1"    -->  "0..*"  Sensor             : contains >
Sensor                ..>          SensorType         : typed as >

@enduml
