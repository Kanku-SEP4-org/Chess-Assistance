using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Integration;

public class AnalysisBackfillTests : IDisposable
{
    private readonly ServiceProvider _serviceProvider;
    private readonly AnalysisBackfillService _service;
    private readonly Mock<LichessGameFetcher> _mockGameFetcher;
    private readonly string _dbName = Guid.NewGuid().ToString();

    public AnalysisBackfillTests()
    {
        var mockHttpFactory = new Mock<IHttpClientFactory>();

        _mockGameFetcher = new Mock<LichessGameFetcher>(mockHttpFactory.Object);

        var services = new ServiceCollection();
        services.AddDbContext<LichessDbContext>(options =>
            options.UseInMemoryDatabase(_dbName));
        services.AddScoped(_ => _mockGameFetcher.Object);

        _serviceProvider = services.BuildServiceProvider();

        _service = new AnalysisBackfillService(
            _serviceProvider,
            Mock.Of<ILogger<AnalysisBackfillService>>());
    }

    private LichessDbContext CreateDb() =>
        _serviceProvider.CreateScope().ServiceProvider.GetRequiredService<LichessDbContext>();

    private async Task<(int sessionId, int matchId, int gameId)> SeedGameWithoutAnalysisAsync()
    {
        var db = CreateDb();

        var player = new Player { LichessId = "testplayer", Username = "TestPlayer" };
        db.Players.Add(player);
        await db.SaveChangesAsync();

        var healthRecord = new HealthRecord
        {
            SleepTime = DateTime.UtcNow.AddHours(-8),
            AwakenTime = DateTime.UtcNow.AddHours(-1),
            ConfirmedAt = DateTime.UtcNow,
            PlayerId = player.Id
        };
        db.HealthRecords.Add(healthRecord);
        await db.SaveChangesAsync();

        var session = new Session
        {
            StartedAt = DateTime.UtcNow,
            PlayerId = player.Id,
            HealthRecordId = healthRecord.Id
        };
        db.Sessions.Add(session);
        await db.SaveChangesAsync();

        var match = new LichessApiService.Grpc.Data.Entities.Match
        {
            MatchDate = DateOnly.FromDateTime(DateTime.UtcNow),
            SessionId = session.Id,
            PlayerId = player.Id
        };
        db.Matches.Add(match);
        await db.SaveChangesAsync();

        var game = new Game
        {
            LichessGameId = "test1234",
            TimeControl = TimeControlType.Blitz,
            Result = GameResultType.Win,
            IsPlayerPieceBlack = false,
            MatchId = match.Id
        };
        db.Games.Add(game);
        await db.SaveChangesAsync();

        return (session.Id, match.Id, game.Id);
    }

    private static LichessGameDto CreateGameDtoWithAnalysis() => new()
    {
        Id = "test1234",
        Rated = true,
        Speed = "blitz",
        Status = "mate",
        CreatedAt = 1700000000000,
        LastMoveAt = 1700000600000,
        Players = new LichessPlayersDto
        {
            White = new LichessPlayerSideDto
            {
                User = new LichessUserDto { Id = "testplayer", Name = "TestPlayer" },
                Rating = 1500,
                RatingDiff = 8,
                Analysis = new LichessAnalysisDto
                {
                    Inaccuracy = 2,
                    Mistake = 1,
                    Blunder = 0,
                    Acpl = 18,
                    Accuracy = 93
                }
            },
            Black = new LichessPlayerSideDto
            {
                User = new LichessUserDto { Id = "opponent", Name = "Opponent" },
                Rating = 1480,
                RatingDiff = -8,
                Analysis = new LichessAnalysisDto
                {
                    Inaccuracy = 3,
                    Mistake = 2,
                    Blunder = 1,
                    Acpl = 45,
                    Accuracy = 78
                }
            }
        },
        Winner = "white"
    };

    private static LichessGameDto CreateGameDtoWithoutAnalysis() => new()
    {
        Id = "test1234",
        Rated = true,
        Speed = "blitz",
        Status = "mate",
        CreatedAt = 1700000000000,
        LastMoveAt = 1700000600000,
        Players = new LichessPlayersDto
        {
            White = new LichessPlayerSideDto
            {
                User = new LichessUserDto { Id = "testplayer", Name = "TestPlayer" },
                Rating = 1500,
                RatingDiff = 8
            },
            Black = new LichessPlayerSideDto
            {
                User = new LichessUserDto { Id = "opponent", Name = "Opponent" },
                Rating = 1480,
                RatingDiff = -8
            }
        },
        Winner = "white"
    };

