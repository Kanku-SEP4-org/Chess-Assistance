namespace LichessApiService.Grpc.Data.Entities;

public class SleepRecord
{
    public int Id { get; set; }
    public DateTime SleepTime { get; set; }
    public DateTime AwakenTime { get; set; }
    public TimeSpan? SleepDuration { get; set; }
    public DateTime ConfirmedAt { get; set; }
    public TimeSpan? AwakeDuration { get; set; }
    public DateTime RecordAt { get; set; }
    public int SessionId { get; set; }

    public Session Session { get; set; } = null!;
}
