@startuml ActivityDiagram_ViewDashboard

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
:User is logged in;
:User navigates to Dashboard;

|User / Frontend|
:Start polling timer\n(every 10 seconds);

repeat

  |User / Frontend|
  :Send GET /iot/temp?id=1\nSend GET /iot/light?id=1\nSend GET /iot/co2?id=1;

  |API Gateway|
  :Receive HTTP requests;
  :Call gRPC getTemperature()\nCall gRPC getLight()\nCall gRPC getCO2();

  |IoT Service|
  :Look up latest values\nin in-memory state store;

  if (Data available?) then (yes)
    :Return sensorReadings\n(value, type, timestamp);
  else (no)
    :Return value=0\nsuccess=false;
  endif

  |API Gateway|
  :Transform gRPC responses\nto REST JSON;
  :Return JSON responses\nto frontend;

  |User / Frontend|
  if (Requests successful?) then (yes)
    :Display sensor data\n(temperature, light, CO2)\nand chess games data;

    if (Alerts active?) then (yes)
      :Display alerts\n(CO2 warning, sleep alert,\nwater intake warning);
    else (no)
      :Display\n"All conditions normal";
    endif

  else (no)
    :Display error message\n"Failed to load data";
  endif

  :User reviews the information;
  :Wait 10 seconds;

repeat while (User stays on dashboard?) is (yes)
-> no;

|User / Frontend|
:User navigates away\nor closes application;

stop

@enduml
