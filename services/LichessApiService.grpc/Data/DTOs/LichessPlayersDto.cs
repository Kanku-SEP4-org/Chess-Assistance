using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessPlayersDto
{
    [JsonPropertyName("white")]
    public LichessPlayerSideDto White { get; set; } = new();

    [JsonPropertyName("black")]
    public LichessPlayerSideDto Black { get; set; } = new();
}
