using System.Text;
using System.Text.Json;
using IoTGrpcServer.Contracts;
using RabbitMQ.Client;

var conFactory = new ConnectionFactory { HostName = "localhost" };

using var connection = await conFactory.CreateConnectionAsync();
using var channel = await connection.CreateChannelAsync();

await channel.QueueDeclareAsync(
    queue: "sensor.responses", //queue name
    durable: true, //if false, messages dont persist through server restart
    exclusive: false, //whether queue is exclusive to this connection
    autoDelete: false, //if true, deletes queue if no subcribers exist
    arguments: null
);

Random rnd = new Random();


for (int i = 0; i < 10; i++)
{
    var sensor = new SensorMessage
    {
        ArduinoId = rnd.Next(1, 5),
        Value = rnd.Next(0, 256),
        Type = "temp",
        Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
    };

    byte[] body = JsonSerializer.SerializeToUtf8Bytes(sensor);

    await channel.BasicPublishAsync(
        exchange: string.Empty,
        routingKey: "sensor.responses",
        mandatory: true,
        basicProperties: new BasicProperties { Persistent = true },
        body: body
    );

    Console.WriteLine($"Sent: {JsonSerializer.Serialize(sensor)}");

    await Task.Delay(2000);
}