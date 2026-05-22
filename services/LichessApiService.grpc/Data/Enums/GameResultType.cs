using NpgsqlTypes;

namespace LichessApiService.Grpc.Data.Enums;

public enum GameResultType
{
    [PgName("win")]
    Win,

    [PgName("loss")]
    Loss,

    [PgName("draw")]
    Draw
}
