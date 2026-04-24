using Grpc.Core;
using IotService;
using IoTGrpcServer;
using ProtoStatus = IotService.Status;
using Grpc_Server.Messaging;
using System.Text;

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

    public override Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        // We need to change 
        _messageQueue.DequeueObjectAsync();
        _messageQueue.EnqueueAsync(Encoding.UTF8.GetBytes("test"));
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