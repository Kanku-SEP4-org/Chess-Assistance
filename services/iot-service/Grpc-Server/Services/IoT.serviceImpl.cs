using Grpc.Core;
using IotService;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using ProtoStatus = IotService.Status;
using Grpc_Server.Messaging;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly IIoTStateStore _stateStore;
    private readonly IMessageQueue _messageQueue;

    public IoTServiceImpl(IIoTStateStore stateStore, IMessageQueue messageQueue)
    {
        _stateStore = stateStore;
        _messageQueue = messageQueue;//for sending commands
    }

    //SENSOR READINGS
    public override async Task<tempRes> getTemperature(tempReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, sensorType.Temp);

        return new tempRes()
        {
            Reading = BuildReading(latest, sensorType.Temp),
            Status = BuildStatus(latest, "temperature", request.ArduinoId)
        };
    }
    public override async Task<lightRes> getLight(lightReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, sensorType.Light);

        return new lightRes()
        {
            Reading = BuildReading(latest, sensorType.Light),
            Status = BuildStatus(latest, "light", request.ArduinoId)
        };
    }

    public override async Task<waterLevelRes> getWaterLevel(waterLevelReq request, ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, sensorType.Water);

        return new waterLevelRes
        {
            Reading = BuildReading(latest, sensorType.Water),
            Status = BuildStatus(latest, "water level", request.ArduinoId)
        };
    }

    //COMMANDS
    public override async Task<fillCupRes> fillCup(fillCupReq request, ServerCallContext context)
    {
        var payload = new {
            Action = "Fill"
        };

        var status = await SendCommandAsync(request.ArduinoId, sensorType.Pump, payload);

        if (!status.Success)
        {
            return new fillCupRes { Status = status };
        }

        // pump works for 2s, including small communication delays we give it a grace period
        // waiting 3s for a response
        Thread.Sleep(3000);

        var pump = _stateStore.GetLatest(request.ArduinoId, sensorType.Pump);

        return new fillCupRes { 
            Reading = BuildReading(pump, sensorType.Pump),
            Status = BuildStatus(pump, "water pump", request.ArduinoId)
        };
    }

    public override Task<co2Res> getCO2(co2Req request,
        ServerCallContext context)
    {
        var latest = _stateStore.GetLatest(request.ArduinoId, sensorType.Co2);

        if (latest == null)
        {
            return Task.FromResult(new co2Res
            {
                Reading = new sensorReading
                {
                    Value = 0,
                    Type = sensorType.Co2,
                    Timestamp = 0
                },
                Status = new ProtoStatus
                {
                    Success = false,
                    Message =
                        $"No CO2 reading available yet for Arduino {request.ArduinoId}."
                }
            });
        }

        return Task.FromResult(new co2Res
        {
            Reading = new sensorReading
            {
                Value = latest.Value,
                Type = latest.Type,
                Timestamp = latest.Timestamp
            },
            Status = new ProtoStatus
            {
                Success = true,
                Message =
                    $"Latest CO2 reading for Arduino {request.ArduinoId} retrieved successfully."
            }
        });
    }



// HELPER methods

    private sensorReading BuildReading(SensorState? state, sensorType defaultType)
    {
        return new sensorReading
        {
            Value = state?.Value ?? 0,
            // If state exists, map its string type to enum, otherwise use defaultType (Error)
            Type = state?.Type ?? defaultType,
            Timestamp = state?.Timestamp ?? 0
        };
    }

    private ProtoStatus BuildStatus(SensorState? state, string sensorName, int id)
    {
        bool exists = state != null;
        return new ProtoStatus
        {
            Success = exists,
            Message = exists
                ? $"Latest {sensorName} reading for Arduino {id} retrieved successfully."
                : $"No {sensorName} reading available yet for Arduino {id}."
        };
    }

    private async Task<ProtoStatus> SendCommandAsync(int id, sensorType type, object data)
    {
        try
        {
            // Standardized command envelope
            var command = new {
                ArduinoId = id,
                Type = type, // Use the Enum
                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                Payload = data
            };

            // One single place where we talk to RabbitMQ
            await _messageQueue.EnqueueObjectAsync( command);

            return new ProtoStatus {
                Success = true,
                Message = $"Command {type} successfully queued for Arduino {id}."
            };
        }
        catch (Exception ex)
        {
            // Centralized error handling for all commands
            return new ProtoStatus {
                Success = false,
                Message = $"Failed to dispatch {type} command: {ex.Message}"
            };
        }
    }


    public override Task<ProtoStatus> startRecording(recReq request, ServerCallContext context)
    {
        var sensors = _stateStore.Record(request.ArduinoId);
        if(sensors != null || !sensors.Any())
        {
            return Task.FromResult(
                new ProtoStatus
                {
                    Success = true,
                    Message = $"Recording for Arduino {request.ArduinoId} started"
                }
            );
        }
        else
        {
            return Task.FromResult(
                new ProtoStatus
                {
                    Success = false,
                    Message = $"Recording for Arduino {request.ArduinoId} failed"
                }
            );
        }
    }
    public override Task<ProtoStatus> stopRecording(recReq request, ServerCallContext context)
    {
        var sensors = _stateStore.StopRecord(request.ArduinoId);
        if(sensors != null || !sensors.Any())
        {
            return Task.FromResult(
                new ProtoStatus
                {
                    Success = true,
                    Message = $"Recording for Arduino {request.ArduinoId} stopped"
                }
            );
        }
        else
        {
            return Task.FromResult(
                new ProtoStatus
                {
                    Success = false,
                    Message = $"Recording for Arduino {request.ArduinoId} stop failed"
                }
            );
        }


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
