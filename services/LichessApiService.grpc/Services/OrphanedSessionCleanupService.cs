using LichessApiService.Grpc.Data;
using Microsoft.EntityFrameworkCore;

namespace LichessApiService.Grpc.Services;

public class OrphanedSessionCleanupService(
    IServiceProvider serviceProvider,
    ILogger<OrphanedSessionCleanupService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var scope = serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LichessDbContext>();

        var orphaned = await db.Sessions
            .Where(s => s.EndedAt == null)
            .ToListAsync(stoppingToken);

        if (orphaned.Count == 0)
            return;

        var now = DateTime.UtcNow;
        foreach (var session in orphaned)
        {
            session.EndedAt = now;
            logger.LogWarning(
                "Closed orphaned session {SessionId} (player {PlayerId}, started {StartedAt})",
                session.Id, session.PlayerId, session.StartedAt);
        }

        await db.SaveChangesAsync(stoppingToken);
        logger.LogInformation("Cleaned up {Count} orphaned session(s) on startup", orphaned.Count);
    }
}
