using System.Text;
using Google.Protobuf;
using Grpc.Core;
using MachineLearning;

namespace GrpcService.Services;

public class WinRateServiceImpl : WinrateService.WinrateServiceBase
{
    private readonly IHttpClientFactory _httpClientFactory;

    public WinRateServiceImpl(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }

    public override async Task<WinratePredictionResponse> Predict(
        WinratePredictionRequest request,
        ServerCallContext context)
    {
        // Preserve proto field names (snake_case) so FastAPI receives the exact field names it expects
        var formatter = new JsonFormatter(JsonFormatter.Settings.Default.WithPreserveProtoFieldNames(true));
        var jsonPayload = formatter.Format(request);

        var client = _httpClientFactory.CreateClient("FastApiClient");
        var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

        var response = await client.PostAsync("predict", content);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new RpcException(new Status(StatusCode.Internal,
                $"FastAPI error: {response.StatusCode}. {error}"));
        }

        var json = await response.Content.ReadAsStringAsync();
        var parser = new JsonParser(JsonParser.Settings.Default);
        return parser.Parse<WinratePredictionResponse>(json);
    }

    public override Task<WinratePredictionResponse> PredictMock(
        WinratePredictionRequest request,
        ServerCallContext context)
    {
        return Task.FromResult(new WinratePredictionResponse { Prediction = 0.5f });
    }
}
