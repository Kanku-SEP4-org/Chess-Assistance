using IotService;

namespace IoTGrpcServer.Contracts;

public sealed class SensorKey : IEquatable<SensorKey>
{
    public int ArduinoId { get; set; }
    public sensorType Type { get; set; }

    public bool Equals(SensorKey? other)
    {
        if (other is null) return false;
        if (ReferenceEquals(this, other)) return true;

        return ArduinoId == other.ArduinoId && Type == other.Type;
    }

    public override bool Equals(object? obj) => Equals(obj as SensorKey);

    public override int GetHashCode()
    {
        return HashCode.Combine(ArduinoId, Type);
    }
}