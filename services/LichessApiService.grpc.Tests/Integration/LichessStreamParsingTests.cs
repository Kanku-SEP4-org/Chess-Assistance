using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Protos;
using LichessApiService.Grpc.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Integration;

public class LichessStreamParsingTests : IDisposable
{
    private readonly ServiceProvider _serviceProvider;
    private readonly LichessStreamService _streamService;
    private readonly Mock<LichessApiClient> _mockIotClient;
    private readonly Mock<LichessGameFetcher> _mockGameFetcher;
    private readonly string _dbName = Guid.NewGuid().ToString();

    public LichessStreamParsingTests()
    {
        var mockHttpFactory = new Mock<IHttpClientFactory>();
        var mockGrpcClient = new Mock<SensorFeedService.SensorFeedServiceClient>();

        _mockIotClient = new Mock<LichessApiClient>(
            mockGrpcClient.Object, Mock.Of<ILogger<LichessApiClient>>());
        _mockIotClient.Setup(c => c.StartSensorFeedAsync(It.IsAny<int>())).Returns(Task.CompletedTask);
        _mockIotClient.Setup(c => c.StopSensorFeedAsync(It.IsAny<int>())).Returns(Task.CompletedTask);

        _mockGameFetcher = new Mock<LichessGameFetcher>(mockHttpFactory.Object);
        _mockGameFetcher
            .Setup(f => f.FetchLatestGameAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(CreateSampleLichessGame());
        _mockGameFetcher
            .Setup(f => f.MapToGameEntity(It.IsAny<LichessGameDto>(), It.IsAny<string>(), It.IsAny<int>()))
            .Returns((LichessGameDto dto, string username, int matchId) => new Game
            {
                LichessGameId = dto.Id,
                TimeControl = TimeControlType.Blitz,
                Result = GameResultType.Win,
                MatchId = matchId
            });

        var services = new ServiceCollection();
        services.AddDbContext<LichessDbContext>(options =>
            options.UseInMemoryDatabase(_dbName));
        services.AddScoped(_ => _mockIotClient.Object);
        services.AddScoped(_ => _mockGameFetcher.Object);

        _serviceProvider = services.BuildServiceProvider();

        _streamService = new LichessStreamService(
            mockHttpFactory.Object,
            _serviceProvider,
            Mock.Of<ILogger<LichessStreamService>>());
    }

    private LichessDbContext CreateDb() =>
        _serviceProvider.CreateScope().ServiceProvider.GetRequiredService<LichessDbContext>();

    private async Task<int> SeedSessionAsync()
    {
        var db = CreateDb();
        var session = new Session { StartedAt = DateTime.UtcNow, PlayerId = 1 };
        db.Sessions.Add(session);
        await db.SaveChangesAsync();
        return session.Id;
    }

    private static LichessGameDto CreateSampleLichessGame() => new()
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
                Rating = 1500, RatingDiff = 8
            },
            Black = new LichessPlayerSideDto
            {
                User = new LichessUserDto { Id = "opponent", Name = "Opponent" },
                Rating = 1480, RatingDiff = -8
            }
        },
        Winner = "white",
        Moves = "e4 e5 Nf3 Nc6"
    };

    // --- Stream parsing tests ---

    [Fact]
    public async Task GameStart_CreatesMatchInDb()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"gameStart","game":{"gameId":"abc12345","fullId":"abc12345xxxx","color":"white"}}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        var matches = await db.Matches.Where(m => m.SessionId == sessionId).ToListAsync();

        Assert.Single(matches);
        Assert.Equal(SessionStatus.Pending, matches[0].Status);
        Assert.Equal(1, matches[0].PlayerId);
    }

    [Fact]
    public async Task GameStart_CallsIoTStartSensorFeed()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"gameStart","game":{"gameId":"abc12345"}}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        _mockIotClient.Verify(c => c.StartSensorFeedAsync(It.IsAny<int>()), Times.Once);
    }

    [Fact]
    public async Task GameFinish_AfterGameStart_InsertsGameAndCallsIoTStop()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"gameStart","game":{"gameId":"abc12345"}}
            {"type":"gameFinish","game":{"gameId":"abc12345"}}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        var games = await db.Games.ToListAsync();

        Assert.Single(games);
        Assert.Equal("test1234", games[0].LichessGameId);

        _mockIotClient.Verify(c => c.StopSensorFeedAsync(It.IsAny<int>()), Times.Once);
        _mockGameFetcher.Verify(
            f => f.FetchLatestGameAsync("testplayer", "fake_token", It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task GameFinish_WithoutPriorGameStart_IsIgnored()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"gameFinish","game":{"gameId":"abc12345"}}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        Assert.Empty(await db.Games.ToListAsync());
        Assert.Empty(await db.Matches.ToListAsync());

        _mockIotClient.Verify(c => c.StopSensorFeedAsync(It.IsAny<int>()), Times.Never);
    }

    [Fact]
    public async Task BlankLines_AreSkipped()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = "\n\n   \n{"
            + "\"type\":\"gameStart\",\"game\":{\"gameId\":\"abc12345\"}}\n\n";
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        Assert.Single(await db.Matches.Where(m => m.SessionId == sessionId).ToListAsync());
    }

    [Fact]
    public async Task MalformedJson_IsSkippedWithoutCrash()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            not valid json at all
            {"type":"gameStart","game":{"gameId":"abc12345"}}
            {broken json{{{
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        Assert.Single(await db.Matches.Where(m => m.SessionId == sessionId).ToListAsync());
    }

    [Fact]
    public async Task UnknownEventType_IsIgnored()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"challenge","challenge":{"id":"xyz"}}
            {"type":"challengeDeclined"}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        Assert.Empty(await db.Matches.ToListAsync());
    }

    [Fact]
    public async Task MultipleGames_InOneSession_CreatesMultipleMatches()
    {
        var sessionId = await SeedSessionAsync();

        var ndjson = """
            {"type":"gameStart","game":{"gameId":"game1"}}
            {"type":"gameFinish","game":{"gameId":"game1"}}
            {"type":"gameStart","game":{"gameId":"game2"}}
            {"type":"gameFinish","game":{"gameId":"game2"}}
            """;
        using var reader = new StringReader(ndjson);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", CancellationToken.None);

        var db = CreateDb();
        var matches = await db.Matches.Where(m => m.SessionId == sessionId).ToListAsync();
        var games = await db.Games.ToListAsync();

        Assert.Equal(2, matches.Count);
        Assert.Equal(2, games.Count);

        _mockIotClient.Verify(c => c.StartSensorFeedAsync(It.IsAny<int>()), Times.Exactly(2));
        _mockIotClient.Verify(c => c.StopSensorFeedAsync(It.IsAny<int>()), Times.Exactly(2));
    }

    [Fact]
    public async Task CancellationToken_StopsProcessing()
    {
        var sessionId = await SeedSessionAsync();

        var cts = new CancellationTokenSource();

        // Create a reader that cancels after first line is read
        var ndjson = """
            {"type":"gameStart","game":{"gameId":"game1"}}
            {"type":"gameStart","game":{"gameId":"game2"}}
            """;
        using var reader = new CancellingReader(ndjson, cts, cancelAfterLine: 1);

        await _streamService.ProcessStreamAsync(
            reader, sessionId, playerId: 1, "testplayer", "fake_token", cts.Token);

        var db = CreateDb();
        var matches = await db.Matches.Where(m => m.SessionId == sessionId).ToListAsync();

        Assert.Single(matches);
    }

    public void Dispose()
    {
        _serviceProvider.Dispose();
    }
}

internal class CancellingReader(string content, CancellationTokenSource cts, int cancelAfterLine) : StringReader(content)
{
    private int _linesRead;

    public override ValueTask<string?> ReadLineAsync(CancellationToken cancellationToken = default)
    {
        if (_linesRead >= cancelAfterLine)
        {
            cts.Cancel();
            cancellationToken.ThrowIfCancellationRequested();
        }

        var line = base.ReadLine();
        if (line != null && !string.IsNullOrWhiteSpace(line))
            _linesRead++;

        return new ValueTask<string?>(line);
    }
}
