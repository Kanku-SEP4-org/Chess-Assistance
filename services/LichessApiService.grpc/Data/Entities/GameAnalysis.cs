namespace LichessApiService.Grpc.Data.Entities;

public class GameAnalysis
{
    public int Id { get; set; }
    public int GameId { get; set; }
    public int? InaccuracyCnt { get; set; }
    public int? MistakeCnt { get; set; }
    public int? BlunderCnt { get; set; }
    public int? Acpl { get; set; }
    public int? Accuracy { get; set; }

    public Game Game { get; set; } = null!;
}
