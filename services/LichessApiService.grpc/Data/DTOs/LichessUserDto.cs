using System.Text.Json.Serialization;

namespace LichessApiService.Grpc.Data.DTOs;

public class LichessUserDto
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("id")]
    public string Id { get; set; } = "";
}
