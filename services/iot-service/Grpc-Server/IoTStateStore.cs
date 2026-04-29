namespace IoTGrpcServer;

public class IoTStateStore
{
    private readonly object _lock = new();

    public float LatestValue { get; private set; }
    public string LatestType { get; private set; } = string.Empty;
    public long LatestTimestamp { get; private set; }
    public bool HasValue { get; private set; }

    public void Update(float value, long timestamp, string type)
    {
        lock (_lock)
        {
            LatestValue = value;
            LatestTimestamp = timestamp;
            LatestType = type;
            HasValue = true;
        }
    }

    public (bool HasValue, float Value, long Timestamp, string Type) GetLatest()
    {
        lock (_lock)
        {
            return (HasValue, LatestValue, LatestTimestamp, LatestType);
        }
    }
}