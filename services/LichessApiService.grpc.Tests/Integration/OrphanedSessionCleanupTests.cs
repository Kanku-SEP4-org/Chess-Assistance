using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Integration;

public class OrphanedSessionCleanupTests : IDisposable
{
    private readonly ServiceProvider _serviceProvider;
    private readonly string _dbName = Guid.NewGuid().ToString();

    public OrphanedSessionCleanupTests()
    {
        var services = new ServiceCollection();
        services.AddDbContext<LichessDbContext>(options =>
            options.UseInMemoryDatabase(_dbName));
        _serviceProvider = services.BuildServiceProvider();
    }

    private LichessDbContext CreateDb() =>
        _serviceProvider.CreateScope().ServiceProvider.GetRequiredService<LichessDbContext>();

    private async Task<HealthRecord> SeedHealthRecordAsync(LichessDbContext db, int playerId = 1)
    {
        var hr = new HealthRecord
        {
            SleepTime = DateTime.UtcNow.AddHours(-8),
            AwakenTime = DateTime.UtcNow.AddHours(-1),
            ConfirmedAt = DateTime.UtcNow.AddMinutes(-5),
            PlayerId = playerId
        };
        db.HealthRecords.Add(hr);
        await db.SaveChangesAsync();
        return hr;
    }

    private TestableCleanupService CreateService() => new(
        _serviceProvider, Mock.Of<ILogger<OrphanedSessionCleanupService>>());

    [Fact]
    public async Task ExecuteAsync_ClosesOrphanedSessions()
    {
        var db = CreateDb();
        var hr = await SeedHealthRecordAsync(db);

        var orphaned = new Session
        {
            StartedAt = DateTime.UtcNow.AddHours(-2),
            PlayerId = 1,
            HealthRecordId = hr.Id
        };
        var alreadyEnded = new Session
        {
            StartedAt = DateTime.UtcNow.AddHours(-5),
            EndedAt = DateTime.UtcNow.AddHours(-4),
            PlayerId = 1,
            HealthRecordId = hr.Id
        };

        db.Sessions.AddRange(orphaned, alreadyEnded);
        await db.SaveChangesAsync();

        await CreateService().RunAsync(CancellationToken.None);

        var freshDb = CreateDb();
        var updatedOrphaned = await freshDb.Sessions.FindAsync(orphaned.Id);
        var updatedEnded = await freshDb.Sessions.FindAsync(alreadyEnded.Id);

        Assert.NotNull(updatedOrphaned!.EndedAt);
        Assert.Equal(alreadyEnded.EndedAt, updatedEnded!.EndedAt);
    }

    [Fact]
    public async Task ExecuteAsync_NoOrphans_DoesNothing()
    {
        var db = CreateDb();
        var hr = await SeedHealthRecordAsync(db);

        db.Sessions.Add(new Session
        {
            StartedAt = DateTime.UtcNow.AddHours(-3),
            EndedAt = DateTime.UtcNow.AddHours(-2),
            PlayerId = 1,
            HealthRecordId = hr.Id
        });
        await db.SaveChangesAsync();

        await CreateService().RunAsync(CancellationToken.None);

        var freshDb = CreateDb();
        var sessions = await freshDb.Sessions.ToListAsync();
        Assert.Single(sessions);
        Assert.NotNull(sessions[0].EndedAt);
    }

    public void Dispose()
    {
        _serviceProvider.Dispose();
    }
}

internal class TestableCleanupService(
    IServiceProvider serviceProvider,
    ILogger<OrphanedSessionCleanupService> logger)
    : OrphanedSessionCleanupService(serviceProvider, logger)
{
    public Task RunAsync(CancellationToken ct) => ExecuteAsync(ct);
}
