namespace Grpc_Server.Tests;

using FluentAssertions;
using IoTGrpcServer;

public class CO2SensorTests
{
    [Fact]
    public void CO2Sensor_CanStoreProperties()
    {
        var timestamp = DateTime.UtcNow;

        var sensor = new CO2Sensor
        {
            Id = 1,
            TimeStamp = timestamp,
            Ppm = 450,
            RoomId = 2,
            MatchId = 3
        };

        sensor.Id.Should().Be(1);
        sensor.TimeStamp.Should().Be(timestamp);
        sensor.Ppm.Should().Be(450);
        sensor.RoomId.Should().Be(2);
        sensor.MatchId.Should().Be(3);
    }

    [Fact]
    public void CO2Sensor_CanStoreNavigationProperties()
    {
        var room = new Room
        {
            Id = 2
        };

        var match = new Match
        {
            Id = 3
        };

        var sensor = new CO2Sensor
        {
            Room = room,
            Match = match
        };

        sensor.Room.Should().Be(room);
        sensor.Match.Should().Be(match);
    }
}