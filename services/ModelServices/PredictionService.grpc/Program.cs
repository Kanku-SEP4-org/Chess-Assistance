using MachineLearning;
using PredictionService.grpc.ServiceInterfaces;
using PredictionService.grpc.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddGrpc();
builder.Services.AddHttpClient("FastApiClient", client =>
{
    client.BaseAddress = new Uri("http://localhost:8000/"); 
});
var app = builder.Build();
app.MapGrpcService<WinRateService>();
app.Run();

