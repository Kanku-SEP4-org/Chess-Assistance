using Grpc.Core;
using IotService;
using IoTGrpcServer;
using ProtoStatus = IotService.Status;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly IoTStateStore _stateStore;

    public IoTServiceImpl(IoTStateStore stateStore)
    {
        _stateStore = stateStore;
    }

    public override Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest();

        if (!latest.HasValue)
        {
            return Task.FromResult(new tempRes
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
                    Message = "No temperature reading available yet."
                }
            });
        }

        return Task.FromResult(new tempRes
        {
            Reading = new sensorReading
            {
                Value = latest.Value,
                Type = sensorType.Temp,
                Timestamp = latest.Timestamp
            },
            Status = new ProtoStatus
            {
                Success = true,
                Message = $"Latest temperature for Arduino {request.ArduinoId} retrieved successfully."
            }
        });
    }
}