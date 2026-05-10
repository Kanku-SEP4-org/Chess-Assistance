namespace IoTGrpcServer.Contracts;

public sealed class SensorKey : IEquatable<SensorKey>
{
    public int ArduinoId { get; set; }
    public string Type { get; set; } = string.Empty;

    public bool Equals(SensorKey? other)
    {
        if (other is null) return false;

        return ArduinoId == other.ArduinoId &&
               string.Equals(Type, other.Type, StringComparison.OrdinalIgnoreCase);
    }

    public override bool Equals(object? obj) => Equals(obj as SensorKey);

    public override int GetHashCode()
    {
        return HashCode.Combine(ArduinoId, Type.ToLowerInvariant());
    }
}