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
}