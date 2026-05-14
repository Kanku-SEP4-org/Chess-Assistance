using System.Collections.Concurrent;
using IoTGrpcServer.Contracts;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualBasic;

namespace IoTGrpcServer;

public class IoTStateStore : IIoTStateStore
{
    private readonly DbContext dbContext;
    private readonly ConcurrentDictionary<SensorKey, SensorState> _states = new();
    private readonly HashSet<string> _allowedTypes = new() { "temp", "light", "water" };

    public IoTStateStore(DbContext dbContext)
    {
        this.dbContext = dbContext;
    }

    public void Update(int arduinoId, float value, long timestamp, string type)
    {
        var normalizedType = type.Trim().ToLowerInvariant();

        // does not rely on a key list, providing a vulnerability, which allows to create any new key by sending a new message type
        // DONE: make key lists limiting what message types we handle
        if (!_allowedTypes.Contains(normalizedType))
        {
            Console.WriteLine($"Invalid sensor type: {normalizedType}");
            return;
        }
        var key = new SensorKey 
        {
            ArduinoId = arduinoId,
            Type = normalizedType
        };

        // this code currently makes a new sensor state with each message
        // if we go with recording as a boolean for a sensor state to signify that messages get recorded we should be updating existing states instead
        _states[key] = new SensorState
        {
            ArduinoId = arduinoId,
            Value = value,
            Timestamp = timestamp,
            Type = normalizedType
        };

        // until we do further the development, will sadly only do temperatureSensor with a dummy match and room
        // that being said, if i magically find time before sprint end then sure
        // currently i am at my wits end tho :(
        if (_states[key].Recording)
        {
            dbContext.Add(new TemperatureSensor
            {
                Celsius = (int)value,
                Room = new Room
                {
                    PlayerId = 1,
                    Perimeter = 20
                },
                Match = new Match
                {
                    SessionDate = DateOnly.MaxValue,
                    DurationFromPrevious = new DateInterval(),
                    SessionId = 1,
                    PlayerId = 1
                }
            });
        }

        // currenty saves into db when new message received, should it save when recording stopped?
        dbContext.SaveChanges();
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

