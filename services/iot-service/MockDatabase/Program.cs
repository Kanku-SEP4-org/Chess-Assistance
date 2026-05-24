using Microsoft.EntityFrameworkCore;
using IoTGrpcServer;
using System.Data;

namespace MockDatabase;

public class Program
{
    public static async Task Main(string[] args)
    {
        const string schema = "chess_assistant";

        var connectionString =
            "Host=localhost;Port=5433;Database=chess_test;Username=chess;Password=chess";

        var options = new DbContextOptionsBuilder<MockDbContext>()
            .UseNpgsql(connectionString)
            .Options;

        await using var db = new MockDbContext(options);

        Console.WriteLine("Connecting to database...");

        if (!await db.Database.CanConnectAsync())
        {
            Console.WriteLine("Could not connect to database.");
            return;
        }

        Console.WriteLine("Connected to database.");

        await using var command = db.Database.GetDbConnection().CreateCommand();

        command.CommandText = $"""
    INSERT INTO {schema}.player (lichess_id, username)
    VALUES ('mock_lichess_user', 'Mock Player')
    ON CONFLICT (lichess_id)
    DO UPDATE SET username = EXCLUDED.username
    RETURNING id
""";

        if (command.Connection!.State != System.Data.ConnectionState.Open)
        {
            await command.Connection.OpenAsync();
        }

        var playerIdResult = await command.ExecuteScalarAsync();
        var playerId = Convert.ToInt32(playerIdResult);

        Console.WriteLine($"Using mock player with id: {playerId}");

        var room = new Room
        {
            PlayerId = playerId,
            Perimeter = 25
        };

        db.Rooms.Add(room);
        await db.SaveChangesAsync();

        Console.WriteLine($"Created mock room with id: {room.Id}");

        var fixedTimestamp = DateTime.UtcNow;

        var random = new Random();

        var sensors = new List<Sensor>
        {
            new Sensor
            {
                RoomId = room.Id,
                Type = "light",
                Value = random.Next(0, 1024),
                TimeStamp = fixedTimestamp
            },
            new Sensor
            {
                RoomId = room.Id,
                Type = "temperature",
                Value = random.Next(-100, 100),
                TimeStamp = fixedTimestamp
            },
            new Sensor
            {
                RoomId = room.Id,
                Type = "humidity",
                Value = random.Next(0, 100),
                TimeStamp = fixedTimestamp
            },
            new Sensor
            {
                RoomId = room.Id,
                Type = "co2",
                Value = random.Next(400, 1200),
                TimeStamp = fixedTimestamp
            }
        };

        db.Sensors.AddRange(sensors);
        await db.SaveChangesAsync();

        Console.WriteLine("Created mock sensors with random values:");

        foreach (var sensor in sensors)
        {
            Console.WriteLine($"- {sensor.Type}: {sensor.Value}");
        }

        Console.WriteLine("Mock data inserted successfully.");
    }
}