using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Protos;
using LichessApiService.Grpc.Services;
using Npgsql;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

var dataSource = new NpgsqlDataSourceBuilder(
        builder.Configuration.GetConnectionString("DefaultConnection"))
    .MapEnum<SessionStatus>("session_status")
    .MapEnum<TimeControlType>("time_control_type")
    .MapEnum<GameResultType>("game_result_type")
    .Build();

builder.Services.AddDbContext<LichessDbContext>(options =>
    options.UseNpgsql(dataSource));

builder.Services.AddGrpc();

var iotHost = builder.Configuration["IoT:GrpcHost"] ?? "localhost";
var iotPort = builder.Configuration["IoT:GrpcPort"] ?? "8080";
builder.Services.AddGrpcClient<SensorFeedService.SensorFeedServiceClient>(o =>
    o.Address = new Uri($"http://{iotHost}:{iotPort}"));

builder.Services.AddHttpClient("Lichess", client =>
{
    client.BaseAddress = new Uri("https://lichess.org");
    client.Timeout = TimeSpan.FromMinutes(30);
});

builder.Services.AddScoped<LichessApiClient>();
builder.Services.AddScoped<LichessGameFetcher>();
builder.Services.AddSingleton<LichessStreamService>();

var app = builder.Build();

app.MapGrpcService<LichessApiGrpcService>();
app.MapGet("/", () => "LichessApiService gRPC server is running.");

app.Run();
