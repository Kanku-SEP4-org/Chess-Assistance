namespace IoTGrpcServer.Contracts;

public class SensorState
{
    public int ArduinoId { get; set; }
    public float Value { get; set; }
    public long Timestamp { get; set; }
    public string Type { get; set; } = string.Empty;
<<<<<<< HEAD
    public bool Recording { get; set; } = false;
=======
>>>>>>> 6090698 (fix: cherry-pick unmerged msg queue implementation)
}