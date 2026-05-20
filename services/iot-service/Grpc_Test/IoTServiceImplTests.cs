using Moq;
using Xunit;
using Grpc_Server.Services;
using IoTGrpcServer;
using IotService;
using Grpc.Core;
using IoTGrpcServer.Contracts;

namespace Grpc_Test;

public class IoTServiceImplTests
{
    private readonly Mock<IIoTStateStore> _mockStore;
    private readonly IoTServiceImpl _service;

    public IoTServiceImplTests()
    {
        _mockStore = new Mock<IIoTStateStore>();
        _service = new IoTServiceImpl(_mockStore.Object);
    }

    [Fact]
    public async Task GetTemperature_Found_ReturnsSuccess()
    {
        // Arrange mocked state
        int arduinoId = 1;
        var mockState = new SensorState
        {
            Value = 22.5f,
            Timestamp = 12345,
            Type = "temp"
        };

        // the mock must return the fake state when called with these specific arguments
        _mockStore.Setup(s => s.GetLatest(arduinoId, "temp")).Returns(mockState);

        var request = new tempReq { ArduinoId = arduinoId };

        // Act
        var response = await _service.getTemperature(request, null!);

        // Assert
        Assert.True(response.Status.Success);
        Assert.Equal(22.5f, response.Reading.Value);
        Assert.Contains("successfully", response.Status.Message);
    }

    [Fact]
    public async Task GetTemperature_NotFound_ReturnsFailure()
    {
        // Arrange
        int arduinoId = 99;
        // Tell the mock to return null for this ID
        _mockStore.Setup(s => s.GetLatest(arduinoId, "temp")).Returns((SensorState)null!);

        var request = new tempReq { ArduinoId = arduinoId };

        // Act
        var response = await _service.getTemperature(request, null!);

        // Assert
        Assert.False(response.Status.Success);
        Assert.Equal(0, response.Reading.Value);
        Assert.Contains("No temperature reading available", response.Status.Message);
    }

    [Fact]
    public async Task GetCO2_Found_ReturnsSuccess()
    {
        int arduinoId = 1;
        var mockState = new SensorState
        {
            Value = 650.5f,
            Timestamp = 54321,
            Type = "co2"
        };

        _mockStore.Setup(s => s.GetLatest(arduinoId, "co2")).Returns(mockState);

        var request = new co2Req { ArduinoId = arduinoId };

        var response = await _service.getCO2(request, null!);

        Assert.True(response.Status.Success);
        Assert.Equal(650.5f, response.Reading.Value);
        Assert.Equal(sensorType.Co2, response.Reading.Type);
        Assert.Equal(54321, response.Reading.Timestamp);
        Assert.Contains("CO2", response.Status.Message);
    }

    [Fact]
    public async Task GetCO2_NotFound_ReturnsFailure()
    {
        int arduinoId = 99;
        _mockStore.Setup(s => s.GetLatest(arduinoId, "co2")).Returns((SensorState)null!);

        var request = new co2Req { ArduinoId = arduinoId };

        var response = await _service.getCO2(request, null!);

        Assert.False(response.Status.Success);
        Assert.Equal(0, response.Reading.Value);
        Assert.Equal(sensorType.Co2, response.Reading.Type);
        Assert.Equal(0, response.Reading.Timestamp);
        Assert.Contains("No CO2 reading available", response.Status.Message);
    }

    [Fact]
    public async Task GetCO2_CallsStateStoreWithCorrectType()
    {
    int arduinoId = 5;
    _mockStore.Setup(s => s.GetLatest(arduinoId, "co2"))
              .Returns((SensorState)null!);

    var request = new co2Req { ArduinoId = arduinoId };

    await _service.getCO2(request, null!);

    _mockStore.Verify(s => s.GetLatest(arduinoId, "co2"), Times.Once);
    }
}