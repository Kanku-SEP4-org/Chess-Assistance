using System.Text.Json;
using Grpc.Core;
using Grpc.Core.Interceptors;

namespace GrpcService.Interceptors;

public class GlobalExceptionInterceptor : Interceptor
{
    private readonly ILogger<GlobalExceptionInterceptor> _logger;

    public GlobalExceptionInterceptor(ILogger<GlobalExceptionInterceptor> logger)
    {
        _logger = logger;
    }

    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try
        {
            return await continuation(request, context);
        }
        catch (RpcException)
        {
            throw;
        }
        catch (HttpRequestException e)
        {
            _logger.LogError(e, "Failed to reach downstream REST service");
            throw new RpcException(new Status(StatusCode.Unavailable,
                $"Could not connect to FastAPI: {e.Message}"));
        }
        catch (JsonException e)
        {
            _logger.LogError(e, "Failed to parse JSON response from downstream service");
            throw new RpcException(new Status(StatusCode.Internal,
                $"Invalid JSON from downstream service: {e.Message}"));
        }
        catch (Exception e)
        {
            _logger.LogError(e, "Unhandled exception in gRPC method {Method}", context.Method);
            throw new RpcException(new Status(StatusCode.Internal,
                $"Internal server error: {e.Message}"));
        }
    }
}
