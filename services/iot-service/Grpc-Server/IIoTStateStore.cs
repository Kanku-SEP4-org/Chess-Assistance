using IoTGrpcServer.Contracts;

namespace IoTGrpcServer;

public interface IIoTStateStore
{
    void Update(int arduinoId, float value, long timestamp, string type);
    void Record(int arduinoId, bool isRecording);
    SensorState? GetLatest(int arduinoId, string type);
}