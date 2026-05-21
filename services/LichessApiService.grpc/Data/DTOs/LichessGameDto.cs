using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessGameDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("rated")]
    public bool Rated { get; set; }

    [JsonPropertyName("variant")]
    public string Variant { get; set; } = "";

    [JsonPropertyName("speed")]
    public string Speed { get; set; } = "";

    [JsonPropertyName("status")]
    public string Status { get; set; } = "";

    [JsonPropertyName("source")]
    public string? Source { get; set; }

    [JsonPropertyName("createdAt")]
    public long CreatedAt { get; set; }

    [JsonPropertyName("lastMoveAt")]
    public long LastMoveAt { get; set; }

    [JsonPropertyName("players")]
    public LichessPlayersDto Players { get; set; } = new();

    [JsonPropertyName("winner")]
    public string? Winner { get; set; }

    [JsonPropertyName("opening")]
    public LichessOpeningDto? Opening { get; set; }

    [JsonPropertyName("moves")]
    public string? Moves { get; set; }

    [JsonPropertyName("clock")]
    public LichessClockDto? Clock { get; set; }
}
