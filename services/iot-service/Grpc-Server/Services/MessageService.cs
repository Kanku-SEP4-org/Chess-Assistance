using System;
using System.Text.Json;
using Grpc_Server.Contracts;
using Grpc_Server.Messaging;
using IoTGrpcServer.Contracts;
using IotService;
using RabbitMQ.Client;

namespace Grpc_Server.Services;

public class MessageService : IMessageQueue
{
    private readonly IMessageReceiver _messageReceiver;

    private readonly IChannel _reqChannel;
    private readonly IChannel _resChannel;

    private string reqQueue {get; set;}
    private string resQueue {get; set;}

    public MessageService(IMessageReceiver messageReceiver, ReqChannel reqChannel, ResChannel resChannel)
    {
        _messageReceiver = messageReceiver;
        _reqChannel = reqChannel.Channel;
        _resChannel = resChannel.Channel;
        reqQueue = "sensor.requests";
        resQueue = "sensor.responses";
    }

    public async Task<byte[]> DequeueAsync()
    {
        // Gets 1 message only
        var result = await _resChannel.BasicGetAsync(queue: resQueue, autoAck: false);
        if(result == null)
        {
            return null;
        }

        byte[] body = result.Body.ToArray();

        try
        {
            // Try to ACK message
            await _resChannel.BasicAckAsync(result.DeliveryTag, multiple: false);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to Ack message: {ex.Message}");
            try { await _resChannel.BasicNackAsync(result.DeliveryTag, multiple: false, requeue: true); } catch { }
            throw;
        }

        return body;
    }

    public async Task<object> DequeueObjectAsync()
    {
        var bytes = await DequeueAsync();
        if (bytes == null) return null;

        try
        {
            // TODO: Move casting to Sensor Message somewhere else
            var obj = JsonSerializer.Deserialize<SensorMessage>(bytes, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            Console.WriteLine(JsonSerializer.Serialize(obj));
            _messageReceiver.ReceiveSensorMessage(obj);
            return obj;
        }
        catch (JsonException)
        {
            return bytes;
        }
    }

    public async Task EnqueueAsync(byte[] bytes)
    {
        await _reqChannel.BasicPublishAsync(
            exchange: string.Empty,
            routingKey: reqQueue, 
            mandatory: true,
            basicProperties: new BasicProperties { Persistent = true },
            body: bytes
        );

        Console.WriteLine($"Sent { bytes }");
    }

    public async Task EnqueueObjectAsync(object message)
    {
        byte[] body = JsonSerializer.SerializeToUtf8Bytes(message);
        await EnqueueAsync(body);
    }
}
