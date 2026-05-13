namespace Grpc_Server.Messaging;

public interface IMessageQueue
{   
    Task EnqueueAsync(byte[] bytes);
    Task EnqueueObjectAsync(object message);

}
