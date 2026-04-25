using PredictionService.grpc.Interceptors;
using PredictionService.grpc.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<GlobalExceptionInterceptor>();
});
builder.Services.AddHttpClient("FastApiClient", client =>
{
    client.BaseAddress = new Uri("http://localhost:8000/");
});
var app = builder.Build();
app.MapGrpcService<WinRateService>();
app.Run();

