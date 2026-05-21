namespace LichessApiService.Grpc.Data.Entities;

public class Player
{
    public int Id { get; set; }
    public string LichessId { get; set; } = null!;
    public string Username { get; set; } = null!;
}
