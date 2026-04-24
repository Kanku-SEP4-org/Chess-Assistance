using Grpc_Server.Services;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using IoTGrpcServer.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddGrpc();
builder.Services.AddSingleton<IoTStateStore>();
builder.Services.AddSingleton<IMessageReceiver, MessageReceiver>();

var app = builder.Build();

app.MapGrpcService<IoTServiceImpl>();

app.MapGet("/", () => "IoT gRPC server is running.");

app.Run();