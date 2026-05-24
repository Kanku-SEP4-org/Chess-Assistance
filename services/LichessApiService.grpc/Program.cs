using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Services;
using Npgsql;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

var dataSource = new NpgsqlDataSourceBuilder(
        builder.Configuration.GetConnectionString("DefaultConnection"))
    // gean: map enums to the schema where init.sql creates them, so Npgsql sends Postgres enum values instead of integers.
    .MapEnum<TimeControlType>("time_control_type")
    .MapEnum<GameResultType>("game_result_type")
    .Build();

builder.Services.AddDbContext<LichessDbContext>(options =>
    options.UseNpgsql(dataSource, npgsqlOptions =>
    {
        // gean: EF also needs enum mappings so inserts use Postgres enum parameters, not C# integer values.
        npgsqlOptions.MapEnum<TimeControlType>("time_control_type", "chess_assistant");
        npgsqlOptions.MapEnum<GameResultType>("game_result_type", "chess_assistant");
    }));

builder.Services.AddGrpc();

builder.Services.AddHttpClient("Lichess", client =>
{
    client.BaseAddress = new Uri("https://lichess.org");
    client.Timeout = TimeSpan.FromMinutes(30);
});

builder.Services.AddScoped<LichessGameFetcher>();
builder.Services.AddSingleton<LichessStreamService>();
builder.Services.AddHostedService<OrphanedSessionCleanupService>();
builder.Services.AddHostedService<AnalysisBackfillService>();

var app = builder.Build();

app.MapGrpcService<LichessApiGrpcService>();
app.MapGet("/", () => "LichessApiService gRPC server is running.");

app.Run();
