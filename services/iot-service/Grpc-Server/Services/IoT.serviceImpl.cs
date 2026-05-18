using Grpc.Core;
using IotService;
using IoTGrpcServer;
using ProtoStatus = IotService.Status;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly IIoTStateStore _stateStore;

    public IoTServiceImpl(IIoTStateStore stateStore)
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
    public override async Task<lightRes> getLight(lightReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, "light");

        if (latest == null)
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

    public override async Task<waterLevelRes> getWaterLevel(waterLevelReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, "water");

        if (latest == null)
        {
            return new waterLevelRes
            {
                Reading = new sensorReading
                {
                    Value = 0,
                    Type = sensorType.Water,
                    Timestamp = 0
                },
                Status = new ProtoStatus
                {
                    Success = false,
                    Message = "No sensor reading available yet."
                }
            };
        }

        return new waterLevelRes
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

    public override Task<ProtoStatus> startRecording(recReq request, ServerCallContext context)
    {
        //TODO: error handling
        _stateStore.Record(request.ArduinoId, true);

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
        //TODO: error handling
        _stateStore.Record(request.ArduinoId, false);

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
            "light" => sensorType.Light,
            "water" => sensorType.Water,
            _ => sensorType.Error // default case, should not happen if we control the input types properly
            //!!! all cases must be added lowercase in declaration too, so the unit tests pass without a hitch
            //in the methods, camelcase must match the proto enum
        };
    }
}
