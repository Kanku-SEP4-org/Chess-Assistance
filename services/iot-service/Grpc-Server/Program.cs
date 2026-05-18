using Grpc_Server.Messaging;
using Grpc_Server.Services;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using IoTGrpcServer.Services;
using RabbitMQ.Client;
using Grpc_Server.Contracts;

var builder = WebApplication.CreateBuilder(args);

// RabbitMQ settings
//var rabbitHost = builder.Configuration["RabbitMQ:Host"] ?? "rabbitmq";

// Look for an environment variable named RABBIT_HOST,
// then check appsettings, then default to "localhost" for local dev safety.
var rabbitHost = Environment.GetEnvironmentVariable("RABBIT_HOST")
                 ?? builder.Configuration["RabbitMQ:Host"]
                 ?? "localhost"; // Changed default from "rabbitmq" to "localhost"
//after making sure the rabbitmq server works on http://localhost:15672
//in console: $env:RabbitMQ__Host="localhost"
//then you can build and run without docker
var rabbitUser = builder.Configuration["RabbitMQ:User"] ?? "guest";
var rabbitPass = builder.Configuration["RabbitMQ:Password"] ?? "guest";
var requestQueue = builder.Configuration["RabbitMQ:RequestQueue"] ?? "sensor.requests";
var responseQueue = builder.Configuration["RabbitMQ:ResponseQueue"] ?? "sensor.responses";

builder.Services.AddGrpc();

builder.Services.AddSingleton<IIoTStateStore, IoTStateStore>();
builder.Services.AddSingleton<IMessageReceiver, MessageReceiver>();
builder.Services.AddSingleton(sp => new ConnectionFactory
{
    HostName = rabbitHost,
    UserName = rabbitUser,
    Password = rabbitPass
});

// RabbitMQ uses Async methods, needed to wrap the async calls in this annoying way, should look into fix
builder.Services.AddSingleton<IConnection>(sp =>
{
    var factory = sp.GetRequiredService<ConnectionFactory>();
    return factory.CreateConnectionAsync().GetAwaiter().GetResult();
});

// Register channels
builder.Services.AddSingleton<ReqChannel>(sp =>
{
    var conn = sp.GetRequiredService<IConnection>();
    var ch = conn.CreateChannelAsync().GetAwaiter().GetResult();
    ch.QueueDeclareAsync(
        queue: requestQueue,
        durable: true,
        exclusive: false,
        autoDelete: false,
        arguments: null
    ).GetAwaiter().GetResult();

    return new ReqChannel(ch);
});
builder.Services.AddSingleton<ResChannel>(sp =>
{
    var conn = sp.GetRequiredService<IConnection>();
    var ch = conn.CreateChannelAsync().GetAwaiter().GetResult();
    ch.QueueDeclareAsync(
        queue: responseQueue,
        durable: true,
        exclusive: false,
        autoDelete: false,
        arguments: null
    ).GetAwaiter().GetResult();

    return new ResChannel(ch);
});

builder.Services.AddSingleton<MessageService>(sp =>
{
    var receiver = sp.GetRequiredService<IMessageReceiver>();
    var req = sp.GetRequiredService<ReqChannel>();
    var res = sp.GetRequiredService<ResChannel>();
    return new MessageService(receiver, req, res);
});

builder.Services.AddSingleton<IMessageQueue>(sp =>
    sp.GetRequiredService<MessageService>());

builder.Services.AddHostedService(sp =>
    sp.GetRequiredService<MessageService>());

var app = builder.Build();

app.MapGrpcService<IoTServiceImpl>();
app.MapGet("/", () => "IoT gRPC server is running.");

app.Run();
