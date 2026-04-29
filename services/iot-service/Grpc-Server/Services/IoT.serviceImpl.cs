using Grpc.Core;
using IotService;
using IoTGrpcServer;
using ProtoStatus = IotService.Status;
using Grpc_Server.Messaging;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly IoTStateStore _stateStore;
    private readonly IMessageQueue _messageQueue;

    public IoTServiceImpl(IoTStateStore stateStore, IMessageQueue messageQueue)
    {
        _stateStore = stateStore;
        _messageQueue = messageQueue;
    }

    public override async Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        //await _messageQueue.EnqueueAsync([]);
        await _messageQueue.DequeueObjectAsync();

        var latest = _stateStore.GetLatest();

        if (!latest.HasValue)
        {
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
                    Message = "No sensor reading available yet."
                }
            };
        }

        return new tempRes
        {
            Reading = new sensorReading
            {
                Value = latest.Value,
                Type = MapSensorType(latest.Type),
                Timestamp = latest.Timestamp
            },
            Status = new ProtoStatus
            {
                Success = true,
                Message = $"Latest reading for Arduino {request.ArduinoId} retrieved successfully."
            }
        };
    }

    private static sensorType MapSensorType(string type)
    {
        return type.ToLower() switch
        {
            "temp" => sensorType.Temp,
            _ => sensorType.Temp
        };
    }
}