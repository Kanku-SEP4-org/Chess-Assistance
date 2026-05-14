using Grpc.Core;
using LichessApiService.Grpc.Protos;

namespace LichessApiService.Grpc.Tests.Mocks;

public class MockSensorFeedService : SensorFeedService.SensorFeedServiceBase
{
    public List<int> StartedMatchIds { get; } = [];
    public List<int> StoppedMatchIds { get; } = [];

    public override Task<SensorFeedResponse> StartSensorFeed(
        SensorFeedRequest request, ServerCallContext context)
    {
        StartedMatchIds.Add(request.MatchId);
        return Task.FromResult(new SensorFeedResponse
        {
            Success = true,
            Message = $"Mock: started sensor feed for match {request.MatchId}"
        });
    }

    public override Task<SensorFeedResponse> StopSensorFeed(
        SensorFeedRequest request, ServerCallContext context)
    {
        StoppedMatchIds.Add(request.MatchId);
        return Task.FromResult(new SensorFeedResponse
        {
            Success = true,
            Message = $"Mock: stopped sensor feed for match {request.MatchId}"
        });
    }
}
