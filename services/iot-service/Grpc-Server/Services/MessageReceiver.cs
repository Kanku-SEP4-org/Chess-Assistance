using IoTGrpcServer.Contracts;

namespace IoTGrpcServer.Services;

public class MessageReceiver : IMessageReceiver
{
    private readonly IoTStateStore _stateStore;

    public MessageReceiver(IoTStateStore stateStore)
    {
        _stateStore = stateStore;
    }

    public void ReceiveSensorMessage(SensorMessage message)
    {
        _stateStore.Update(message.ArduinoId, message.Value, message.Timestamp, message.Type);
    }
}