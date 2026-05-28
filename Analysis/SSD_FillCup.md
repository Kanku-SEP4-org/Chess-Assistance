@startuml
actor User
participant Cup
participant App [
    =App
    ----
    ""Frontend+ArduinoBoard""
]


User->App : enable Water Pump

App->Cup: monitor water level
return water level value (500-1000)
App-->User: water level value

alt water level low(500-600)
    App->Cup: FillCup(start pump)
else water level adequate(>600)
    loop 10 second interval
    App --> Cup: monitor water level
    end
else water level data absent (sensor/connection malfunction)
    App --> User : sensor error message
    group user choice
        group Retry
        User->Cup: readjust
        User->App: Try again
        App->Cup: monitor water level
        App-->User: water level value
        end
        group Disable    
        User -> App : disable Water Pump
        return confirm Water Pump disabled
        end
    end
end

@enduml