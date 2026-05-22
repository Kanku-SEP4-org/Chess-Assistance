namespace LichessApiService.Grpc.Data.Entities;

public class Room
{
    public int Id { get; set; }
    public decimal? Perimeter { get; set; }
    public int PlayerId { get; set; }
}
