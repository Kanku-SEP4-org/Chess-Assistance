using System.Text;
using System.Text.Json;
using IoTGrpcServer.Contracts;
using IotService;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

var rabbitUrl = Environment.GetEnvironmentVariable("RABBITMQ_URL")
                ?? "amqp://guest:guest@localhost:5672/"; //fallback for running without docker

Uri uri = new Uri(rabbitUrl);

var conFactory = new ConnectionFactory { Uri = uri };

using var connection = await conFactory.CreateConnectionAsync();
using var channel = await connection.CreateChannelAsync();

// Declare both queues
await channel.QueueDeclareAsync("sensor.responses", true, false, false, null);
await channel.QueueDeclareAsync("sensor.requests", true, false, false, null);

// Consumer to "Listen" for commands (like fillCup)
//since commands are sent to the sensor.requests queue, the consumer will only react to
//active commands, like fillcup and, future openWindow
var consumer = new AsyncEventingBasicConsumer(channel);
consumer.ReceivedAsync += async (model, ea) =>
{
    var body = ea.Body.ToArray();
    var message = JsonSerializer.Deserialize<JsonElement>(body); // Flexible read

    Console.WriteLine($"\n[ACTUATOR] Received Command: {message}");

    await channel.BasicAckAsync(ea.DeliveryTag, false);
};

await channel.BasicConsumeAsync("sensor.requests", false, consumer);


//for the sensors we keep this
Random rnd = new Random();
sensorType[] types = { sensorType.Temp, sensorType.Light, sensorType.Water }; // Add new types here

for (int i = 0; i < 20; i++)
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

    await Task.Delay(5000); //making it wait a bit longer
}