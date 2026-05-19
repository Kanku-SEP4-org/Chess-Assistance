using IoTGrpcServer.Contracts;
using IotService;

namespace IoTGrpcServer;

public interface IIoTStateStore
{
    void Update(int arduinoId, float value, long timestamp, sensorType type);
    SensorState? GetLatest(int arduinoId, sensorType type);
}