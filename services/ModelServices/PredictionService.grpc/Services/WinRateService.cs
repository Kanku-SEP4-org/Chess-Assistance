using System.Text.Json;
using Grpc.Core;
using MachineLearning;
using PredictionService.grpc.ServiceInterfaces;

namespace PredictionService.grpc.Services;

public class WinRateService : WinrateService.WinrateServiceBase, IWinRateService
{
    // Must match the type integers your IoT devices send for each sensor
    private const int SensorTypeTemperature = 1;
    private const int SensorTypeCo2        = 2;
    private const int SensorTypeLight      = 3;

    private static readonly JsonSerializerOptions _kebabCase = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.KebabCaseLower
    };

    private readonly HttpClient _httpClient;

    public WinRateService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public override async Task<WinratePredictionResponse> Predict(WinratePredictionInput request, ServerCallContext context)
    {
        var readings = request.Room.SensorReading;
        var payload = new
        {
            minutes_slept       = request.PhysicalCondition.MinutesSlept,
            minutes_awake       = request.PhysicalCondition.MinutesAwake,
            temperature_celsius = (float)(readings.FirstOrDefault(r => r.Type == SensorTypeTemperature)?.Value ?? 0),
            co2                 = (float)(readings.FirstOrDefault(r => r.Type == SensorTypeCo2)?.Value ?? 0),
            light               = (float)(readings.FirstOrDefault(r => r.Type == SensorTypeLight)?.Value ?? 0),
        };

        var httpResponse = await _httpClient.PostAsJsonAsync("http://localhost:8000/predict", payload);
        httpResponse.EnsureSuccessStatusCode();

        var fastApiResult = await httpResponse.Content.ReadFromJsonAsync<FastApiPredictResponse>(_kebabCase);
        return new WinratePredictionResponse { Winrate = fastApiResult?.Winrate ?? 0 };
    }
    
    private record FastApiPredictResponse(int Winrate);
}
