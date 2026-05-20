using LichessApiService.Grpc.Data.Enums;

namespace LichessApiService.Grpc.Data.Entities;

public class Dataset
{
    public int Id { get; set; }
    public int MatchId { get; set; }
    public decimal? AvgLux { get; set; }
    public decimal? AvgCelsius { get; set; }
    public decimal? AvgPpm { get; set; }
    public int? WaterIntakeMl { get; set; }
    public TimeSpan? SleepDuration { get; set; }
    public TimeSpan? AwakeDuration { get; set; }
    public string? EcoCode { get; set; }
    public string? OpeningName { get; set; }
    public bool? IsRated { get; set; }
    public int? TotalPly { get; set; }
    public int? OpeningPly { get; set; }
    public int? PlayerMoveCount { get; set; }
    public int? OpponentMoveCount { get; set; }
    public TimeControlType? TimeControl { get; set; }
    public bool? IsTimeIncrease { get; set; }
    public int? TimeIncreaseSec { get; set; }
    public bool? IsBerserk { get; set; }
    public int? DurationMin { get; set; }
    public int? UserRating { get; set; }
    public int? OppRating { get; set; }
    public int? RatingDiff { get; set; }
    public bool? IsPlayerPieceBlack { get; set; }
    public string? TerminationType { get; set; }
    public GameResultType? Result { get; set; }
    public decimal? PlayerOpeningWinRate { get; set; }
    public int? PlayerOpeningGameCount { get; set; }
    public int? InaccuracyCnt { get; set; }
    public int? MistakeCnt { get; set; }
    public int? BlunderCnt { get; set; }
    public int? Acpl { get; set; }
    public int? Accuracy { get; set; }
    public int? ConsecutiveLossesPregame { get; set; }
    public decimal? AvgTpmSeconds { get; set; }

    public Match Match { get; set; } = null!;
}
