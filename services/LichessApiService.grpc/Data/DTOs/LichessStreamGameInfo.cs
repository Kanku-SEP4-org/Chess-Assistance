using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessStreamGameInfo
{
    [JsonPropertyName("gameId")]
    public string GameId { get; set; } = "";

    [JsonPropertyName("fullId")]
    public string FullId { get; set; } = "";

    [JsonPropertyName("color")]
    public string Color { get; set; } = "";

    [JsonPropertyName("fen")]
    public string Fen { get; set; } = "";

    [JsonPropertyName("hasMoved")]
    public bool HasMoved { get; set; }

    [JsonPropertyName("isMyTurn")]
    public bool IsMyTurn { get; set; }

    [JsonPropertyName("opponent")]
    public LichessOpponentDto? Opponent { get; set; }

    [JsonPropertyName("source")]
    public string? Source { get; set; }

    [JsonPropertyName("speed")]
    public string? Speed { get; set; }

    [JsonPropertyName("rated")]
    public bool? Rated { get; set; }
}
