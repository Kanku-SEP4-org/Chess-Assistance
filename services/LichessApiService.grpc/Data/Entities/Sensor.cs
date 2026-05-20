using LichessApiService.Grpc.Data.Enums;

namespace LichessApiService.Grpc.Data.Entities;

public class Sensor
{
    public int Id { get; set; }
    public int RoomId { get; set; }
    public SensorType Type { get; set; }
    public double Value { get; set; }
    public DateTime TimeStamp { get; set; }

    public Room Room { get; set; } = null!;
}
