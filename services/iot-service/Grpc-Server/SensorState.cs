namespace IoTGrpcServer.Contracts;

public class SensorState
{
    public int ArduinoId { get; set; }
    public float Value { get; set; }
    public long Timestamp { get; set; }
    public string Type { get; set; } = string.Empty;
}