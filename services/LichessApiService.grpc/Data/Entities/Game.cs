using LichessApiService.Grpc.Data.Enums;

namespace LichessApiService.Grpc.Data.Entities;

public class Game
{
    public int Id { get; set; }
    public string? LichessGameId { get; set; }
    public TimeControlType TimeControl { get; set; }
    public bool? IsTimeIncrease { get; set; }
    public int? TimeIncreaseSec { get; set; }
    public bool? IsRated { get; set; }
    public bool? IsBerserk { get; set; }
    public string? Source { get; set; }
    public string? EcoCode { get; set; }
    public string? OpeningName { get; set; }
    public int? TotalPly { get; set; }
    public int? OpeningPly { get; set; }
    public int? PlayerMoveCount { get; set; }
    public int? OpponentMoveCount { get; set; }
    public int? UserRating { get; set; }
    public int? OppRating { get; set; }
    public int? RatingDiff { get; set; }
    public bool? IsPlayerPieceBlack { get; set; }
    public GameResultType Result { get; set; }
    public string? TerminationType { get; set; }
    public DateTime? StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public int? DurationMin { get; set; }
    public int MatchId { get; set; }

    public Match Match { get; set; } = null!;
}
