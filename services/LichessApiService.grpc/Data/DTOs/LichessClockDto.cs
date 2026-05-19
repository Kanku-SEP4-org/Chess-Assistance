using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessClockDto
{
    [JsonPropertyName("initial")]
    public int Initial { get; set; }

    [JsonPropertyName("increment")]
    public int Increment { get; set; }

    [JsonPropertyName("totalTime")]
    public int TotalTime { get; set; }
}
