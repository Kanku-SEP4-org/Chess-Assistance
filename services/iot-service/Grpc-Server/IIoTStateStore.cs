namespace IoTGrpcServer;

public interface IIoTStateStore
{
    void Update(float value, long timestamp, string type);
    (bool HasValue, float Value, long Timestamp, string Type)GetLatest();
}