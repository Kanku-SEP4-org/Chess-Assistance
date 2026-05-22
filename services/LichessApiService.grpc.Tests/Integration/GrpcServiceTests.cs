using Google.Protobuf.WellKnownTypes;
using Grpc.Core;
using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Protos;
using LichessApiService.Grpc.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Integration;

public class GrpcServiceTests : IDisposable
{
    private readonly LichessDbContext _db;
    private readonly LichessApiGrpcService _service;

    public GrpcServiceTests()
    {
        // Use an in-memory SQLite database for testing.
        // PostgreSQL-specific features (enums) won't be exercised here,
        // but the core logic (insert/query/update) works fine.
        var options = new DbContextOptionsBuilder<LichessDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _db = new LichessDbContext(options);
        _db.Database.EnsureCreated();

        var mockStreamService = new Mock<LichessStreamService>(
            Mock.Of<IHttpClientFactory>(),
            Mock.Of<IServiceProvider>(),
            Mock.Of<ILogger<LichessStreamService>>());

        var logger = Mock.Of<ILogger<LichessApiGrpcService>>();

        _service = new LichessApiGrpcService(_db, mockStreamService.Object, logger);
    }

    private static ServerCallContext CreateTestContext() =>
        new FakeServerCallContext();

    private async Task<Player> SeedPlayerAsync(int id = 1)
    {
        var player = new Player
        {
            Id = id,
            LichessId = $"lichess_{id}",
            Username = "testplayer"
        };
        _db.Players.Add(player);
        await _db.SaveChangesAsync();
        return player;
    }

    private async Task<HealthRecord> SeedHealthRecordAsync(int playerId = 1)
    {
        var hr = new HealthRecord
        {
            SleepTime = DateTime.UtcNow.AddHours(-8),
            AwakenTime = DateTime.UtcNow.AddHours(-1),
            ConfirmedAt = DateTime.UtcNow.AddMinutes(-5),
            PlayerId = playerId
        };
        _db.HealthRecords.Add(hr);
        await _db.SaveChangesAsync();
        return hr;
    }

