using NpgsqlTypes;

namespace LichessApiService.Grpc.Data.Enums;

public enum TimeControlType
{
    [PgName("bullet")]
    Bullet,

    [PgName("blitz")]
    Blitz,

    [PgName("rapid")]
    Rapid,

    [PgName("classical")]
    Classical
}
