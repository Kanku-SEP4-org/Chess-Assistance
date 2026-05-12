using IoTGrpcServer.Contracts;

namespace IoTGrpcServer;

public interface IIoTStateStore
{
    void Update(int arduinoId, float value, long timestamp, string type);
    SensorState? GetLatest(int arduinoId, string type);
}