using NpgsqlTypes;

namespace LichessApiService.Grpc.Data.Enums;

public enum SessionStatus
{
    [PgName("pending")]
    Pending,

    [PgName("complete")]
    Complete,

    [PgName("exported")]
    Exported
}