    private static StartSessionRequest CreateValidRequest(int playerId = 1) => new()
    {
        PlayerId = playerId,
        PlayerUsername = "testplayer",
        LichessToken = "lip_test_token_123",
        SleepTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-9)),
        AwakenTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-1.5)),
        ConfirmedAt = Timestamp.FromDateTime(DateTime.UtcNow.AddMinutes(-5)),
        WaterIntakeInitialMl = 500
    };

    // --- RegisterPlayer ---

    [Fact]
    public async Task RegisterPlayer_NewPlayer_CreatesAndReturnsIsNewTrue()
    {
        var request = new RegisterPlayerRequest
        {
            LichessId = "lichess123",
            Username = "testplayer"
        };

        var response = await _service.RegisterPlayer(request, CreateTestContext());

        Assert.True(response.IsNew);
        Assert.True(response.PlayerId > 0);

        var player = await _db.Players.FindAsync(response.PlayerId);
        Assert.NotNull(player);
        Assert.Equal("lichess123", player.LichessId);
        Assert.Equal("testplayer", player.Username);
    }

    [Fact]
    public async Task RegisterPlayer_ExistingPlayer_UpdatesUsernameAndReturnsIsNewFalse()
    {
        _db.Players.Add(new Player
        {
            LichessId = "lichess123",
            Username = "oldname"
        });
        await _db.SaveChangesAsync();

        var request = new RegisterPlayerRequest
        {
            LichessId = "lichess123",
            Username = "newname"
        };

        var response = await _service.RegisterPlayer(request, CreateTestContext());

        Assert.False(response.IsNew);

        var player = await _db.Players.FindAsync(response.PlayerId);
        Assert.NotNull(player);
        Assert.Equal("newname", player.Username);

        Assert.Equal(1, await _db.Players.CountAsync());
    }

    [Theory]
    [InlineData("", "testplayer")]
    [InlineData("lichess123", "")]
    [InlineData("", "")]
    [InlineData("  ", "testplayer")]
    public async Task RegisterPlayer_MissingFields_ThrowsInvalidArgument(
        string lichessId, string username)
    {
        var request = new RegisterPlayerRequest
        {
            LichessId = lichessId,
            Username = username
        };

        var ex = await Assert.ThrowsAsync<RpcException>(
            () => _service.RegisterPlayer(request, CreateTestContext()));

        Assert.Equal(StatusCode.InvalidArgument, ex.StatusCode);
    }

    // --- StartSession: core flow ---

    [Fact]
    public async Task StartSession_ValidRequest_CreatesSessionAndHealthRecord()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.True(response.Success);
        Assert.True(response.SessionId > 0);

        var session = await _db.Sessions.FindAsync(response.SessionId);
        Assert.NotNull(session);
        Assert.Equal(1, session.PlayerId);
        Assert.Null(session.EndedAt);

        Assert.True(session.HealthRecordId > 0);

        var healthRecord = await _db.HealthRecords.FindAsync(session.HealthRecordId);
        Assert.NotNull(healthRecord);
        Assert.Equal(1, healthRecord.PlayerId);
        Assert.Equal(request.SleepTime.ToDateTime(), healthRecord.SleepTime);
        Assert.Equal(request.AwakenTime.ToDateTime(), healthRecord.AwakenTime);
        Assert.Equal(request.ConfirmedAt.ToDateTime(), healthRecord.ConfirmedAt);
        Assert.Equal(500, healthRecord.WaterIntakeMl);
    }

    // --- StartSession: validation ---

    [Fact]
    public async Task StartSession_MissingUsername_ReturnsFalse()
    {
        var request = CreateValidRequest();
        request.PlayerUsername = "";

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("required", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingToken_ReturnsFalse()
    {
        var request = CreateValidRequest();
        request.LichessToken = "";

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("lichess_token", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingSleepTime_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();
        request.SleepTime = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("sleep_time", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingAwakenTime_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();
        request.AwakenTime = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("awaken_time", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingConfirmedAt_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();
        request.ConfirmedAt = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("confirmed_at", response.Message);
    }

    [Fact]
    public async Task StartSession_AwakenBeforeSleep_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();
        request.SleepTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-2));
        request.AwakenTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-5));

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("awaken_time must be after sleep_time", response.Message);
    }

    [Fact]
    public async Task StartSession_ConfirmedAtBeforeAwaken_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var request = CreateValidRequest();
        request.AwakenTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-1));
        request.ConfirmedAt = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-2));

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("confirmed_at must be after awaken_time", response.Message);
    }

    [Fact]
    public async Task StartSession_DuplicateActiveSession_ReturnsFalse()
    {
        await SeedPlayerAsync();
        var hr = await SeedHealthRecordAsync();
        _db.Sessions.Add(new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-10),
            PlayerId = 1,
            HealthRecordId = hr.Id
        });
        await _db.SaveChangesAsync();

        var request = CreateValidRequest();

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("active session", response.Message);
    }

    [Fact]
    public async Task StartSession_NoHealthRecordCreated_WhenValidationFails()
    {
        var request = CreateValidRequest();
        request.PlayerUsername = "";

        await _service.StartSession(request, CreateTestContext());

        Assert.Empty(await _db.Sessions.ToListAsync());
        Assert.Empty(await _db.HealthRecords.ToListAsync());
    }

    [Fact]
    public async Task StartSession_SecondSessionSameDay_ReusesHealthRecord()
    {
        await SeedPlayerAsync();
        var request1 = CreateValidRequest();
        var response1 = await _service.StartSession(request1, CreateTestContext());
        Assert.True(response1.Success);

        var session1 = await _db.Sessions.FindAsync(response1.SessionId);
        Assert.NotNull(session1);

        session1.EndedAt = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        var request2 = CreateValidRequest();
        request2.WaterIntakeInitialMl = 750;
        var response2 = await _service.StartSession(request2, CreateTestContext());
        Assert.True(response2.Success);

        var session2 = await _db.Sessions.FindAsync(response2.SessionId);
        Assert.NotNull(session2);

        Assert.Equal(session1.HealthRecordId, session2.HealthRecordId);

        var healthRecords = await _db.HealthRecords.ToListAsync();
        Assert.Single(healthRecords);
        Assert.Equal(750, healthRecords[0].WaterIntakeMl);
    }

    [Fact]
    public async Task EndSession_ValidSession_SetsEndedAt()
    {
        var hr = await SeedHealthRecordAsync();
        var session = new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-10),
            PlayerId = 1,
            HealthRecordId = hr.Id
        };
        _db.Sessions.Add(session);
        await _db.SaveChangesAsync();

        var response = await _service.EndSession(
            new EndSessionRequest { SessionId = session.Id },
            CreateTestContext());

        Assert.True(response.Success);

        var updated = await _db.Sessions.FindAsync(session.Id);
        Assert.NotNull(updated!.EndedAt);
    }

    [Fact]
    public async Task EndSession_NonexistentSession_ReturnsFalse()
    {
        var response = await _service.EndSession(
            new EndSessionRequest { SessionId = 9999 },
            CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("not found", response.Message);
    }

    [Fact]
    public async Task EndSession_AlreadyEnded_ReturnsFalse()
    {
        var hr = await SeedHealthRecordAsync();
        _db.Sessions.Add(new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-30),
            EndedAt = DateTime.UtcNow.AddMinutes(-5),
            PlayerId = 1,
            HealthRecordId = hr.Id
        });
        await _db.SaveChangesAsync();

        var session = await _db.Sessions.FirstAsync();

        var response = await _service.EndSession(
            new EndSessionRequest { SessionId = session.Id },
            CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("already ended", response.Message);
    }

    public void Dispose()
    {
        _db.Database.EnsureDeleted();
        _db.Dispose();
    }
}

internal class FakeServerCallContext : ServerCallContext
{
    protected override string MethodCore => "TestMethod";
    protected override string HostCore => "localhost";
    protected override string PeerCore => "test-peer";
    protected override DateTime DeadlineCore => DateTime.UtcNow.AddMinutes(5);
    protected override Metadata RequestHeadersCore => [];
    protected override CancellationToken CancellationTokenCore => CancellationToken.None;
    protected override Metadata ResponseTrailersCore => [];
    protected override Status StatusCore { get; set; }
    protected override WriteOptions? WriteOptionsCore { get; set; }
    protected override AuthContext AuthContextCore =>
        new(null, new Dictionary<string, List<AuthProperty>>());

    protected override ContextPropagationToken CreatePropagationTokenCore(ContextPropagationOptions? options) =>
        throw new NotImplementedException();

    protected override Task WriteResponseHeadersAsyncCore(Metadata responseHeaders) =>
        Task.CompletedTask;
}
