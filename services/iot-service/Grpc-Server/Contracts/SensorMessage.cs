namespace IoTGrpcServer.Contracts;

public class SensorMessage
{
    public int ArduinoId { get; set; }
    public float Value { get; set; }
    public string Type { get; set; } = string.Empty;
    public long Timestamp { get; set; }
}