using System.Text.RegularExpressions;

namespace IoTGrpcServer;

public class Sensor
{
    public int Id {get; set;}

    public DateTime TimeStamp {get; set;}

    public float Value {get; set;}
    public int RoomId {get;set;}

    public Room Room {get; set;}

    public String Type {get; set;}
}