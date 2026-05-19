using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessOpponentDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("username")]
    public string Username { get; set; } = "";

    [JsonPropertyName("rating")]
    public int? Rating { get; set; }
}
