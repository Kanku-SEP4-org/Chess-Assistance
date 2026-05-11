using IoTGrpcServer.Contracts;

namespace IoTGrpcServer.Services;

public class MessageReceiver : IMessageReceiver
{
    private readonly SensorStateStores _sensorStateStores;

    public MessageReceiver(SensorStateStores sensorStateStores)
    {
        _sensorStateStores = sensorStateStores;
    }

    public void ReceiveSensorMessage(SensorMessage message)
    {
        var store = _sensorStateStores.GetStore(message.Type);
        store.Update(message.Value, message.Timestamp, message.Type);
    }
}