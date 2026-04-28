using PredictionService.grpc.Interceptors;
using PredictionService.grpc.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<GlobalExceptionInterceptor>();
});
var fastApiBaseUrl = builder.Configuration["FastApi:BaseUrl"] ?? "http://localhost:8000/";
builder.Services.AddHttpClient("FastApiClient", client =>
{
    client.BaseAddress = new Uri(fastApiBaseUrl);
});
var app = builder.Build();
app.MapGrpcService<WinRateService>();
app.Run();

