using System.Net;
using System.Text.Json;
using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Lichess;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Unit;

public class LichessGameFetcherHttpTests
{
    private static LichessGameFetcher CreateFetcher(Func<HttpRequestMessage, HttpResponseMessage> handler)
    {
        var fakeHandler = new FakeHttpMessageHandler(handler);
        var httpClient = new HttpClient(fakeHandler)
        {
            BaseAddress = new Uri("https://lichess.org")
        };

        var mockFactory = new Mock<IHttpClientFactory>();
        mockFactory.Setup(f => f.CreateClient("Lichess")).Returns(httpClient);

        return new LichessGameFetcher(mockFactory.Object);
    }

    private static string SampleGameJson(string id = "abc12345") => JsonSerializer.Serialize(new
    {
        id,
        rated = true,
        speed = "blitz",
        status = "mate",
        createdAt = 1700000000000L,
        lastMoveAt = 1700000600000L,
        players = new
        {
            white = new { user = new { id = "testplayer", name = "TestPlayer" }, rating = 1500 },
            black = new { user = new { id = "opponent", name = "Opponent" }, rating = 1480 }
        },
        winner = "white"
    });

    // --- FetchLatestGameAsync ---

    [Fact]
    public async Task FetchLatestGameAsync_ValidNdjson_ReturnsDto()
    {
        HttpRequestMessage? captured = null;
        var fetcher = CreateFetcher(req =>
        {
            captured = req;
            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(SampleGameJson())
            };
        });

        var result = await fetcher.FetchLatestGameAsync("testplayer", "tok_123");

        Assert.NotNull(result);
        Assert.Equal("abc12345", result.Id);
        Assert.NotNull(captured);
        Assert.Contains("/api/games/user/testplayer", captured.RequestUri!.ToString());
        Assert.Equal("Bearer", captured.Headers.Authorization?.Scheme);
        Assert.Equal("tok_123", captured.Headers.Authorization?.Parameter);
    }

    [Fact]
    public async Task FetchLatestGameAsync_EmptyBody_ReturnsNull()
    {
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("")
        });

        var result = await fetcher.FetchLatestGameAsync("testplayer", "tok_123");

        Assert.Null(result);
    }

    [Fact]
    public async Task FetchLatestGameAsync_WhitespaceOnly_ReturnsNull()
    {
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("\n\n")
        });

        var result = await fetcher.FetchLatestGameAsync("testplayer", "tok_123");

        Assert.Null(result);
    }

    [Fact]
    public async Task FetchLatestGameAsync_MultipleLines_ReturnsFirst()
    {
        var body = SampleGameJson("game1") + "\n" + SampleGameJson("game2");
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(body)
        });

        var result = await fetcher.FetchLatestGameAsync("testplayer", "tok_123");

        Assert.NotNull(result);
        Assert.Equal("game1", result.Id);
    }

    [Fact]
    public async Task FetchLatestGameAsync_ServerError_Throws()
    {
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.InternalServerError));

        await Assert.ThrowsAsync<HttpRequestException>(
            () => fetcher.FetchLatestGameAsync("testplayer", "tok_123"));
    }

    // --- FetchGameByIdAsync ---

    [Fact]
    public async Task FetchGameByIdAsync_ValidJson_ReturnsDto()
    {
        HttpRequestMessage? captured = null;
        var fetcher = CreateFetcher(req =>
        {
            captured = req;
            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(SampleGameJson())
            };
        });

        var result = await fetcher.FetchGameByIdAsync("abc12345");

        Assert.NotNull(result);
        Assert.Equal("abc12345", result.Id);
        Assert.NotNull(captured);
        Assert.Contains("/game/export/abc12345", captured.RequestUri!.ToString());
    }

    [Fact]
    public async Task FetchGameByIdAsync_EmptyBody_ReturnsNull()
    {
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("")
        });

        var result = await fetcher.FetchGameByIdAsync("abc12345");

        Assert.Null(result);
    }

    [Fact]
    public async Task FetchGameByIdAsync_ServerError_Throws()
    {
        var fetcher = CreateFetcher(_ => new HttpResponseMessage(HttpStatusCode.InternalServerError));

        await Assert.ThrowsAsync<HttpRequestException>(
            () => fetcher.FetchGameByIdAsync("abc12345"));
    }

    private class FakeHttpMessageHandler(
        Func<HttpRequestMessage, HttpResponseMessage> handler) : DelegatingHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return Task.FromResult(handler(request));
        }
    }
}
