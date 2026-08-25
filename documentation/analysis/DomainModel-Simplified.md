@startuml DomainModel-Simplified

' ─────────────────────────────────────────────────────────────────────
' Simplified CONCEPTUAL domain model (analysis-level).
' Deliberately NOT a mirror of the database / EER (scripts/databases/init.sql).
'
' Merged / omitted vs. the original DomainModel.md:
'   • GameAnalysis  → merged into Game (it was a 1:1 normalization table —
'                     conceptually just a game's quality metrics).
'   • Match         → merged into Game (Match was 1:1 with Game in the EER).
'   • Dataset       → omitted (a denormalized ML feature/training table; a
'                     derived snapshot of data already modelled here).
'   • PlayerOpeningStat → omitted (a derived per-opening aggregate, not a
'                     domain concept; computable from Games).
'
' Relationships use PLAIN associations (no navigability arrowheads, no
' dependency arrows to enums). Navigability/dependency are design concerns,
' not domain facts. Enums are value types, referenced via attribute typing.
' ─────────────────────────────────────────────────────────────────────

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

' Game now carries the play facts (was Match) AND the quality metrics
' (was GameAnalysis).
class Game {
  lichessGameId
  playedAt
  timeControl : TimeControlType
  result : GameResultType
  isRated
  userRating
  oppRating
  openingName
  ecoCode
  accuracy
  acpl
  blunderCount
  mistakeCount
  inaccuracyCount
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
  type : SensorType
  value
  timestamp
}

' ── Enums (value types — referenced via attribute typing, no arrows) ───

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

' ── Layout Skeleton (hidden edges — invisible, no arrows rendered) ─────
' Main vertical spine
Player        -[hidden]-> Session
Session       -[hidden]-> Game

' Health & preference column (right of Player)
Player        -[hidden]-> HealthRecord
HealthRecord  -[hidden]-> PlayerPreference

' IoT column (far right)
Player        -[hidden]-> Room
Room          -[hidden]-> Sensor

' Enums anchored beside the class that uses them
Game          -[hidden]-> TimeControlType
Game          -[hidden]-> GameResultType
Sensor        -[hidden]-> SensorType

' ── Associations (plain lines, no navigability arrowheads) ────────────
Player   "1"    --  "0..*"  Session           : has >
Player   "1"    --  "0..*"  HealthRecord      : logs >
Player   "1"    --  "0..1"  PlayerPreference  : configures >
Player   "1"    --  "0..1"  Room              : owns >

Session  "1"    --  "1..*"  Game              : contains >
' A play session is tied to that day's health state — the product's core
' "correlate condition with performance" idea.
Session  "0..*" --  "1"     HealthRecord      : linked to >

Room     "1"    --  "0..*"  Sensor            : contains >

@enduml
