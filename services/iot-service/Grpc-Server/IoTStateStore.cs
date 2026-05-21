using System.Collections.Concurrent;
using IoTGrpcServer.Contracts;
using IotService;

namespace IoTGrpcServer;

public class IoTStateStore : IIoTStateStore
{
    private readonly ConcurrentDictionary<SensorKey, SensorState> _states = new();
    //private readonly HashSet<string> _allowedTypes = new() { "temp", "light", "water" };
    public void Update(int arduinoId, float value, long timestamp,
        sensorType type)
    {

        if (type == sensorType.Error)
        {
            Console.WriteLine("Invalid sensor type.");
            return;
        }
        var key = new SensorKey 
        {
            ArduinoId = arduinoId,
            Type = type
        };

        _states[key] = new SensorState
        {
            ArduinoId = arduinoId,
            Value = value,
            Timestamp = timestamp,
            Type = type
        };
    }

    public SensorState? GetLatest(int arduinoId, sensorType type) // a little cleaner this way, bc the get latest return the sensorstate directly
    {
        var key = new SensorKey
        {
            ArduinoId = arduinoId,
            Type = type
        };

        return _states.TryGetValue(key, out var state) ? state : null;
        
    }
}

