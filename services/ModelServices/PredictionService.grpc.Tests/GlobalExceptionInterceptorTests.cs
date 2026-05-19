using System.Text.Json;
using Grpc.Core;
using Microsoft.Extensions.Logging.Abstractions;
using PredictionService.grpc.Interceptors;
using PredictionService.grpc.Tests.TestHelpers;
using Xunit;

namespace PredictionService.grpc.Tests;

public class GlobalExceptionInterceptorTests
{
    [Fact]
    public async Task UnaryServerHandler_WhenHttpRequestException_MapsToUnavailable()
    {
        var interceptor = new GlobalExceptionInterceptor(new NullLogger<GlobalExceptionInterceptor>());
        var context = TestServerCallContextFactory.Create();

        async Task<string> Continuation(string _, ServerCallContext __)
        {
            await Task.Yield();
            throw new HttpRequestException("downstream unreachable");
        }

        var ex = await Assert.ThrowsAsync<RpcException>(() =>
            interceptor.UnaryServerHandler("req", context, Continuation));

        Assert.Equal(StatusCode.Unavailable, ex.StatusCode);
    }

    [Fact]
    public async Task UnaryServerHandler_WhenJsonException_MapsToInternal()
    {
        var interceptor = new GlobalExceptionInterceptor(new NullLogger<GlobalExceptionInterceptor>());
        var context = TestServerCallContextFactory.Create();

        async Task<string> Continuation(string _, ServerCallContext __)
        {
            await Task.Yield();
            throw new JsonException("bad json");
        }

        var ex = await Assert.ThrowsAsync<RpcException>(() =>
            interceptor.UnaryServerHandler("req", context, Continuation));

        Assert.Equal(StatusCode.Internal, ex.StatusCode);
    }
}
