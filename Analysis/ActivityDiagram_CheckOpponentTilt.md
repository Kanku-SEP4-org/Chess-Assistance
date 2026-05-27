@startuml ActivityDiagram_CheckOpponentTilt

skinparam linetype ortho
skinparam defaultTextAlignment center
skinparam shadowing false
skinparam roundCorner 4

skinparam ranksep 40
skinparam nodesep 40
skinparam padding 10
skinparam dpi 180

skinparam defaultFontName "Helvetica"
skinparam defaultFontSize 11

skinparam ArrowColor #333333
skinparam ArrowThickness 1.2
skinparam ArrowFontColor #444444
skinparam ArrowFontSize 10
skinparam ArrowFontStyle italic

skinparam ActivityBorderColor #333333
skinparam ActivityBackgroundColor #FFFFFF
skinparam ActivityFontName "Helvetica"
skinparam ActivityFontSize 11
skinparam ActivityFontColor #111111
skinparam ActivityBorderThickness 1.2

skinparam ActivityDiamondBorderColor #333333
skinparam ActivityDiamondBackgroundColor #FFFFFF
skinparam ActivityDiamondFontName "Helvetica"
skinparam ActivityDiamondFontSize 10

skinparam PartitionBorderColor #5B8DB8
skinparam PartitionFontName "Helvetica"
skinparam PartitionFontSize 12
skinparam PartitionFontStyle bold
skinparam PartitionBackgroundColor #F8FBFF

|User / Frontend|
start
:User navigates to\nAngriness Predictor page;

:User enters opponent's\nLichess username;

|API Gateway|
:Fetch opponent's recent games\nfrom Lichess API;

if (Player found?) then (yes)
  :Return list of\nrecent games;
else (no)
  |User / Frontend|
  :Display error\n"Username not found on Lichess";
  stop
endif

|User / Frontend|
:Display list of\nopponent's recent games;
:User selects a game\nand clicks "Predict";

|API Gateway|
:Fetch detailed game data\nfrom Lichess;

if (Game has computer analysis?) then (yes)

  |ML Service|
  :Extract behavioral features\n(blunders, mistakes, inaccuracies,\nACPL, accuracy, avg time per move,\nconsecutive losses, ELO);
  :Run Angriness/Tilt\nprediction model;
  :Return predicted\nangriness level (1–5);

  |User / Frontend|
  :Display predicted tilt level\nwith visual scale (1–5)\nand game context;
  note right
    1 = Very Calm
    5 = Very Tilted
  end note

else (no)
  |User / Frontend|
  :Display message\n"Game not computer-analyzed"\nwith link to request\nanalysis on Lichess;
endif

stop

@enduml
