using System;
using System.Text.Json;
using Grpc_Server.Contracts;
using Grpc_Server.Messaging;
using IoTGrpcServer.Contracts;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace Grpc_Server.Services;

public class MessageService : BackgroundService, IMessageQueue{
    private readonly IMessageReceiver _messageReceiver;

    private readonly IChannel _reqChannel;
    private readonly IChannel _resChannel;

    private readonly string reqQueue;
    private readonly string resQueue;

    public MessageService(IMessageReceiver messageReceiver, ReqChannel reqChannel, ResChannel resChannel)
    {
        _messageReceiver = messageReceiver;
        _reqChannel = reqChannel.Channel;
        _resChannel = resChannel.Channel;
        reqQueue = "sensor.requests";
        resQueue = "sensor.responses";
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var consumer = new AsyncEventingBasicConsumer(_resChannel);

        consumer.ReceivedAsync += async (_, ea) => //This is the event that happens when RabbitMQ delivers a message
        // += means attach/subscribe the handler to the event
        // _,ea - is a lambda expression, basically a short anonymous function which means the handler receives 2 parameters, one ignored and the ea-eventArgs
        {
            try
            {
                var body = ea.Body.ToArray();
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                var obj = JsonSerializer.Deserialize<SensorMessage>(body, options);

                if (obj != null)
                {
                    _messageReceiver.ReceiveSensorMessage(obj);
                    Console.WriteLine($"Consumed: {JsonSerializer.Serialize(obj)}");
                }

                await _resChannel.BasicAckAsync(ea.DeliveryTag, multiple: false);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Message consume error: {ex.Message}");
                await _resChannel.BasicNackAsync(ea.DeliveryTag, multiple: false, requeue: true);
            }
        };

        await _resChannel.BasicConsumeAsync(
            queue: resQueue,
            autoAck: false,
            consumer: consumer,
            cancellationToken: stoppingToken
        );

        await Task.Delay(Timeout.Infinite, stoppingToken);
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
    }

    public async Task EnqueueObjectAsync(object message)
    {
        byte[] body = JsonSerializer.SerializeToUtf8Bytes(message);
        await EnqueueAsync(body);
    }
}
