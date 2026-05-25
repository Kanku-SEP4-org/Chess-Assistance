using LichessApiService.Grpc.Data.Entities;
using LichessApiService.Grpc.Data.Enums;
using Microsoft.EntityFrameworkCore;

namespace LichessApiService.Grpc.Data;

public class LichessDbContext(DbContextOptions<LichessDbContext> options) : DbContext(options)
{
    public DbSet<Player> Players => Set<Player>();
    public DbSet<Session> Sessions => Set<Session>();
    public DbSet<Match> Matches => Set<Match>();
    public DbSet<Game> Games => Set<Game>();
    public DbSet<GameAnalysis> GameAnalyses => Set<GameAnalysis>();
    public DbSet<HealthRecord> HealthRecords => Set<HealthRecord>();
    public DbSet<Room> Rooms => Set<Room>();
    public DbSet<Sensor> Sensors => Set<Sensor>();
    public DbSet<Dataset> Datasets => Set<Dataset>();
    public DbSet<PlayerOpeningStat> PlayerOpeningStats => Set<PlayerOpeningStat>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema("chess_assistant");

        // gean: these enum types are created in the chess_assistant schema, not public.
        modelBuilder.HasPostgresEnum<TimeControlType>("chess_assistant", "time_control_type");
        modelBuilder.HasPostgresEnum<GameResultType>("chess_assistant", "game_result_type");

