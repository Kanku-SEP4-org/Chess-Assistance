using IoTGrpcServer.Contracts;

namespace IoTGrpcServer;

public interface IIoTStateStore
{
    void Update(int arduinoId, float value, long timestamp, string type);
    IEnumerable<SensorState> Record(int arduinoId);
    IEnumerable<SensorState> StopRecord(int arduinoId);
    SensorState? GetLatest(int arduinoId, string type);
}