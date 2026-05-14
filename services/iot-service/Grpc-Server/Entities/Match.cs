using Microsoft.VisualBasic;

namespace IoTGrpcServer;

public class Match
{
    public int Id {get; set;}

    public DateOnly SessionDate {get; set;}

    public DateInterval DurationFromPrevious {get; set;}

    public Enum Status {get; set;}
    
    public int SessionId {get; set;}

    public int PlayerId {get; set;}

    public int Perimeter {get; set;}
    public ICollection<CO2Sensor> CO2Sensors {get; set;} = new List<CO2Sensor>();
    public ICollection<LightSensor> LightSensors {get; set;} = new List<LightSensor>();
    public ICollection<TemperatureSensor> TemperatureSensors {get; set;} = new List<TemperatureSensor>();
    public ICollection<WaterSensor> WaterSensors {get; set;} = new List<WaterSensor>();
}