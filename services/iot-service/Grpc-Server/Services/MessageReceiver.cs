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
        if (message.Type.ToLower() == "temp")
        {
            _stateStore.Update(message.Value, message.Timestamp);
        }
    }
}