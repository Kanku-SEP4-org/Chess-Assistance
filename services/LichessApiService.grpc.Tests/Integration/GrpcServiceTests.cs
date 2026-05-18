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

    private static StartSessionRequest CreateValidRequest(int playerId = 1) => new()
    {
        PlayerId = playerId,
        PlayerUsername = "testplayer",
        LichessToken = "lip_test_token_123",
        SleepTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-9)),
        AwakenTime = Timestamp.FromDateTime(DateTime.UtcNow.AddHours(-1.5)),
        ConfirmedAt = Timestamp.FromDateTime(DateTime.UtcNow.AddMinutes(-5))
    };

    // --- StartSession: core flow ---

    [Fact]
    public async Task StartSession_ValidRequest_CreatesSessionAndHealthRecord()
    {
        var request = CreateValidRequest();

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.True(response.Success);
        Assert.True(response.SessionId > 0);

        var session = await _db.Sessions.FindAsync(response.SessionId);
        Assert.NotNull(session);
        Assert.Equal(1, session.PlayerId);
        Assert.Null(session.EndedAt);

        var sleepRecord = await _db.HealthRecords.FirstOrDefaultAsync(s => s.SessionId == response.SessionId);
        Assert.NotNull(sleepRecord);
        Assert.Equal(request.SleepTime.ToDateTime(), sleepRecord.SleepTime);
        Assert.Equal(request.AwakenTime.ToDateTime(), sleepRecord.AwakenTime);
        Assert.Equal(request.ConfirmedAt.ToDateTime(), sleepRecord.ConfirmedAt);
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
        var request = CreateValidRequest();
        request.SleepTime = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("sleep_time", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingAwakenTime_ReturnsFalse()
    {
        var request = CreateValidRequest();
        request.AwakenTime = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("awaken_time", response.Message);
    }

    [Fact]
    public async Task StartSession_MissingConfirmedAt_ReturnsFalse()
    {
        var request = CreateValidRequest();
        request.ConfirmedAt = null;

        var response = await _service.StartSession(request, CreateTestContext());

        Assert.False(response.Success);
        Assert.Contains("confirmed_at", response.Message);
    }

    [Fact]
    public async Task StartSession_AwakenBeforeSleep_ReturnsFalse()
    {
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
        _db.Sessions.Add(new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-10),
            PlayerId = 1
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
    public async Task EndSession_ValidSession_SetsEndedAt()
    {
        var session = new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-10),
            PlayerId = 1
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
        _db.Sessions.Add(new Session
        {
            StartedAt = DateTime.UtcNow.AddMinutes(-30),
            EndedAt = DateTime.UtcNow.AddMinutes(-5),
            PlayerId = 1
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
