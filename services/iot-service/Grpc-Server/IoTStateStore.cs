using System.Collections.Concurrent;
using IoTGrpcServer.Contracts;
using IotService;
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

    private static DateTime UnixTimeStampToDateTime( double unixTimeStamp )
    {
        // Unix timestamp is seconds past epoch
        DateTime dateTime = new DateTime(1970, 1, 1, 0, 0, 0, 0, DateTimeKind.Utc);
        dateTime = dateTime.AddSeconds( unixTimeStamp ).ToLocalTime();
        return dateTime;
    }

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

        // this code currently makes a new sensor state with each message
        // if we go with recording as a boolean for a sensor state to signify that messages get recorded we should be updating existing states instead
        _states[key] = new SensorState
        {
            ArduinoId = arduinoId,
            Value = value,
            Timestamp = timestamp,
            Type = type
        };

        // we have no handling of rooms so for now we create a dummy room
        if (_states[key].Recording)
        {
            dbContext.Add(new Sensor
            {
                Value = value,
                Type = type.ToString(),
                TimeStamp = UnixTimeStampToDateTime(timestamp),
                Room = new Room
                {
                    PlayerId = 1,
                    Perimeter = 20
                }
            });
        }

        // currenty saves into db when new message received, should it save when recording stopped?
        dbContext.SaveChanges();
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

    public IEnumerable<SensorState> Record(int arduinoId)
    {
        var sensors = _states
            .Where(kvp => kvp.Key.ArduinoId == arduinoId)
            .Select(kvp => kvp.Value);

        foreach(var s in sensors)
        {
            s.Recording = true;
        }

        return sensors;
    }

    public IEnumerable<SensorState> StopRecord(int arduinoId)
    {
        var sensors = _states
            .Where(kvp => kvp.Key.ArduinoId == arduinoId)
            .Select(kvp => kvp.Value);

        foreach(var s in sensors)
        {
            s.Recording = true;
        }

        dbContext.SaveChangesAsync();

        return sensors;
    }
}

