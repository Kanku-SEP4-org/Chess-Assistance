using System.Text;
using System.Text.Json;
using Google.Protobuf;
using Grpc.Core;
using MachineLearning;
using PredictionService.grpc.ServiceInterfaces;

namespace PredictionService.grpc.Services;

public class WinRateService : WinrateService.WinrateServiceBase
{
    private static readonly JsonSerializerOptions _kebabCase = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.KebabCaseLower
    };

    private readonly IHttpClientFactory _httpClientFactory;

    public WinRateService(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }

    public override async Task<WinratePredictionResponse> Predict(
        WinratePredictionRequest request, 
        ServerCallContext context)
    {
        try
        {
            // odd af but ok i guess? (REST -> gRPC -> REST)???
            var formatter = new JsonFormatter(JsonFormatter.Settings.Default);
            var jsonPayload = formatter.Format(request); // gRPC -> JSON

            // prepare REST request
            var fastApiClient = _httpClientFactory.CreateClient("FastApiClient");
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            // check the machine_learning/api/main.py for REST request format
            var response = await fastApiClient.PostAsync("predict", content);
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                throw new RpcException(new Status(StatusCode.Internal, $"FastAPI Error: {response.StatusCode}. Details: {errorContent}"));
            }

            // Read the FastAPI JSON response
            string jsonResponse = await response.Content.ReadAsStringAsync();

            // Convert the FastAPI JSON response back into a gRPC WinratePredictionResponse
            var parser = new JsonParser(JsonParser.Settings.Default);
            var grpcResponse = parser.Parse<WinratePredictionResponse>(jsonResponse);

            return Task.FromResult(grpcResponse).Result;
        }
        catch (RpcException)
        {
            throw; 
        }
        catch (HttpRequestException e)
        {
            throw new RpcException(new Status(StatusCode.Unavailable, $"Could not connect to FastAPI server: {e.Message}"));
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    }

    public override async Task<WinratePredictionResponse> PredictMock(
        WinratePredictionRequest request, 
        ServerCallContext context)
    {
       
       try
       {
           var random = new Random();
           var mockWinrate = random.Next(0, 101); // Random winrate between 0 and 100
           var response = new WinratePredictionResponse()
           {
               Winrate = mockWinrate
           };
           return Task.FromResult(response).Result;
       }
       catch (RpcException)
       {
           throw; 
       }
       catch (HttpRequestException e)
       {
           throw new RpcException(new Status(StatusCode.Unavailable, $"Could not connect to FastAPI server: {e.Message}"));
       }
       catch (Exception e)
       {
           Console.WriteLine(e);
           throw;
       }
    }

}
