using FluentAssertions;
using IoTGrpcServer;

namespace Grpc_Server.Tests;

public class RoomTests
{
    [Fact]
    public void Room_CO2SensorsCollection_ShouldBeInitialized()
    {
        var room = new Room();

        room.CO2Sensors.Should().NotBeNull();
        room.CO2Sensors.Should().BeEmpty();
    }

    [Fact]
    public void Room_CanAddCO2Sensor()
    {
        var room = new Room();
        var sensor = new CO2Sensor
        {
            Id = 1,
            Ppm = 500
        };

        room.CO2Sensors.Add(sensor);

        room.CO2Sensors.Should().Contain(sensor);
        room.CO2Sensors.Should().HaveCount(1);
    }
}