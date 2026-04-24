using MachineLearning;
using PredictionService.grpc.ServiceInterfaces;
using PredictionService.grpc.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddGrpc();
builder.Services.AddHttpClient<IWinRateService, WinRateService>();
var app = builder.Build();
app.MapGrpcService<WinRateService>();
app.MapPost("/api/winrate/predict", async (WinRateService winRateService) =>
{
    var response = await winRateService.Predict(new WinratePredictionInput(), null!);
    return Results.Ok(response);
});
app.Run();

