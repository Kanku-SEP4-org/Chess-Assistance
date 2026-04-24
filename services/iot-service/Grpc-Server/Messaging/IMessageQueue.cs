using System;
using RabbitMQ.Client;

namespace Grpc_Server.Messaging;

public interface IMessageQueue
{
    public Task EnqueueAsync(byte[] bytes);
    public Task EnqueueObjectAsync(Object message);
    public Task<byte[]> DequeueAsync();
    public Task<object> DequeueObjectAsync();
}
