using IotService;

namespace IoTGrpcServer.Contracts;

public class SensorState
{
    public int ArduinoId { get; set; }
    public float Value { get; set; }
    public long Timestamp { get; set; }
    public bool Recording { get; set; } = false;
    public sensorType Type { get; set; }
}