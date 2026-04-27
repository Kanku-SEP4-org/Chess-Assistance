namespace IoTGrpcServer.Contracts;

public class SensorMessage
{
    public int ArduinoId { get; set; }
    public int Value { get; set; }
    public string Type { get; set; } = string.Empty;
    public long Timestamp { get; set; }
}