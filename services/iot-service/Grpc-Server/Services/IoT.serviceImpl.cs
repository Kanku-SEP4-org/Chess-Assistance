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
        var latest = _stateStore.GetLatest(request.ArduinoId, "temp");
        
        if (latest == null)
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
                    Message = $"No temperature reading available yet for Arduino {request.ArduinoId}."
                }
            });
        }

        return Task.FromResult( new tempRes
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
                Message = $"Latest reading for Arduino {request.ArduinoId} retrieved successfully."
            }
        });
    }

    public override Task<ProtoStatus> startRecording(recReq request, ServerCallContext context)
    {
        return Task.FromResult(
            new ProtoStatus
            {
                Success = true,
                Message = $"Recording for Arduino {request.ArduinoId} started"
            }
        );
    }
    public override Task<ProtoStatus> stopRecording(recReq request, ServerCallContext context)
    {
        return Task.FromResult(
            new ProtoStatus
            {
                Success = true,
                Message = $"Recording for Arduino {request.ArduinoId} stopped"
            }
        );
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