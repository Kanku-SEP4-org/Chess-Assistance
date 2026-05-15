using LichessApiService.Grpc.Data.DTOs;
using LichessApiService.Grpc.Data.Enums;
using LichessApiService.Grpc.Lichess;
using Moq;
using Xunit;

namespace LichessApiService.Grpc.Tests.Unit;

public class LichessGameMappingTests
{
    private readonly LichessGameFetcher _fetcher;

    public LichessGameMappingTests()
    {
        var httpFactory = new Mock<IHttpClientFactory>();
        _fetcher = new LichessGameFetcher(httpFactory.Object);
    }

    private static LichessGameDto CreateSampleGame(
        string winner = "white",
        string speed = "blitz",
        string playerColor = "white",
        string playerUsername = "testplayer") =>
        new()
        {
            Id = "abc12345",
            Rated = true,
            Variant = "standard",
            Speed = speed,
            Status = "mate",
            Source = "lobby",
            CreatedAt = 1700000000000,
            LastMoveAt = 1700000600000,
            Players = new LichessPlayersDto
            {
                White = new LichessPlayerSideDto
                {
                    User = new LichessUserDto
                    {
                        Id = playerColor == "white" ? playerUsername : "opponent1",
                        Name = playerColor == "white" ? "TestPlayer" : "Opponent1"
                    },
                    Rating = 1500,
                    RatingDiff = playerColor == "white" && winner == "white" ? 8
                        : playerColor == "white" && winner == "black" ? -8 : 0
                },
                Black = new LichessPlayerSideDto
                {
                    User = new LichessUserDto
                    {
                        Id = playerColor == "black" ? playerUsername : "opponent1",
                        Name = playerColor == "black" ? "TestPlayer" : "Opponent1"
                    },
                    Rating = 1480,
                    RatingDiff = playerColor == "black" && winner == "black" ? 8
                        : playerColor == "black" && winner == "white" ? -8 : 0
                }
            },
            Winner = winner,
            Opening = new LichessOpeningDto
            {
                Eco = "B12",
                Name = "Caro-Kann Defense",
                Ply = 6
            },
            Moves = "e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 c5 O-O Nc6 c3 cxd4 cxd4 Nge7",
            Clock = new LichessClockDto
            {
                Initial = 180,
                Increment = 2,
                TotalTime = 300
            }
        };

    [Fact]
    public void MapToGameEntity_BasicFields_MappedCorrectly()
    {
        var dto = CreateSampleGame();
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 42);

