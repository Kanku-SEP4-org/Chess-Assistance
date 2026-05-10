using System.Collections.Concurrent;
using IoTGrpcServer.Contracts;

namespace IoTGrpcServer;

public class IoTStateStore
{
    private readonly ConcurrentDictionary<SensorKey, SensorState> _states = new();
    public void Update(int arduinoId, float value, long timestamp, string type)
    {
        var normalizedType = type.Trim().ToLowerInvariant();

        var key = new SensorKey
        {
            ArduinoId = arduinoId,
            Type = normalizedType
        };

        _states[key] = new SensorState
        {
            ArduinoId = arduinoId,
            Value = value,
            Timestamp = timestamp,
            Type = type
        };
    }

    public SensorState? GetLatest(int arduinoId, string type) // a little cleaner this way, bc the get latest return the sensorstate directly
    {
        var normalizedType = type.Trim().ToLowerInvariant();
        var key = new SensorKey
        {
            ArduinoId = arduinoId,
            Type = normalizedType
        };

        if (_states.TryGetValue(key, out var state))
        {
            return state;
        }        
            return null;
        
    }
}