    [Fact]
    public async Task BackfillService_GameWithoutAnalysis_FetchesAndInserts()
    {
        var (_, _, gameId) = await SeedGameWithoutAnalysisAsync();

        _mockGameFetcher
            .Setup(f => f.FetchGameByIdAsync("test1234", It.IsAny<CancellationToken>()))
            .ReturnsAsync(CreateGameDtoWithAnalysis());

        await _service.BackfillAsync(CancellationToken.None);

        var db = CreateDb();
        var analysis = await db.GameAnalyses.FirstOrDefaultAsync(a => a.GameId == gameId);

        Assert.NotNull(analysis);
        Assert.Equal(2, analysis.InaccuracyCnt);
        Assert.Equal(1, analysis.MistakeCnt);
        Assert.Equal(0, analysis.BlunderCnt);
        Assert.Equal(18, analysis.Acpl);
        Assert.Equal(93, analysis.Accuracy);
    }

    [Fact]
    public async Task BackfillService_GameAlreadyHasAnalysis_Skips()
    {
        var (_, _, gameId) = await SeedGameWithoutAnalysisAsync();

        var db = CreateDb();
        db.GameAnalyses.Add(new GameAnalysis
        {
            GameId = gameId,
            InaccuracyCnt = 5,
            MistakeCnt = 3,
            BlunderCnt = 1,
            Acpl = 40,
            Accuracy = 80
        });
        await db.SaveChangesAsync();

        await _service.BackfillAsync(CancellationToken.None);

        _mockGameFetcher.Verify(
            f => f.FetchGameByIdAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task BackfillService_LichessReturnsNoAnalysis_SkipsGracefully()
    {
        await SeedGameWithoutAnalysisAsync();

        _mockGameFetcher
            .Setup(f => f.FetchGameByIdAsync("test1234", It.IsAny<CancellationToken>()))
            .ReturnsAsync(CreateGameDtoWithoutAnalysis());

        await _service.BackfillAsync(CancellationToken.None);

        var db = CreateDb();
        Assert.Empty(await db.GameAnalyses.ToListAsync());
    }

    [Fact]
    public async Task BackfillService_FetchFails_ContinuesWithNextGame()
    {
        await SeedGameWithoutAnalysisAsync();

        _mockGameFetcher
            .Setup(f => f.FetchGameByIdAsync("test1234", It.IsAny<CancellationToken>()))
            .ThrowsAsync(new HttpRequestException("Network error"));

        await _service.BackfillAsync(CancellationToken.None);

        var db = CreateDb();
        Assert.Empty(await db.GameAnalyses.ToListAsync());
    }

    [Fact]
    public async Task ExecuteAsync_RunsBackfillThenStopsOnCancel()
    {
        var (_, _, gameId) = await SeedGameWithoutAnalysisAsync();

        _mockGameFetcher
            .Setup(f => f.FetchGameByIdAsync("test1234", It.IsAny<CancellationToken>()))
            .ReturnsAsync(CreateGameDtoWithAnalysis());

        var testableService = new TestableBackfillService(
            _serviceProvider,
            Mock.Of<ILogger<AnalysisBackfillService>>());

        using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(500));

        try
        {
            await testableService.RunAsync(cts.Token);
        }
        catch (OperationCanceledException) { }

        var db = CreateDb();
        var analysis = await db.GameAnalyses.FirstOrDefaultAsync(a => a.GameId == gameId);
        Assert.NotNull(analysis);
        Assert.Equal(93, analysis.Accuracy);
    }

    [Fact]
    public async Task ExecuteAsync_ImmediateCancellation_NeverCallsBackfill()
    {
        await SeedGameWithoutAnalysisAsync();

        var testableService = new TestableBackfillService(
            _serviceProvider,
            Mock.Of<ILogger<AnalysisBackfillService>>());

        using var cts = new CancellationTokenSource();
        cts.Cancel();

        await testableService.RunAsync(cts.Token);

        _mockGameFetcher.Verify(
            f => f.FetchGameByIdAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    public void Dispose()
    {
        _serviceProvider.Dispose();
    }
}

internal class TestableBackfillService(
    IServiceProvider serviceProvider,
    ILogger<AnalysisBackfillService> logger)
    : AnalysisBackfillService(serviceProvider, logger)
{
    public Task RunAsync(CancellationToken ct) => ExecuteAsync(ct);
}
