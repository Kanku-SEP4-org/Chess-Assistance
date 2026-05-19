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

        var session = new Session
        {
            StartedAt = DateTime.UtcNow,
            PlayerId = request.PlayerId
        };

        db.Sessions.Add(session);
        await db.SaveChangesAsync();

        logger.LogInformation(
            "Session {SessionId} created for player {PlayerId} ({Username})",
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
        await db.SaveChangesAsync();

        logger.LogInformation("Session {SessionId} ended", request.SessionId);

        return new EndSessionResponse
        {
            Success = true,
            Message = "Session ended"
        };
    }
}
