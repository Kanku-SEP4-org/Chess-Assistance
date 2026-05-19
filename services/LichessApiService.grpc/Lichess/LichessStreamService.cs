using System.Text.Json;
using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Services;
using Microsoft.EntityFrameworkCore;

namespace LichessApiService.Grpc.Lichess;

public class LichessStreamService(
    IHttpClientFactory httpClientFactory,
    IServiceProvider serviceProvider,
    ILogger<LichessStreamService> logger)
{
    public async Task StreamSessionAsync(
        int sessionId,
        int playerId,
        string playerUsername,
        string lichessToken,
        CancellationToken ct)
    {
        var client = httpClientFactory.CreateClient("Lichess");

        using var request = new HttpRequestMessage(HttpMethod.Get, "/api/stream/event");
        request.Headers.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", lichessToken);

        try
        {
            using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
            response.EnsureSuccessStatusCode();

            await using var stream = await response.Content.ReadAsStreamAsync(ct);
            using var reader = new StreamReader(stream);

            await ProcessStreamAsync(reader, sessionId, playerId, playerUsername, lichessToken, ct);
        }
        catch (OperationCanceledException)
        {
            logger.LogInformation("Stream cancelled for session {SessionId}", sessionId);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Stream error for session {SessionId}", sessionId);
        }
    }

    internal async Task ProcessStreamAsync(
        TextReader reader,
        int sessionId,
        int playerId,
        string playerUsername,
        string lichessToken,
        CancellationToken ct)
    {
        int? currentMatchId = null;

        while (!ct.IsCancellationRequested)
        {
            string? line;
            try
            {
                line = await reader.ReadLineAsync(ct);
            }
            catch (OperationCanceledException)
            {
                break;
            }

            if (line == null)
                break;

            if (string.IsNullOrWhiteSpace(line))
                continue;

            LichessStreamEvent? streamEvent;
            try
            {
                streamEvent = JsonSerializer.Deserialize<LichessStreamEvent>(line);
            }
            catch (JsonException ex)
            {
                logger.LogWarning(ex, "Failed to parse stream event: {Line}", line);
                continue;
            }

            if (streamEvent == null)
                continue;

            switch (streamEvent.Type)
            {
                case "gameStart":
                    currentMatchId = await HandleGameStartAsync(
                        sessionId, playerId, playerUsername, ct);
                    break;

                case "gameFinish" when currentMatchId.HasValue:
                    await HandleGameFinishAsync(
                        currentMatchId.Value, playerUsername, lichessToken, ct);
                    currentMatchId = null;
                    break;
            }
        }
    }

    private async Task<int> HandleGameStartAsync(
        int sessionId, int playerId, string playerUsername, CancellationToken ct)
    {
        using var scope = serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LichessDbContext>();
        var iotClient = scope.ServiceProvider.GetRequiredService<LichessApiClient>();

        var prevMatch = await db.Matches
            .Where(m => m.SessionId == sessionId)
            .OrderByDescending(m => m.Id)
            .FirstOrDefaultAsync(ct);

        var match = new Match
        {
            MatchDate = DateOnly.FromDateTime(DateTime.UtcNow),
            Status = SessionStatus.Pending,
            DurationFromPrevMatch = prevMatch != null
                ? DateTime.UtcNow - prevMatch.MatchDate.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc)
                : null,
            SessionId = sessionId,
            PlayerId = playerId
        };

        db.Matches.Add(match);
        await db.SaveChangesAsync(ct);

        logger.LogInformation(
            "Match {MatchId} created for session {SessionId}", match.Id, sessionId);

        try
        {
            await iotClient.StartSensorFeedAsync(match.Id);
        }
        catch (Exception ex)
        {
            logger.LogWarning(ex,
                "Failed to start sensor feed for match {MatchId} — IoT service may not be available", match.Id);
        }

        return match.Id;
    }

    private async Task HandleGameFinishAsync(
        int matchId, string playerUsername, string lichessToken, CancellationToken ct)
    {
        using var scope = serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LichessDbContext>();
        var iotClient = scope.ServiceProvider.GetRequiredService<LichessApiClient>();
        var gameFetcher = scope.ServiceProvider.GetRequiredService<LichessGameFetcher>();

        try
        {
            await iotClient.StopSensorFeedAsync(matchId);
        }
        catch (Exception ex)
        {
            logger.LogWarning(ex,
                "Failed to stop sensor feed for match {MatchId} — IoT service may not be available", matchId);
        }

        // Small delay to ensure Lichess API has the finished game data
        await Task.Delay(TimeSpan.FromSeconds(2), ct);

        var lichessGame = await gameFetcher.FetchLatestGameAsync(playerUsername, lichessToken, ct);
        if (lichessGame == null)
        {
            logger.LogWarning("Could not fetch game data for match {MatchId}", matchId);
            return;
        }

        var gameEntity = gameFetcher.MapToGameEntity(lichessGame, playerUsername, matchId);
        db.Games.Add(gameEntity);
        await db.SaveChangesAsync(ct);

        logger.LogInformation(
            "Game {LichessGameId} inserted for match {MatchId}", lichessGame.Id, matchId);
    }
}
