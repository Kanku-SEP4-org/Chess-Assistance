using IoTGrpcServer.Contracts;

namespace IoTGrpcServer.Services;

public class MessageReceiver : IMessageReceiver
{
    private readonly IIoTStateStore _temperatureStateStore;
    private readonly IIoTStateStore _lightStateStore;

    public MessageReceiver(IIoTStateStore temperatureStateStore,IIoTStateStore lightStateStore )
    {
        _temperatureStateStore = temperatureStateStore;
        _lightStateStore = lightStateStore;
    }

    public void ReceiveSensorMessage(SensorMessage message)
    {
        _temperatureStateStore.Update(message.Value, message.Timestamp, message.Type);
        _lightStateStore.Update(message.Value, message.Timestamp, message.Type);
    }
}