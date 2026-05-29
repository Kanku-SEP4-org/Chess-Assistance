@startuml
actor User
participant App [
    =App
    ----
    ""Frontend""
]


User->App : view dashboard

return present temperature values

alt no data available
    App --> User : displays "N/A"
else Service/API gate unreachable
    loop 10 second interval
    App --> User: retry
    end
else Player navigates to Environment Recommendation page
    App --> User : show last recorded temperature
    User -> App : fill sleep and awake duration form and submit
    return recommended temperature and expected win probability improvement
end

@enduml