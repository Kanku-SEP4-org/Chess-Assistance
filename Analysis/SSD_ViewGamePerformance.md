@startuml
actor User
participant App [
    =App
    ----
    ""Frontend""
]


User->App : view game history
return most recent 10 games
User->App: Predict(per game)
return Actual performance|Predicted performance|Verdict (overperformed/underperformed/normal)

alt no data available
    App --> User : Predict button absent
else Service/API gate unreachable
    loop 10 second interval
    App --> User: retry
    end
end

@enduml