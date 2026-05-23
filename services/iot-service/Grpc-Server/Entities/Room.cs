namespace IoTGrpcServer;

public class Room
{
    public int Id {get; set;}

    public int PlayerId {get; set;}

    public int Perimeter {get; set;}
    public ICollection<Sensor> Sensors {get; set;} = new List<Sensor>();
}