        modelBuilder.Entity<Player>(entity =>
        {
            entity.ToTable("player");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.LichessId).HasColumnName("lichess_id").HasMaxLength(50);
            entity.Property(e => e.Username).HasColumnName("username").HasMaxLength(255);

            entity.HasIndex(e => e.LichessId).IsUnique();
            entity.HasIndex(e => e.Username).IsUnique();
        });

        modelBuilder.Entity<Session>(entity =>
        {
            entity.ToTable("session");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.StartedAt).HasColumnName("started_at");
            entity.Property(e => e.EndedAt).HasColumnName("ended_at");
            entity.Property(e => e.TotalDuration).HasColumnName("total_duration")
                .ValueGeneratedOnAddOrUpdate();
            entity.Property(e => e.GameCount).HasColumnName("game_count").HasDefaultValue(0);
            entity.Property(e => e.TotalWaterMl).HasColumnName("total_water_ml").HasDefaultValue(0);
            entity.Property(e => e.PlayerId).HasColumnName("player_id");
            entity.Property(e => e.HealthRecordId).HasColumnName("health_record_id");

            entity.HasIndex(e => e.PlayerId)
                .HasFilter("ended_at IS NULL")
                .IsUnique()
                .HasDatabaseName("uq_one_active_session");

            entity.HasOne(e => e.HealthRecord)
                .WithMany(hr => hr.Sessions)
                .HasForeignKey(e => e.HealthRecordId);
        });

        modelBuilder.Entity<Match>(entity =>
        {
            entity.ToTable("match");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.MatchDate).HasColumnName("match_date");
            entity.Property(e => e.DurationFromPrevMatch).HasColumnName("duration_from_prev_match");
            entity.Property(e => e.SessionId).HasColumnName("session_id");
            entity.Property(e => e.PlayerId).HasColumnName("player_id");

            entity.HasOne(e => e.Session)
                .WithMany(s => s.Matches)
                .HasForeignKey(e => e.SessionId);

            entity.HasOne(e => e.Game)
                .WithOne(g => g.Match)
                .HasForeignKey<Game>(g => g.MatchId);

            entity.HasOne(e => e.Dataset)
                .WithOne(d => d.Match)
                .HasForeignKey<Dataset>(d => d.MatchId);
        });

        modelBuilder.Entity<HealthRecord>(entity =>
        {
            entity.ToTable("health_record");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.SleepTime).HasColumnName("sleep_time");
            entity.Property(e => e.AwakenTime).HasColumnName("awaken_time");
            entity.Property(e => e.SleepDuration).HasColumnName("sleep_duration")
                .ValueGeneratedOnAddOrUpdate();
            entity.Property(e => e.ConfirmedAt).HasColumnName("confirmed_at");
            entity.Property(e => e.AwakeDuration).HasColumnName("awake_duration")
                .ValueGeneratedOnAddOrUpdate();
            entity.Property(e => e.WaterIntakeMl).HasColumnName("water_intake_ml");
            entity.Property(e => e.PlayerId).HasColumnName("player_id");
        });

        modelBuilder.Entity<Game>(entity =>
        {
            entity.ToTable("game");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.LichessGameId).HasColumnName("lichess_game_id").HasMaxLength(16);
            entity.Property(e => e.TimeControl).HasColumnName("time_control")
                .HasColumnType("chess_assistant.time_control_type");
            entity.Property(e => e.IsTimeIncrease).HasColumnName("is_time_increase");
            entity.Property(e => e.TimeIncreaseSec).HasColumnName("time_increase_sec");
            entity.Property(e => e.IsRated).HasColumnName("is_rated");
            entity.Property(e => e.IsBerserk).HasColumnName("is_berserk");
            entity.Property(e => e.Source).HasColumnName("source").HasMaxLength(50);
            entity.Property(e => e.EcoCode).HasColumnName("eco_code").HasMaxLength(3);
            entity.Property(e => e.OpeningName).HasColumnName("opening_name").HasMaxLength(100);
            entity.Property(e => e.TotalPly).HasColumnName("total_ply");
            entity.Property(e => e.OpeningPly).HasColumnName("opening_ply");
            entity.Property(e => e.PlayerMoveCount).HasColumnName("player_move_count");
            entity.Property(e => e.OpponentMoveCount).HasColumnName("opponent_move_count");
            entity.Property(e => e.UserRating).HasColumnName("user_rating");
            entity.Property(e => e.OppRating).HasColumnName("opp_rating");
            entity.Property(e => e.RatingDiff).HasColumnName("rating_diff");
            entity.Property(e => e.IsPlayerPieceBlack).HasColumnName("is_player_piece_black");
            entity.Property(e => e.Result).HasColumnName("result")
                .HasColumnType("chess_assistant.game_result_type");
            entity.Property(e => e.TerminationType).HasColumnName("termination_type").HasMaxLength(50);
            entity.Property(e => e.StartedAt).HasColumnName("started_at");
            entity.Property(e => e.EndedAt).HasColumnName("ended_at");
            entity.Property(e => e.DurationMin).HasColumnName("duration_min");
            entity.Property(e => e.MatchId).HasColumnName("match_id");

            entity.HasIndex(e => e.MatchId).IsUnique();

            entity.HasOne(e => e.Analysis)
                .WithOne(a => a.Game)
                .HasForeignKey<GameAnalysis>(a => a.GameId);
        });

        modelBuilder.Entity<GameAnalysis>(entity =>
        {
            entity.ToTable("game_analysis");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.GameId).HasColumnName("game_id");
            entity.Property(e => e.InaccuracyCnt).HasColumnName("inaccuracy_cnt");
            entity.Property(e => e.MistakeCnt).HasColumnName("mistake_cnt");
            entity.Property(e => e.BlunderCnt).HasColumnName("blunder_cnt");
            entity.Property(e => e.Acpl).HasColumnName("acpl");
            entity.Property(e => e.Accuracy).HasColumnName("accuracy");

            entity.HasIndex(e => e.GameId).IsUnique();
        });

        modelBuilder.Entity<Room>(entity =>
        {
            entity.ToTable("room");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Perimeter).HasColumnName("perimeter");
            entity.Property(e => e.PlayerId).HasColumnName("player_id");
        });

        modelBuilder.Entity<Sensor>(entity =>
        {
            entity.ToTable("sensor");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.Type).HasColumnName("type").HasConversion<string>();
            entity.Property(e => e.Value).HasColumnName("value");
            entity.Property(e => e.TimeStamp).HasColumnName("time_stamp")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            entity.HasIndex(e => new { e.RoomId, e.TimeStamp });

            entity.HasOne(e => e.Room).WithMany().HasForeignKey(e => e.RoomId);
        });

        modelBuilder.Entity<Dataset>(entity =>
        {
            entity.ToTable("dataset");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.MatchId).HasColumnName("match_id");
            entity.Property(e => e.AvgLux).HasColumnName("avg_lux");
            entity.Property(e => e.AvgCelsius).HasColumnName("avg_celsius");
            entity.Property(e => e.AvgPpm).HasColumnName("avg_ppm");
            entity.Property(e => e.WaterIntakeMl).HasColumnName("water_intake_ml");
            entity.Property(e => e.SleepDuration).HasColumnName("sleep_duration");
            entity.Property(e => e.AwakeDuration).HasColumnName("awake_duration");
            entity.Property(e => e.EcoCode).HasColumnName("eco_code").HasMaxLength(3);
            entity.Property(e => e.OpeningName).HasColumnName("opening_name").HasMaxLength(100);
            entity.Property(e => e.IsRated).HasColumnName("is_rated");
            entity.Property(e => e.TotalPly).HasColumnName("total_ply");
            entity.Property(e => e.OpeningPly).HasColumnName("opening_ply");
            entity.Property(e => e.PlayerMoveCount).HasColumnName("player_move_count");
            entity.Property(e => e.OpponentMoveCount).HasColumnName("opponent_move_count");
            entity.Property(e => e.TimeControl).HasColumnName("time_control")
                .HasColumnType("chess_assistant.time_control_type");
            entity.Property(e => e.IsTimeIncrease).HasColumnName("is_time_increase");
            entity.Property(e => e.TimeIncreaseSec).HasColumnName("time_increase_sec");
            entity.Property(e => e.IsBerserk).HasColumnName("is_berserk");
            entity.Property(e => e.DurationMin).HasColumnName("duration_min");
            entity.Property(e => e.UserRating).HasColumnName("user_rating");
            entity.Property(e => e.OppRating).HasColumnName("opp_rating");
            entity.Property(e => e.RatingDiff).HasColumnName("rating_diff");
            entity.Property(e => e.IsPlayerPieceBlack).HasColumnName("is_player_piece_black");
            entity.Property(e => e.TerminationType).HasColumnName("termination_type").HasMaxLength(50);
            entity.Property(e => e.Result).HasColumnName("result")
                .HasColumnType("chess_assistant.game_result_type");
            entity.Property(e => e.PlayerOpeningWinRate).HasColumnName("player_opening_win_rate");
            entity.Property(e => e.PlayerOpeningGameCount).HasColumnName("player_opening_game_count");
            entity.Property(e => e.InaccuracyCnt).HasColumnName("inaccuracy_cnt");
            entity.Property(e => e.MistakeCnt).HasColumnName("mistake_cnt");
            entity.Property(e => e.BlunderCnt).HasColumnName("blunder_cnt");
            entity.Property(e => e.Acpl).HasColumnName("acpl");
            entity.Property(e => e.Accuracy).HasColumnName("accuracy");
            entity.Property(e => e.ConsecutiveLossesPregame).HasColumnName("consecutive_losses_pregame");
            entity.Property(e => e.AvgTpmSeconds).HasColumnName("avg_tpm_seconds");

            entity.HasIndex(e => e.MatchId).IsUnique();
        });

        modelBuilder.Entity<PlayerOpeningStat>(entity =>
        {
            entity.ToTable("player_opening_stat");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.PlayerId).HasColumnName("player_id");
            entity.Property(e => e.EcoCode).HasColumnName("eco_code").HasMaxLength(3);
            entity.Property(e => e.OpeningName).HasColumnName("opening_name").HasMaxLength(100);
            entity.Property(e => e.PlayerAsWhite).HasColumnName("player_as_white");
            entity.Property(e => e.PlayerAsBlack).HasColumnName("player_as_black");
            entity.Property(e => e.PlayerWins).HasColumnName("player_wins");
            entity.Property(e => e.PlayerLosses).HasColumnName("player_losses");
            entity.Property(e => e.PlayerDraws).HasColumnName("player_draws");
            entity.Property(e => e.OppAsWhite).HasColumnName("opp_as_white");
            entity.Property(e => e.OppAsBlack).HasColumnName("opp_as_black");
            entity.Property(e => e.OppWins).HasColumnName("opp_wins");
            entity.Property(e => e.OppLosses).HasColumnName("opp_losses");
            entity.Property(e => e.TotalGames).HasColumnName("total_games")
                .ValueGeneratedOnAddOrUpdate();

            entity.HasIndex(e => new { e.PlayerId, e.EcoCode })
                .IsUnique()
                .HasDatabaseName("uq_player_opening");
        });
    }
}
