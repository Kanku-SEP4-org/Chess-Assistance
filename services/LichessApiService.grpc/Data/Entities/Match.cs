namespace LichessApiService.Grpc.Data.Entities;

public class Match
{
    public int Id { get; set; }
    public DateOnly MatchDate { get; set; }
    public TimeSpan? DurationFromPrevMatch { get; set; }
    public int SessionId { get; set; }
    public int PlayerId { get; set; }

    public Session Session { get; set; } = null!;
    public Game? Game { get; set; }
    public Dataset? Dataset { get; set; }
}
