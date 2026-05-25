using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Lichess;
using Microsoft.EntityFrameworkCore;

namespace LichessApiService.Grpc.Services;

public class AnalysisBackfillService(
    IServiceProvider serviceProvider,
    ILogger<AnalysisBackfillService> logger) : BackgroundService
{
    private static readonly TimeSpan Interval = TimeSpan.FromMinutes(30);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await BackfillAsync(stoppingToken);
            await Task.Delay(Interval, stoppingToken);
        }
    }

    internal async Task BackfillAsync(CancellationToken ct)
    {
        using var scope = serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LichessDbContext>();
        var gameFetcher = scope.ServiceProvider.GetRequiredService<LichessGameFetcher>();

        var unanalyzed = await db.Games
            .Where(g => g.LichessGameId != null && g.Analysis == null)
            .Select(g => new
            {
                g.Id,
                g.LichessGameId,
                g.IsPlayerPieceBlack,
                g.Match.PlayerId
            })
            .ToListAsync(ct);

        if (unanalyzed.Count == 0)
            return;

        var playerIds = unanalyzed.Select(e => e.PlayerId).Distinct().ToList();
        var playerUsernames = await db.Players
            .Where(p => playerIds.Contains(p.Id))
            .ToDictionaryAsync(p => p.Id, p => p.Username, ct);

        logger.LogInformation("Found {Count} game(s) without analysis to check", unanalyzed.Count);

        foreach (var entry in unanalyzed)
        {
            try
            {
                var lichessGame = await gameFetcher.FetchGameByIdAsync(entry.LichessGameId!, ct);
                if (lichessGame == null)
                    continue;

                if (!playerUsernames.TryGetValue(entry.PlayerId, out var username))
                    continue;

                var isBlack = entry.IsPlayerPieceBlack == true;
                var playerSide = isBlack ? lichessGame.Players.Black : lichessGame.Players.White;

                if (playerSide.Analysis == null)
                    continue;

                var analysis = new GameAnalysis
                {
                    GameId = entry.Id,
                    InaccuracyCnt = playerSide.Analysis.Inaccuracy,
                    MistakeCnt = playerSide.Analysis.Mistake,
                    BlunderCnt = playerSide.Analysis.Blunder,
                    Acpl = playerSide.Analysis.Acpl,
                    Accuracy = playerSide.Analysis.Accuracy
                };

                db.GameAnalyses.Add(analysis);
                await db.SaveChangesAsync(ct);

                logger.LogInformation(
                    "Backfilled analysis for game {LichessGameId} (id={GameId})",
                    entry.LichessGameId, entry.Id);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex,
                    "Failed to backfill analysis for game {LichessGameId} (id={GameId})",
                    entry.LichessGameId, entry.Id);
            }

            await Task.Delay(TimeSpan.FromSeconds(1), ct);
        }
    }
}
