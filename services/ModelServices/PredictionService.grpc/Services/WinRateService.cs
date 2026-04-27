using System.Text;
using Google.Protobuf;
using Grpc.Core;
using MachineLearning;

namespace PredictionService.grpc.Services;

public class WinRateService : WinrateService.WinrateServiceBase
{
    private readonly IHttpClientFactory _httpClientFactory;

    public WinRateService(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }

    public override async Task<WinratePredictionResponse> Predict(
        WinratePredictionRequest request,
        ServerCallContext context)
    {
        var formatter = new JsonFormatter(JsonFormatter.Settings.Default.WithPreserveProtoFieldNames(true));
        var jsonPayload = formatter.Format(request);

        var fastApiClient = _httpClientFactory.CreateClient("FastApiClient");
        var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

        var response = await fastApiClient.PostAsync("predict", content);
        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync();
            throw new RpcException(new Status(StatusCode.Internal,
                $"FastAPI Error: {response.StatusCode}. Details: {errorContent}"));
        }

        var jsonResponse = await response.Content.ReadAsStringAsync();
        var parser = new JsonParser(JsonParser.Settings.Default);
        return parser.Parse<WinratePredictionResponse>(jsonResponse);
    }

    public override Task<WinratePredictionResponse> PredictMock(
        WinratePredictionRequest request,
        ServerCallContext context)
    {
        var random = new Random();
        var response = new WinratePredictionResponse
        {
            Winrate = random.Next(0, 101)
        };
        return Task.FromResult(response);
    }
}
