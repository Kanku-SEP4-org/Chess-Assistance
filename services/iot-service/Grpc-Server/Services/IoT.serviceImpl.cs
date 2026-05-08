using Grpc.Core;
using IotService;
using IoTGrpcServer;
using ProtoStatus = IotService.Status;
using Grpc_Server.Messaging;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly TemperatureStateStore _temperatureStateStore;
    private readonly LightStateStore _lightStateStore;
    private readonly IMessageQueue _messageQueue;

    public IoTServiceImpl(TemperatureStateStore temperatureStateStore,LightStateStore lightStateStore, IMessageQueue messageQueue)
    {
        _temperatureStateStore = temperatureStateStore;
        _lightStateStore = lightStateStore;
        _messageQueue = messageQueue;
    }

    public override async Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        //await _messageQueue.EnqueueAsync([]);
        await _messageQueue.DequeueObjectAsync();

        var latest = _temperatureStateStore.GetLatest();

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
    public override async Task<lightRes> getLight(lightReq request, ServerCallContext context)
    {
        await _messageQueue.DequeueObjectAsync();

        var latest = _lightStateStore.GetLatest();

        if (!latest.HasValue)
        {
            return new lightRes
            {
                Reading = new sensorReading
                {
                    Value = 0,
                    Type = sensorType.Light,
                    Timestamp = 0
                },
                Status = new ProtoStatus
                {
                    Success = false,
                    Message = "No sensor reading available yet."
                }
            };
        }

        return new lightRes
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
            "light" => sensorType.Light,
            _ => sensorType.Temp
        };
    }
}