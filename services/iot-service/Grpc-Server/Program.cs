using Grpc_Server.Messaging;
using Grpc_Server.Services;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using IoTGrpcServer.Services;
using RabbitMQ.Client;
using Grpc_Server.Contracts;

var builder = WebApplication.CreateBuilder(args);

// RabbitMQ settings
var rabbitHost = "localhost";
var rabbitUser = "guest";
var rabbitPass = "guest";
var requestQueue = "sensor.requests";
var responseQueue = "sensor.responses";

builder.Services.AddGrpc();

builder.Services.AddSingleton<IoTStateStore>();
builder.Services.AddSingleton<IMessageReceiver, MessageReceiver>();
builder.Services.AddScoped<IMessageQueue, MessageService>();

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
    ch.QueueDeclareAsync(queue: requestQueue, durable: true, exclusive: false, autoDelete: false, arguments: null).GetAwaiter().GetResult();
    return new ReqChannel(ch);
});
builder.Services.AddSingleton<ResChannel>(sp =>
{
    var conn = sp.GetRequiredService<IConnection>();
    var ch = conn.CreateChannelAsync().GetAwaiter().GetResult();
    ch.QueueDeclareAsync(queue: responseQueue, durable: true, exclusive: false, autoDelete: false, arguments: null);
    return new ResChannel(ch);
});

// Register IMessageQueue using the typed channels
builder.Services.AddSingleton<IMessageQueue>(sp =>
{
    var receiver = sp.GetRequiredService<IMessageReceiver>();
    var req = sp.GetRequiredService<ReqChannel>();
    var res = sp.GetRequiredService<ResChannel>();
    return new MessageService(receiver, req, res);
});

var app = builder.Build();

app.MapGrpcService<IoTServiceImpl>();
app.MapGet("/", () => "IoT gRPC server is running.");

app.Run();
