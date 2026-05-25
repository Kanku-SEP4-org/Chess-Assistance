@startuml ActivityDiagram_ViewTemperature

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
:User opens IoT Dashboard;

|User / Frontend|
:Start polling timer\n(every 10 seconds);

repeat

  |User / Frontend|
  :Send GET /iot/temp?id=1;

  |API Gateway|
  :Receive HTTP request;
  :Call gRPC getTemperature(arduinoId=1);

  |IoT Service|
  :Look up latest value\nin in-memory state store;

  if (Data available in state store?) then (yes)
    :Return sensorReading\n(value, type, timestamp);
  else (no)
    :Return value=0\nsuccess=false;
  endif

  |API Gateway|
  :Transform gRPC response\nto REST JSON;
  :Return JSON response\nto frontend;

  |User / Frontend|
  if (Request successful?) then (yes)
    :Calculate comfort status\n< 18°C → Cool\n18–26°C → Comfortable\n> 26°C → Warm;
    :Display temperature value\nand comfort status;
  else (no)
    :Display N/A;
  endif

  :Wait 10 seconds;

repeat while (User stays on dashboard?) is (yes)
-> no;

|User / Frontend|
if (User navigates to\nEnvironment Recommendation?) then (yes)

  :Pre-fill temperature field\nwith latest sensor value;
  :User adjusts sleep / awake\nminutes and submits;

  |ML Service|
  :Receive POST /recommend-environment\n(temperature, co2, light,\nminutes_slept, minutes_awake);
  :Calculate current win probability;
  :Test optimal temperature (20°C)\nand calculate improvement;
  :Return recommendation\n(current value, target 20°C,\nwin probability delta);

  |User / Frontend|
  :Display recommendation\nand probability improvement;

else (no)
endif

stop

@enduml
