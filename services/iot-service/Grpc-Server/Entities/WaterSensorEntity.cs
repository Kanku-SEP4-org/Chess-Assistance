using System.Text.RegularExpressions;

namespace IoTGrpcServer;

public class WaterSensorEntity
{
    public int Id {get; set;}

    public DateTime TimeStamp {get; set;}

    public int Ml {get; set;}

    public Room Room {get; set;}
    public int RoomId {get; set;}

    public Match Match {get; set;}
    public int MatchId {get; set;}
}