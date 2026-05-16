namespace LichessApiService.Grpc.Data.Entities;

public class Session
{
    public int Id { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public TimeSpan? TotalDuration { get; set; }
    public int GameCount { get; set; }
    public int TotalWaterMl { get; set; }
    public int PlayerId { get; set; }

    public ICollection<Match> Matches { get; set; } = [];
    public HealthRecord? HealthRecord { get; set; }
}
