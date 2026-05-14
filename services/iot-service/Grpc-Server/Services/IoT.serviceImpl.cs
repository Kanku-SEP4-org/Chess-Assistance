using Grpc.Core;
using IotService;
using IoTGrpcServer;
using IoTGrpcServer.Contracts;
using ProtoStatus = IotService.Status;

namespace Grpc_Server.Services;

public class IoTServiceImpl : iotService.iotServiceBase
{
    private readonly IIoTStateStore _stateStore;

    public IoTServiceImpl(IIoTStateStore stateStore)
    {
        _stateStore = stateStore;
    }

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


//private helper methods to quell repetition

    private sensorReading BuildReading(SensorState? state, sensorType defaultType)
    {
        return new sensorReading
        {
            Value = state?.Value ?? 0,
            // If state exists, map its string type to enum, otherwise use defaultType
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


}
