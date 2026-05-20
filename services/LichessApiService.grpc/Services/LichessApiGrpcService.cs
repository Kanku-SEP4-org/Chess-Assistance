using System.Collections.Concurrent;
using Grpc.Core;
using LichessApiService.Grpc.Data;
using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Lichess;
using LichessApiService.Grpc.Protos;
using Microsoft.EntityFrameworkCore;

namespace LichessApiService.Grpc.Services;

public class LichessApiGrpcService(
    LichessDbContext db,
    LichessStreamService streamService,
    ILogger<LichessApiGrpcService> logger)
    : LichessService.LichessServiceBase
{
    private static readonly ConcurrentDictionary<int, CancellationTokenSource> ActiveSessions = new();

    public override async Task<RegisterPlayerResponse> RegisterPlayer(
        RegisterPlayerRequest request, ServerCallContext context)
    {
        if (string.IsNullOrWhiteSpace(request.LichessId) || string.IsNullOrWhiteSpace(request.Username))
        {
            throw new RpcException(new Status(StatusCode.InvalidArgument,
                "lichess_id and username are required"));
        }

        var existing = await db.Players
            .FirstOrDefaultAsync(p => p.LichessId == request.LichessId);

        if (existing != null)
        {
            existing.Username = request.Username;
            await db.SaveChangesAsync();

            return new RegisterPlayerResponse { PlayerId = existing.Id, IsNew = false };
        }

        var player = new Player
        {
            LichessId = request.LichessId,
            Username = request.Username
        };

        db.Players.Add(player);
        await db.SaveChangesAsync();

        logger.LogInformation("Player {PlayerId} registered ({LichessId})", player.Id, request.LichessId);

        return new RegisterPlayerResponse { PlayerId = player.Id, IsNew = true };
    }

    public override async Task<StartSessionResponse> StartSession(
        StartSessionRequest request, ServerCallContext context)
    {
        if (string.IsNullOrWhiteSpace(request.PlayerUsername) || request.PlayerId <= 0)
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = "player_id and player_username are required"
            };
        }

        if (string.IsNullOrWhiteSpace(request.LichessToken))
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = "lichess_token is required for streaming"
            };
        }

        if (request.SleepTime == null || request.AwakenTime == null || request.ConfirmedAt == null)
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = "sleep_time, awaken_time, and confirmed_at are required"
            };
        }

        var sleepTime = request.SleepTime.ToDateTime();
        var awakenTime = request.AwakenTime.ToDateTime();
        var confirmedAt = request.ConfirmedAt.ToDateTime();

        if (awakenTime <= sleepTime)
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = "awaken_time must be after sleep_time"
            };
        }

        if (confirmedAt <= awakenTime)
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = "confirmed_at must be after awaken_time"
            };
        }

        var existingSession = await db.Sessions
            .FirstOrDefaultAsync(s => s.PlayerId == request.PlayerId && s.EndedAt == null);

        if (existingSession != null)
        {
            return new StartSessionResponse
            {
                Success = false,
                Message = $"Player already has an active session (id: {existingSession.Id})"
            };
        }

        var today = confirmedAt.Date;
        var tomorrow = today.AddDays(1);

        var healthRecord = await db.HealthRecords
            .FirstOrDefaultAsync(hr => hr.PlayerId == request.PlayerId
                && hr.ConfirmedAt >= today && hr.ConfirmedAt < tomorrow);

        if (healthRecord != null)
        {
            healthRecord.SleepTime = sleepTime;
            healthRecord.AwakenTime = awakenTime;
            healthRecord.ConfirmedAt = confirmedAt;
            healthRecord.WaterIntakeMl = request.WaterIntakeInitialMl;
        }
        else
        {
            healthRecord = new HealthRecord
            {
                SleepTime = sleepTime,
                AwakenTime = awakenTime,
                ConfirmedAt = confirmedAt,
                WaterIntakeMl = request.WaterIntakeInitialMl,
                PlayerId = request.PlayerId
            };
            db.HealthRecords.Add(healthRecord);
        }

        await db.SaveChangesAsync();

        var session = new Session
        {
            StartedAt = DateTime.UtcNow,
            PlayerId = request.PlayerId,
            HealthRecordId = healthRecord.Id
        };

        db.Sessions.Add(session);
        await db.SaveChangesAsync();

        logger.LogInformation(
            "Session {SessionId} created for player {PlayerId} ({Username}) with sleep record",
            session.Id, request.PlayerId, request.PlayerUsername);

        var cts = new CancellationTokenSource();
        ActiveSessions[session.Id] = cts;

        _ = Task.Run(async () =>
        {
            try
            {
                await streamService.StreamSessionAsync(
                    session.Id,
                    request.PlayerId,
                    request.PlayerUsername,
                    request.LichessToken,
                    cts.Token);
            }
            finally
            {
                ActiveSessions.TryRemove(session.Id, out _);
            }
        }, cts.Token);

        return new StartSessionResponse
        {
            SessionId = session.Id,
            Success = true,
            Message = "Session started, listening for matches"
        };
    }

    public override async Task<EndSessionResponse> EndSession(
        EndSessionRequest request, ServerCallContext context)
    {
        var session = await db.Sessions.FindAsync(request.SessionId);

        if (session == null)
        {
            return new EndSessionResponse
            {
                Success = false,
                Message = $"Session {request.SessionId} not found"
            };
        }

        if (session.EndedAt != null)
        {
            return new EndSessionResponse
            {
                Success = false,
                Message = $"Session {request.SessionId} is already ended"
            };
        }

        if (ActiveSessions.TryRemove(request.SessionId, out var cts))
        {
            await cts.CancelAsync();
            cts.Dispose();
        }

        session.EndedAt = DateTime.UtcNow;
        session.TotalWaterMl = request.WaterDrunkDuringSessionMl;
        await db.SaveChangesAsync();

        logger.LogInformation("Session {SessionId} ended", request.SessionId);

        return new EndSessionResponse
        {
            Success = true,
            Message = "Session ended"
        };
    }
}
