using IoTGrpcServer.Contracts;

namespace IoTGrpcServer.Services;

public class MessageReceiver : IMessageReceiver
{
    private readonly IIoTStateStore _stateStore;

    public MessageReceiver(IIoTStateStore sensorState)
    {
        _stateStore = sensorState;
    }

    public void ReceiveSensorMessage(SensorMessage message)
    {
        _stateStore.Update(message.ArduinoId, message.Value, message.Timestamp, message.Type);
    }
}