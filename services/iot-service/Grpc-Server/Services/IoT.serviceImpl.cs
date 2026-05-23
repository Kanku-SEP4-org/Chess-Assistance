using Grpc_Server.Messaging;
using Grpc.Core;
using IotService;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using ProtoStatus = IotService.Status;

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
            await _messageQueue.EnqueueObjectAsync(command);

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


}
