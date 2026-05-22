using System.Text.Json;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;

namespace LichessApiService.Grpc.Lichess;

public class LichessGameFetcher(IHttpClientFactory httpClientFactory)
{
    // the virtual modifier allows mocking in unit tests, and the method can be overridden if needed
    public virtual async Task<LichessGameDto?> FetchLatestGameAsync(string username, string lichessToken,
        CancellationToken ct = default)
    {
        // Named client configured in Program.cs with base address and default headers
        var client = httpClientFactory.CreateClient("Lichess"); 

        using var request = new HttpRequestMessage(HttpMethod.Get,
            $"/api/games/user/{username}?max=1&sort=dateDesc&pgnInJson=true&opening=true&evals=true");
        request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", lichessToken);
        request.Headers.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/x-ndjson"));

        using var response = await client.SendAsync(request, ct);
        response.EnsureSuccessStatusCode();

        var body = await response.Content.ReadAsStringAsync(ct);
        var firstLine = body.Split('\n', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
        if (string.IsNullOrWhiteSpace(firstLine))
            return null;

        return JsonSerializer.Deserialize<LichessGameDto>(firstLine);
    }

    public virtual Game MapToGameEntity(LichessGameDto dto, string playerUsername, int matchId)
    {
        var isBlack = string.Equals(
            dto.Players.Black.User?.Id, playerUsername, StringComparison.OrdinalIgnoreCase);

        var playerSide = isBlack ? dto.Players.Black : dto.Players.White;
        var opponentSide = isBlack ? dto.Players.White : dto.Players.Black;

        var moves = dto.Moves?.Split(' ', StringSplitOptions.RemoveEmptyEntries) ?? [];
        var totalPly = moves.Length;

        var playerMoveCount = isBlack
            ? totalPly / 2
            : (totalPly + 1) / 2;
        var opponentMoveCount = totalPly - playerMoveCount;

        var startedAt = DateTimeOffset.FromUnixTimeMilliseconds(dto.CreatedAt).UtcDateTime;
        var endedAt = DateTimeOffset.FromUnixTimeMilliseconds(dto.LastMoveAt).UtcDateTime;
        var durationMin = (int)(endedAt - startedAt).TotalMinutes;

        GameResultType result;
        if (dto.Winner == null)
            result = GameResultType.Draw;
        else if ((dto.Winner == "black" && isBlack) || (dto.Winner == "white" && !isBlack))
            result = GameResultType.Win;
        else
            result = GameResultType.Loss;

        return new Game
        {
            LichessGameId = dto.Id,
            TimeControl = ParseTimeControl(dto.Speed),
            IsTimeIncrease = dto.Clock is not null && dto.Clock.Increment > 0,
            TimeIncreaseSec = dto.Clock?.Increment,
            IsRated = dto.Rated,
            IsBerserk = playerSide.Berserk,
            Source = dto.Source,
            EcoCode = dto.Opening?.Eco,
            OpeningName = dto.Opening?.Name,
            TotalPly = totalPly > 0 ? totalPly : null,
            OpeningPly = dto.Opening?.Ply,
            PlayerMoveCount = totalPly > 0 ? playerMoveCount : null,
            OpponentMoveCount = totalPly > 0 ? opponentMoveCount : null,
            UserRating = playerSide.Rating,
            OppRating = opponentSide.Rating,
            RatingDiff = playerSide.RatingDiff,
            IsPlayerPieceBlack = isBlack,
            Result = result,
            TerminationType = dto.Status,
            StartedAt = startedAt,
            EndedAt = endedAt,
            DurationMin = durationMin,
            MatchId = matchId,
            Analysis = playerSide.Analysis is not null
                ? new GameAnalysis
                {
                    InaccuracyCnt = playerSide.Analysis.Inaccuracy,
                    MistakeCnt = playerSide.Analysis.Mistake,
                    BlunderCnt = playerSide.Analysis.Blunder,
                    Acpl = playerSide.Analysis.Acpl,
                    Accuracy = playerSide.Analysis.Accuracy,
                }
                : null
        };
    }

    private static TimeControlType ParseTimeControl(string speed) => speed.ToLowerInvariant() switch
    {
        "bullet" => TimeControlType.Bullet,
        "blitz" => TimeControlType.Blitz,
        "rapid" => TimeControlType.Rapid,
        "classical" => TimeControlType.Classical,
        _ => TimeControlType.Rapid
    };
}
