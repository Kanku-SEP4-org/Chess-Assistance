namespace PredictionService.grpc.Tests.TestDoubles;

internal sealed class SingleClientHttpClientFactory : IHttpClientFactory
{
    private readonly HttpClient _client;

    public SingleClientHttpClientFactory(HttpClient client)
    {
        _client = client;
    }

    public HttpClient CreateClient(string name) => _client;
}

