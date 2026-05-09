using Grpc_Server.Messaging;


namespace Grpc_Server.Services;

public class RabbitMqConsumerService : BackgroundService
{
    private readonly IMessageQueue _messageQueue;

    public RabbitMqConsumerService(IMessageQueue messageQueue)
    {
        _messageQueue = messageQueue;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await _messageQueue.DequeueObjectAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"RabbitMqConsumerService error: {ex.Message}");
            }

            await Task.Delay(1000, stoppingToken);
        }
    }
}