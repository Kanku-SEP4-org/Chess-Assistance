namespace IoTGrpcServer;

public class IoTStateStore
{
    private readonly object _lock = new();

    public int LatestTemperature { get; private set; }
    public long LatestTimestamp { get; private set; }
    public bool HasValue { get; private set; }

    public void Update(int value, long timestamp)
    {
        lock (_lock)
        {
            LatestTemperature = value;
            LatestTimestamp = timestamp;
            HasValue = true;
        }
    }

    public (bool HasValue, int Value, long Timestamp) GetLatest()
    {
        lock (_lock)
        {
            return (HasValue, LatestTemperature, LatestTimestamp);
        }
    }
}