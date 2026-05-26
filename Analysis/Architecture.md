@startuml SEP4_Architecture

skinparam linetype ortho
skinparam defaultTextAlignment center
skinparam shadowing false
skinparam roundCorner 6

skinparam ranksep 220
skinparam nodesep 200
skinparam minClassWidth 160
skinparam padding 14
skinparam dpi 180

skinparam defaultFontName "Helvetica"
skinparam defaultFontSize 12

skinparam ArrowColor #333333
skinparam ArrowThickness 1.2
skinparam ArrowFontColor #444444
skinparam ArrowFontSize 11
skinparam ArrowFontStyle italic

skinparam rectangle {
  BorderColor #5B8DB8
  BackgroundColor #FFFFFF
  FontColor #111111
  FontSize 12
}
skinparam database {
  BorderColor #5B8DB8
  BackgroundColor #DAE8FC
  FontColor #111111
  FontSize 12
}
skinparam queue {
  BorderColor #D6830D
  BackgroundColor #FFE6B3
  FontColor #111111
  FontSize 12
}

' ── External Client ──────────────────────────────────────────────────
rectangle "**SEP4 Frontend**\n<i>React / JS</i>" as Frontend #FFF2CC

' ── VPS ──────────────────────────────────────────────────────────────
rectangle "VPS" as VPS #F5F5F5 {

  rectangle "**Reverse Proxy**\n<i>Caddy · Ingress</i>" as CaddyTop #DAE8FC

  rectangle "**Backend**" as Backend #FFFFFF {

    rectangle "**API Gateway**\n<i>Express.js · REST / gRPC</i>" as APIGateway #FFF2CC

    rectangle "**IoT + DB**\n<i>.NET · gRPC / RabbitMQ</i>" as IoTDB #FFF2CC

    rectangle "**Lichess API + Stream**\n<i>.NET / gRPC</i>" as Lichess #FFF2CC

    queue "**RabbitMQ Broker**" as RabbitBroker #FFE6B3

    database "**Database**\n<i>PostgreSQL</i>" as DB #DAE8FC

    rectangle "**ML Service**\n<i>Python / FastAPI</i>" as ML #FFF2CC
  }

  rectangle "**Docker Compose**" as Docker #DAE8FC

  rectangle "**Reverse Proxy**\n<i>Caddy · Egress</i>" as CaddyBottom #DAE8FC
}

' ── IoT Edge ─────────────────────────────────────────────────────────
rectangle "**IoT RabbitMQ Producer**" as IoTProducer #FFF2CC
rectangle "**IoT Driver**\n<i>C</i>" as IoTDriver #FFF2CC

' ── Layout Skeleton ──────────────────────────────────────────────────
Frontend     -[hidden]-> CaddyTop
Frontend     -[hidden]-> CaddyTop
CaddyTop     -[hidden]-> APIGateway
CaddyTop     -[hidden]-> APIGateway
APIGateway   -[hidden]-> IoTDB
IoTDB        -[hidden]-> RabbitBroker
RabbitBroker -[hidden]-> CaddyBottom
CaddyBottom  -[hidden]-> IoTProducer
APIGateway   -[hidden]-> Lichess
APIGateway   -[hidden]-> Lichess
Lichess      -[hidden]-> ML
Lichess      -[hidden]-> ML
ML           -[hidden]-> DB
IoTProducer  -[hidden]-> IoTDriver

' ── Connections ──────────────────────────────────────────────────────
Frontend     <-->  CaddyTop      : HTTPS
CaddyTop     <-->  APIGateway    : Proxy
CaddyTop     <-->  ML            : Proxy

APIGateway   -->   IoTDB         : gRPC
APIGateway   <-->  Lichess       : gRPC

IoTDB        -->   RabbitBroker  : Publish
RabbitBroker -->   IoTDB         : Consume

IoTDB        -->   DB            : Read / Write
Lichess      <-->   DB            : Read / Write
ML           -->   DB            : Read


RabbitBroker <-->  CaddyBottom
CaddyBottom  <-->  IoTProducer
IoTProducer  <-->  IoTDriver     : Data

@enduml
