using IoTGrpcServer.Contracts;
using IotService;

namespace IoTGrpcServer;

public interface IIoTStateStore
{
    IEnumerable<SensorState> Record(int arduinoId);
    IEnumerable<SensorState> StopRecord(int arduinoId);
    void Update(int arduinoId, float value, long timestamp, sensorType type);
    SensorState? GetLatest(int arduinoId, sensorType type);
}