        Assert.Equal("abc12345", game.LichessGameId);
        Assert.Equal(42, game.MatchId);
        Assert.Equal("lobby", game.Source);
        Assert.Equal("mate", game.TerminationType);
        Assert.True(game.IsRated);
    }

    [Fact]
    public void MapToGameEntity_TimeControl_BlitzMapped()
    {
        var dto = CreateSampleGame(speed: "blitz");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(TimeControlType.Blitz, game.TimeControl);
    }

    [Theory]
    [InlineData("bullet", TimeControlType.Bullet)]
    [InlineData("blitz", TimeControlType.Blitz)]
    [InlineData("rapid", TimeControlType.Rapid)]
    [InlineData("classical", TimeControlType.Classical)]
    public void MapToGameEntity_AllTimeControls(string speed, TimeControlType expected)
    {
        var dto = CreateSampleGame(speed: speed);
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(expected, game.TimeControl);
    }

    [Fact]
    public void MapToGameEntity_ClockIncrement_DetectedCorrectly()
    {
        var dto = CreateSampleGame();
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.True(game.IsTimeIncrease);
        Assert.Equal(2, game.TimeIncreaseSec);
    }

    [Fact]
    public void MapToGameEntity_NoIncrement_DetectedCorrectly()
    {
        var dto = CreateSampleGame();
        dto.Clock = new LichessClockDto { Initial = 180, Increment = 0, TotalTime = 180 };
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.False(game.IsTimeIncrease);
        Assert.Equal(0, game.TimeIncreaseSec);
    }

    [Fact]
    public void MapToGameEntity_Opening_MappedCorrectly()
    {
        var dto = CreateSampleGame();
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal("B12", game.EcoCode);
        Assert.Equal("Caro-Kann Defense", game.OpeningName);
        Assert.Equal(6, game.OpeningPly);
    }

    [Fact]
    public void MapToGameEntity_MoveCounts_WhitePlayer()
    {
        // "e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 c5 O-O Nc6 c3 cxd4 cxd4 Nge7" = 16 ply
        var dto = CreateSampleGame(playerColor: "white");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(16, game.TotalPly);
        Assert.Equal(8, game.PlayerMoveCount);   // white: ceil(16/2) = 8
        Assert.Equal(8, game.OpponentMoveCount);  // black: 16 - 8 = 8
        Assert.False(game.IsPlayerPieceBlack);
    }

    [Fact]
    public void MapToGameEntity_MoveCounts_BlackPlayer()
    {
        var dto = CreateSampleGame(playerColor: "black", playerUsername: "testplayer");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(16, game.TotalPly);
        Assert.Equal(8, game.PlayerMoveCount);   // black: floor(16/2) = 8
        Assert.Equal(8, game.OpponentMoveCount);  // white: 16 - 8 = 8
        Assert.True(game.IsPlayerPieceBlack);
    }

    [Fact]
    public void MapToGameEntity_OddPlyCount_AsymmetricMoves()
    {
        var dto = CreateSampleGame(playerColor: "white");
        dto.Moves = "e4 c6 d4 d5 e5"; // 5 ply — white made 3, black made 2

        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(5, game.TotalPly);
        Assert.Equal(3, game.PlayerMoveCount);   // white: ceil(5/2) = 3
        Assert.Equal(2, game.OpponentMoveCount);  // black: 5 - 3 = 2
    }

    [Fact]
    public void MapToGameEntity_OddPlyCount_BlackPlayer()
    {
        var dto = CreateSampleGame(playerColor: "black", playerUsername: "testplayer");
        dto.Moves = "e4 c6 d4 d5 e5"; // 5 ply — white made 3, black made 2

        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(5, game.TotalPly);
        Assert.Equal(2, game.PlayerMoveCount);   // black: floor(5/2) = 2
        Assert.Equal(3, game.OpponentMoveCount);  // white: 5 - 2 = 3
    }

    [Fact]
    public void MapToGameEntity_Ratings_WhitePlayer()
    {
        var dto = CreateSampleGame(winner: "white", playerColor: "white");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(1500, game.UserRating);
        Assert.Equal(1480, game.OppRating);
        Assert.Equal(8, game.RatingDiff);
    }

    [Fact]
    public void MapToGameEntity_Ratings_BlackPlayer()
    {
        var dto = CreateSampleGame(winner: "black", playerColor: "black", playerUsername: "testplayer");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(1480, game.UserRating);
        Assert.Equal(1500, game.OppRating);
        Assert.Equal(8, game.RatingDiff);
    }

    [Fact]
    public void MapToGameEntity_PlayerWins_WhiteSide()
    {
        var dto = CreateSampleGame(winner: "white", playerColor: "white");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(GameResultType.Win, game.Result);
    }

    [Fact]
    public void MapToGameEntity_PlayerLoses_WhiteSide()
    {
        var dto = CreateSampleGame(winner: "black", playerColor: "white");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(GameResultType.Loss, game.Result);
    }

    [Fact]
    public void MapToGameEntity_PlayerWins_BlackSide()
    {
        var dto = CreateSampleGame(winner: "black", playerColor: "black", playerUsername: "testplayer");
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(GameResultType.Win, game.Result);
    }

    [Fact]
    public void MapToGameEntity_Draw()
    {
        var dto = CreateSampleGame();
        dto.Winner = null;
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Equal(GameResultType.Draw, game.Result);
    }

    [Fact]
    public void MapToGameEntity_Timestamps_ConvertedCorrectly()
    {
        var dto = CreateSampleGame();
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        var expectedStart = DateTimeOffset.FromUnixTimeMilliseconds(1700000000000).UtcDateTime;
        var expectedEnd = DateTimeOffset.FromUnixTimeMilliseconds(1700000600000).UtcDateTime;

        Assert.Equal(expectedStart, game.StartedAt);
        Assert.Equal(expectedEnd, game.EndedAt);
        // 600000ms = 10 minutes
        Assert.Equal(10, game.DurationMin);
    }

    [Fact]
    public void MapToGameEntity_NoBerserk_ReturnsNull()
    {
        var dto = CreateSampleGame();
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Null(game.IsBerserk);
    }

    [Fact]
    public void MapToGameEntity_WithBerserk_ReturnsTrueOnPlayerSide()
    {
        var dto = CreateSampleGame(playerColor: "white");
        dto.Players.White.Berserk = true;
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.True(game.IsBerserk);
    }

    [Fact]
    public void MapToGameEntity_NoMoves_NullPlyFields()
    {
        var dto = CreateSampleGame();
        dto.Moves = null;
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Null(game.TotalPly);
        Assert.Null(game.PlayerMoveCount);
        Assert.Null(game.OpponentMoveCount);
    }

    [Fact]
    public void MapToGameEntity_EmptyMoves_NullPlyFields()
    {
        var dto = CreateSampleGame();
        dto.Moves = "";
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Null(game.TotalPly);
        Assert.Null(game.PlayerMoveCount);
        Assert.Null(game.OpponentMoveCount);
    }

    [Fact]
    public void MapToGameEntity_NoOpening_NullFields()
    {
        var dto = CreateSampleGame();
        dto.Opening = null;
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.Null(game.EcoCode);
        Assert.Null(game.OpeningName);
        Assert.Null(game.OpeningPly);
    }

    [Fact]
    public void MapToGameEntity_NoClock_NullIncrementFields()
    {
        var dto = CreateSampleGame();
        dto.Clock = null;
        var game = _fetcher.MapToGameEntity(dto, "testplayer", matchId: 1);

        Assert.False(game.IsTimeIncrease);
        Assert.Null(game.TimeIncreaseSec);
    }

    [Fact]
    public void MapToGameEntity_CaseInsensitiveUsernameMatch()
    {
        var dto = CreateSampleGame(playerColor: "white", playerUsername: "TestPlayer");
        dto.Players.White.User!.Id = "testplayer";

        var game = _fetcher.MapToGameEntity(dto, "TestPlayer", matchId: 1);

        Assert.False(game.IsPlayerPieceBlack);
        Assert.Equal(1500, game.UserRating);
    }
}
