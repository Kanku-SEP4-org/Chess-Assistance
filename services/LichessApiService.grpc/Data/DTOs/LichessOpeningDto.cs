using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessOpeningDto
{
    [JsonPropertyName("eco")]
    public string? Eco { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("ply")]
    public int? Ply { get; set; }
}
