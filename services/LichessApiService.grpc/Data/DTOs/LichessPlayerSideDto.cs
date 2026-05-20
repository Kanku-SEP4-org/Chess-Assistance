using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessPlayerSideDto
{
    [JsonPropertyName("user")]
    public LichessUserDto? User { get; set; }

    [JsonPropertyName("rating")]
    public int? Rating { get; set; }

    [JsonPropertyName("ratingDiff")]
    public int? RatingDiff { get; set; }

    [JsonPropertyName("berserk")]
    public bool? Berserk { get; set; }

    [JsonPropertyName("analysis")]
    public LichessAnalysisDto? Analysis { get; set; }
}
