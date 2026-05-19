using Grpc.Core;
using Grpc.Core.Testing;

namespace PredictionService.grpc.Tests.TestHelpers;

internal static class TestServerCallContextFactory
{
    public static ServerCallContext Create(
        string method = "test/method",
        string host = "localhost",
        DateTime? deadline = null,
        CancellationToken cancellationToken = default)
    {
        return TestServerCallContext.Create(
            method: method,
            host: host,
            deadline: deadline ?? DateTime.UtcNow.AddMinutes(1),
            requestHeaders: new Metadata(),
            cancellationToken: cancellationToken,
            peer: "127.0.0.1",
            authContext: new AuthContext("transport_security_type", new Dictionary<string, List<AuthProperty>>()),
            contextPropagationToken: null,
            writeHeadersFunc: _ => Task.CompletedTask,
            writeOptionsGetter: () => new WriteOptions(),
            writeOptionsSetter: _ => { });
    }
}

