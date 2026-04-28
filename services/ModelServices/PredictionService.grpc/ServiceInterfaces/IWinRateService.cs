using Grpc.Core;
using MachineLearning;

namespace PredictionService.grpc.ServiceInterfaces;

public interface IWinRateService
{
    Task<WinratePredictionResponse> Predict(WinratePredictionInput request, ServerCallContext context);
}