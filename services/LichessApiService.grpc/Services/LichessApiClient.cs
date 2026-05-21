using LichessApiService.Grpc.Protos;

namespace LichessApiService.Grpc.Services;

public class LichessApiClient(
    SensorFeedService.SensorFeedServiceClient grpcClient,
    ILogger<LichessApiClient> logger)
{
    // virtual allows mocking in unit tests and overriding if needed
    public virtual async Task StartSensorFeedAsync(int matchId)
    {
        logger.LogInformation("Requesting IoT to start sensor feed for match {MatchId}", matchId);

        var response = await grpcClient.StartSensorFeedAsync(new SensorFeedRequest { MatchId = matchId });

        if (!response.Success)
            logger.LogWarning("IoT StartSensorFeed failed for match {MatchId}: {Message}",
                matchId, response.Message);
    }

    public virtual async Task StopSensorFeedAsync(int matchId)
    {
        logger.LogInformation("Requesting IoT to stop sensor feed for match {MatchId}", matchId);

        var response = await grpcClient.StopSensorFeedAsync(new SensorFeedRequest { MatchId = matchId });

        if (!response.Success)
            logger.LogWarning("IoT StopSensorFeed failed for match {MatchId}: {Message}",
                matchId, response.Message);
    }
}
