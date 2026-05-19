using System.Net;
using Grpc.Core;
using MachineLearning;
using PredictionService.grpc.Services;
using PredictionService.grpc.Tests.TestDoubles;
using PredictionService.grpc.Tests.TestHelpers;
using Xunit;

namespace PredictionService.grpc.Tests;

public class WinRateServiceTests
{
    [Fact]
    public async Task Predict_WhenFastApiReturnsSuccess_ParsesResponse()
    {
        var handler = FakeHttpMessageHandler.RespondJson(HttpStatusCode.OK, "{\"prediction\": 42.5}");
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("http://fastapi/") };
        var factory = new SingleClientHttpClientFactory(httpClient);
        var sut = new WinRateService(factory);

        var request = new WinratePredictionRequest
        {
            MinutesSlept = 480,
            MinutesAwake = 60,
            TemperatureCelsius = 20,
            Co2 = 400,
            Light = 0.5f
        };

        var response = await sut.Predict(request, TestServerCallContextFactory.Create());

        Assert.Equal(42.5f, response.Prediction);
    }

    [Fact]
    public async Task Predict_WhenFastApiReturnsNonSuccess_ThrowsRpcException()
    {
        var handler = FakeHttpMessageHandler.RespondJson(HttpStatusCode.BadRequest, "{\"detail\":\"bad\"}");
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("http://fastapi/") };
        var factory = new SingleClientHttpClientFactory(httpClient);
        var sut = new WinRateService(factory);

        var request = new WinratePredictionRequest
        {
            MinutesSlept = 480,
            MinutesAwake = 60,
            TemperatureCelsius = 20,
            Co2 = 400,
            Light = 0.5f
        };

        var ex = await Assert.ThrowsAsync<RpcException>(() => sut.Predict(request, TestServerCallContextFactory.Create()));
        Assert.Equal(StatusCode.Internal, ex.StatusCode);
    }
}
