using System.Text;
using System.Text.Json;
using IoTGrpcServer.Contracts;
using IotService;
using RabbitMQ.Client;

var rabbitUrl = Environment.GetEnvironmentVariable("RABBITMQ_URL")
                ?? "amqp://guest:guest@localhost:5672/"; //fallback for running without docker

Uri uri = new Uri(rabbitUrl);

var conFactory = new ConnectionFactory { Uri = uri };

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
sensorType[] types = { sensorType.Temp, sensorType.Light, sensorType.Water }; // Add new types here

for (int i = 0; i < 15; i++)
{
    var selectedType = types[rnd.Next(types.Length)]; // Randomly pick a type
    var sensor = new SensorMessage
    {
        ArduinoId = rnd.Next(1, 5),
        Value = (selectedType == sensorType.Water) ? rnd.Next(0, 101) : rnd.Next(0, 256),
        Type = selectedType,
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