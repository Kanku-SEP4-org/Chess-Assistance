using FluentAssertions;
using IoTGrpcServer;

namespace Grpc_Server.Tests;

public class MatchTests
{
    [Fact]
    public void Match_CO2SensorsCollection_ShouldBeInitialized()
    {
        var match = new Match();

        match.CO2Sensors.Should().NotBeNull();
        match.CO2Sensors.Should().BeEmpty();
    }

    [Fact]
    public void Match_CanAddCO2Sensor()
    {
        var match = new Match();
        var sensor = new CO2Sensor
        {
            Id = 1,
            Ppm = 500
        };

        match.CO2Sensors.Add(sensor);

        match.CO2Sensors.Should().Contain(sensor);
        match.CO2Sensors.Should().HaveCount(1);
    }
}