using Grpc.Core;
using IotService;
using ProtoStatus = IotService.Status;

namespace GrpcService.Services;

public class IoTProxyServiceImpl : iotService.iotServiceBase
{
    private readonly iotService.iotServiceClient _iotClient;

    public IoTProxyServiceImpl(iotService.iotServiceClient iotClient)
    {
        _iotClient = iotClient;
    }

    public override async Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        try
        {
            return await _iotClient.getTemperatureAsync(request);
        }
        catch (RpcException ex)
        {
            // Mirror the JS fallback: return a response with success=false instead of throwing,
            // so the API gateway can handle it gracefully and fall back to a default temperature
            return new tempRes
            {
                Reading = new sensorReading
                {
                    Value = 0,
                    Type = sensorType.Temp,
                    Timestamp = 0
                },
                Status = new ProtoStatus
                {
                    Success = false,
                    Message = ex.Message
                }
            };
        }
    }
}
