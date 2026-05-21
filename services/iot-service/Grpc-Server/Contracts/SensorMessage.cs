using System.Text.Json.Serialization;
using IotService;

namespace IoTGrpcServer.Contracts;

public class SensorMessage
{
    public int ArduinoId { get; set; }
    public float Value { get; set; }

    [JsonConverter(typeof(JsonStringEnumConverter))] // This makes it a string in JSON
    public sensorType Type { get; set; }
    public long Timestamp { get; set; }
}