using System.Text.Json;
using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;
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

        var prevMatch = await db.Matches
            .Where(m => m.SessionId == sessionId)
            .OrderByDescending(m => m.Id)
            .FirstOrDefaultAsync(ct);

        var match = new Match
        {
            MatchDate = DateOnly.FromDateTime(DateTime.UtcNow),
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

        return match.Id;
    }

    private async Task HandleGameFinishAsync(
        int matchId, string playerUsername, string lichessToken, CancellationToken ct)
    {
        using var scope = serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LichessDbContext>();
        var gameFetcher = scope.ServiceProvider.GetRequiredService<LichessGameFetcher>();

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

        await CreateDatasetAsync(db, gameEntity, matchId, ct);
    }

    private async Task CreateDatasetAsync(
        LichessDbContext db, Game game, int matchId, CancellationToken ct)
    {
        var match = await db.Matches.FirstAsync(m => m.Id == matchId, ct);

        var room = await db.Rooms.FirstOrDefaultAsync(r => r.PlayerId == match.PlayerId, ct);

        var sensorAverages = new Dictionary<SensorType, decimal>();

        if (room != null && game.StartedAt.HasValue && game.EndedAt.HasValue)
        {
            var start = game.StartedAt.Value;
            var end = game.EndedAt.Value;

            sensorAverages = await db.Sensors
                .Where(s => s.RoomId == room.Id && s.TimeStamp >= start && s.TimeStamp <= end)
                .GroupBy(s => s.Type)
                .Select(g => new { Type = g.Key, Avg = (decimal)g.Average(s => s.Value) })
                .ToDictionaryAsync(x => x.Type, x => x.Avg, ct);
        }

        var session = await db.Sessions
            .Include(s => s.HealthRecord)
            .FirstAsync(s => s.Id == match.SessionId, ct);
        var healthRecord = session.HealthRecord;

        // Trigger already incremented TotalGames, so subtract 1 for pre-game snapshot
        var openingStat = game.EcoCode != null
            ? await db.PlayerOpeningStats
                .FirstOrDefaultAsync(s => s.PlayerId == match.PlayerId && s.EcoCode == game.EcoCode, ct)
            : null;

        var openingGameCount = openingStat != null ? openingStat.TotalGames - 1 : 0;
        var openingWinRate = openingGameCount > 0
            ? (decimal)openingStat!.PlayerWins / openingGameCount
            : (decimal?)null;

        session.GameCount += 1;

        var dataset = new Dataset
        {
            MatchId = matchId,
            AvgLux = sensorAverages.ContainsKey(SensorType.Light) ? sensorAverages[SensorType.Light] : null,
            AvgCelsius = sensorAverages.ContainsKey(SensorType.Temperature) ? sensorAverages[SensorType.Temperature] : null,
            AvgPpm = sensorAverages.ContainsKey(SensorType.Co2) ? sensorAverages[SensorType.Co2] : null,
            WaterIntakeMl = (healthRecord?.WaterIntakeMl ?? 0) + session.TotalWaterMl,
            SleepDuration = healthRecord?.SleepDuration,
            AwakeDuration = healthRecord?.AwakeDuration,
            EcoCode = game.EcoCode,
            OpeningName = game.OpeningName,
            IsRated = game.IsRated,
            TotalPly = game.TotalPly,
            OpeningPly = game.OpeningPly,
            PlayerMoveCount = game.PlayerMoveCount,
            OpponentMoveCount = game.OpponentMoveCount,
            TimeControl = game.TimeControl,
            IsTimeIncrease = game.IsTimeIncrease,
            TimeIncreaseSec = game.TimeIncreaseSec,
            IsBerserk = game.IsBerserk,
            DurationMin = game.DurationMin,
            UserRating = game.UserRating,
            OppRating = game.OppRating,
            RatingDiff = game.RatingDiff,
            IsPlayerPieceBlack = game.IsPlayerPieceBlack,
            TerminationType = game.TerminationType,
            Result = game.Result,
            PlayerOpeningWinRate = openingWinRate,
            PlayerOpeningGameCount = openingGameCount > 0 ? openingGameCount : null
        };

        db.Datasets.Add(dataset);
        await db.SaveChangesAsync(ct);

        logger.LogInformation("Dataset created for match {MatchId}", matchId);
    }
}
