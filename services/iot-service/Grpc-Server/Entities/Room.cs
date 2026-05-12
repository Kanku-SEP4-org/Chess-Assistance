namespace IoTGrpcServer;

public class Room
{
    public int Id {get; set;}

    public int PlayerId {get; set;}

    public int Perimeter {get; set;}
    ICollection<CO2SensorEntity> CO2s {get; set;} = new List<CO2SensorEntity>();
    ICollection<LightSensorEntity> Lights {get; set;} = new List<LightSensorEntity>();
    ICollection<TemperatureSensorEntity> Temperatures {get; set;} = new List<TemperatureSensorEntity>();
    ICollection<WaterSensorEntity> Waters {get; set;} = new List<WaterSensorEntity>();
}