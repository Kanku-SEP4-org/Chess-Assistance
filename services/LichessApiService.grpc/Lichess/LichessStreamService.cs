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
        const int maxRetries = 5;
        var attempt = 0;

        while (!ct.IsCancellationRequested)
        {
            try
            {
                var client = httpClientFactory.CreateClient("Lichess");

                using var request = new HttpRequestMessage(HttpMethod.Get, "/api/stream/event");
                request.Headers.Authorization =
                    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", lichessToken);

                using var response = await client.SendAsync(
                    request, HttpCompletionOption.ResponseHeadersRead, ct);

                if (response.StatusCode is System.Net.HttpStatusCode.Unauthorized
                    or System.Net.HttpStatusCode.Forbidden)
                {
                    logger.LogError(
                        "Auth failure ({StatusCode}) for session {SessionId}. Stopping stream",
                        response.StatusCode, sessionId);
                    return;
                }

                response.EnsureSuccessStatusCode();

                attempt = 0;
                logger.LogInformation("SSE stream connected for session {SessionId}", sessionId);

                await using var stream = await response.Content.ReadAsStreamAsync(ct);
                using var reader = new StreamReader(stream);

                await ProcessStreamWithTimeoutAsync(
                    reader, sessionId, playerId, playerUsername, lichessToken, ct);

                logger.LogWarning("SSE stream ended (EOF) for session {SessionId}", sessionId);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                logger.LogInformation("Stream cancelled for session {SessionId}", sessionId);
                return;
            }
            catch (HttpRequestException ex) when (
                ex.StatusCode is System.Net.HttpStatusCode.Unauthorized
                or System.Net.HttpStatusCode.Forbidden)
            {
                logger.LogError(ex,
                    "Auth failure for session {SessionId}. Stopping stream", sessionId);
                return;
            }
            catch (Exception ex) when (ex is IOException or HttpRequestException or TimeoutException)
            {
                logger.LogWarning(ex, "Transient stream error for session {SessionId}", sessionId);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Unexpected stream error for session {SessionId}", sessionId);
            }

            attempt++;
            if (attempt > maxRetries)
            {
                logger.LogError(
                    "Max retries ({MaxRetries}) exceeded for session {SessionId}. Giving up",
                    maxRetries, sessionId);
                return;
            }

            var delay = TimeSpan.FromSeconds(Math.Pow(2, attempt));
            logger.LogInformation(
                "Reconnecting session {SessionId} in {Delay}s (attempt {Attempt}/{MaxRetries})",
                sessionId, delay.TotalSeconds, attempt, maxRetries);

            await Task.Delay(delay, ct);
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

            currentMatchId = await ParseAndDispatchAsync(
                line, currentMatchId, sessionId, playerId, playerUsername, lichessToken, ct);
        }
    }

    internal async Task ProcessStreamWithTimeoutAsync(
        TextReader reader,
        int sessionId,
        int playerId,
        string playerUsername,
        string lichessToken,
        CancellationToken ct)
    {
        const int timeoutSeconds = 60;
        int? currentMatchId = null;

        while (!ct.IsCancellationRequested)
        {
            using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            timeoutCts.CancelAfter(TimeSpan.FromSeconds(timeoutSeconds));

            string? line;
            try
            {
                line = await reader.ReadLineAsync(timeoutCts.Token);
            }
            catch (OperationCanceledException) when (!ct.IsCancellationRequested)
            {
                throw new TimeoutException(
                    $"No data for {timeoutSeconds}s on session {sessionId}");
            }

            if (line == null)
                break;

            currentMatchId = await ParseAndDispatchAsync(
                line, currentMatchId, sessionId, playerId, playerUsername, lichessToken, ct);
        }
    }

    private async Task<int?> ParseAndDispatchAsync(
        string line,
        int? currentMatchId,
        int sessionId,
        int playerId,
        string playerUsername,
        string lichessToken,
        CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(line))
            return currentMatchId;

        LichessStreamEvent? streamEvent;
        try
        {
            streamEvent = JsonSerializer.Deserialize<LichessStreamEvent>(line);
        }
        catch (JsonException ex)
        {
            logger.LogWarning(ex, "Failed to parse stream event: {Line}", line);
            return currentMatchId;
        }

        if (streamEvent == null)
            return currentMatchId;

        switch (streamEvent.Type)
        {
            case "gameStart":
                return await HandleGameStartAsync(sessionId, playerId, playerUsername, ct);

            case "gameFinish" when currentMatchId.HasValue:
                await HandleGameFinishAsync(
                    currentMatchId.Value, playerUsername, lichessToken, ct);
                return null;

            default:
                return currentMatchId;
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

        LichessGameDto? lichessGame = null;
        const int maxFetchAttempts = 3;

        for (var attempt = 1; attempt <= maxFetchAttempts; attempt++)
        {
            try
            {
                lichessGame = await gameFetcher.FetchLatestGameAsync(playerUsername, lichessToken, ct);
                if (lichessGame != null) break;

                logger.LogWarning(
                    "Fetch returned null for match {MatchId}, attempt {Attempt}/{Max}",
                    matchId, attempt, maxFetchAttempts);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex,
                    "Fetch failed for match {MatchId}, attempt {Attempt}/{Max}",
                    matchId, attempt, maxFetchAttempts);
            }

            if (attempt < maxFetchAttempts)
                await Task.Delay(TimeSpan.FromSeconds(2 * attempt), ct);
        }

        if (lichessGame == null)
        {
            logger.LogWarning("Could not fetch game data for match {MatchId} after retries", matchId);
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

        var previousResults = await db.Games
            .Where(g => g.Match.SessionId == match.SessionId && g.MatchId != matchId)
            .OrderByDescending(g => g.StartedAt)
            .Select(g => g.Result)
            .ToListAsync(ct);

        var consecutiveLossesPregame = 0;
        foreach (var r in previousResults)
        {
            if (r == GameResultType.Loss)
                consecutiveLossesPregame++;
            else
                break;
        }

        decimal? avgTpmSeconds = null;
        if (game.StartedAt.HasValue && game.EndedAt.HasValue && game.PlayerMoveCount is > 0)
        {
            var durationSeconds = (decimal)(game.EndedAt.Value - game.StartedAt.Value).TotalSeconds;
            avgTpmSeconds = durationSeconds / game.PlayerMoveCount.Value;
        }

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
            PlayerOpeningGameCount = openingGameCount > 0 ? openingGameCount : null,
            InaccuracyCnt = game.InaccuracyCnt,
            MistakeCnt = game.MistakeCnt,
            BlunderCnt = game.BlunderCnt,
            Acpl = game.Acpl,
            Accuracy = game.Accuracy,
            ConsecutiveLossesPregame = consecutiveLossesPregame,
            AvgTpmSeconds = avgTpmSeconds
        };

        db.Datasets.Add(dataset);
        await db.SaveChangesAsync(ct);

        logger.LogInformation("Dataset created for match {MatchId}", matchId);
    }
}
