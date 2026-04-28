using GrpcService.Interceptors;
using GrpcService.Services;
using IotService;
using Microsoft.AspNetCore.Server.Kestrel.Core;

// Required for HTTP/2 cleartext (no TLS) gRPC client calls to the C# IoT service
AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

var builder = WebApplication.CreateBuilder(args);

// ── Kestrel: listen on 50051 with HTTP/2 only (gRPC requirement) ──────────────
builder.WebHost.ConfigureKestrel(options =>
{
    var port = int.Parse(builder.Configuration["Grpc:Port"] ?? "50051");
    options.ListenAnyIP(port, listenOptions =>
    {
        listenOptions.Protocols = HttpProtocols.Http2;
    });
});

// ── gRPC server ───────────────────────────────────────────────────────────────
builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<GlobalExceptionInterceptor>();
});

// ── HTTP client → FastAPI ML service ─────────────────────────────────────────
var mlApiBaseUrl = builder.Configuration["MlApi:BaseUrl"] ?? "http://localhost:8000/";
builder.Services.AddHttpClient("FastApiClient", client =>
{
    client.BaseAddress = new Uri(mlApiBaseUrl);
});

// ── gRPC client → C# IoT service ─────────────────────────────────────────────
var iotHost = builder.Configuration["IotService:Host"] ?? "localhost";
var iotPort = builder.Configuration["IotService:Port"] ?? "5143";
builder.Services.AddGrpcClient<iotService.iotServiceClient>(o =>
{
    o.Address = new Uri($"http://{iotHost}:{iotPort}");
});

var app = builder.Build();

app.MapGrpcService<WinRateServiceImpl>();
app.MapGrpcService<IoTProxyServiceImpl>();
app.MapGet("/", () => "Chess Assistance gRPC Service is running.");

app.Run();
