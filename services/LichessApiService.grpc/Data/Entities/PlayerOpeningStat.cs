namespace LichessApiService.Grpc.Data.Entities;

public class PlayerOpeningStat
{
    public int Id { get; set; }
    public int PlayerId { get; set; }
    public string EcoCode { get; set; } = null!;
    public string? OpeningName { get; set; }
    public int PlayerAsWhite { get; set; }
    public int PlayerAsBlack { get; set; }
    public int PlayerWins { get; set; }
    public int PlayerLosses { get; set; }
    public int PlayerDraws { get; set; }
    public int OppAsWhite { get; set; }
    public int OppAsBlack { get; set; }
    public int OppWins { get; set; }
    public int OppLosses { get; set; }
    public int TotalGames { get; set; }
}
