namespace IoTGrpcServer.Contracts;

public interface IMessageReceiver
{
    void ReceiveSensorMessage(SensorMessage message);
}