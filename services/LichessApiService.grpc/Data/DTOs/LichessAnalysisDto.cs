using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessAnalysisDto
{
    [JsonPropertyName("inaccuracy")]
    public int? Inaccuracy { get; set; }

    [JsonPropertyName("mistake")]
    public int? Mistake { get; set; }

    [JsonPropertyName("blunder")]
    public int? Blunder { get; set; }

    [JsonPropertyName("acpl")]
    public int? Acpl { get; set; }

    [JsonPropertyName("accuracy")]
    public int? Accuracy { get; set; }
}
