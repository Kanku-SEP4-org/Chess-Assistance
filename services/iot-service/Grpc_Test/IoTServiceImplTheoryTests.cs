//testing out more DRY-compliant tests for the IoTServiceImpl class, using xUnit's
//Theory and InlineData attributes to run the same test with different inputs.

using Grpc_Server.Messaging;
using Moq;
using Xunit;
using Grpc_Server.Services;
using IoTGrpcServer;
using IotService;
using IoTGrpcServer.Contracts;

namespace Grpc_Test;

public class IoTServiceImplTheoryTests
{
    private readonly Mock<IIoTStateStore> _mockStore;
    private readonly Mock<IMessageQueue> _mockQueue;
    private readonly IoTServiceImpl _service;

    public IoTServiceImplTheoryTests()
    {
        _mockStore = new Mock<IIoTStateStore>();
        _mockQueue = new Mock<IMessageQueue>();
        _service = new IoTServiceImpl(_mockStore.Object, _mockQueue.Object);
    }

    [Theory]
    [InlineData(sensorType.Temp, 1)]
    [InlineData(sensorType.Light, 1)]
    [InlineData(sensorType.Water, 1)]
    [InlineData(sensorType.Co2, 1)]
    public async Task GetSensorData_WhenStoreEmpty_ReturnsFailureStatus(sensorType type, int arduinoId)
    {
        // Arrange
        // Setup the mock using the enum!
        _mockStore.Setup(s => s.GetLatest(arduinoId, type)).Returns((SensorState)null!);

        // Act & Assert
        if (type == sensorType.Temp)
        {
            var response = await _service.getTemperature(new tempReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
        }
        else if (type == sensorType.Light)
        {
            var response = await _service.getLight(new lightReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
        }
        else if (type == sensorType.Water)
        {
            var response = await _service.getWaterLevel(new waterLevelReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
        }
        else if (type == sensorType.Co2)
{
            var response = await _service.getCO2(new co2Req { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
            Assert.Equal(0, response.Reading.Value);
            Assert.Equal(sensorType.Co2, response.Reading.Type);
}
    }

    [Theory]
    [InlineData(sensorType.Temp, 23.5f)]
    [InlineData(sensorType.Light, 500f)]
    [InlineData(sensorType.Water, 75.0f)]
    [InlineData(sensorType.Co2, 650.0f)]
    public async Task GetSensorData_WhenDataExists_ReturnsCorrectValue(sensorType type, float val)
    {
        // Arrange
        int arduinoId = 1;
        var state = new SensorState
        {
            ArduinoId = arduinoId,
            Value = val,
            Type = type, // Now an enum!
            Timestamp = 123456789
        };

        _mockStore.Setup(s => s.GetLatest(arduinoId, type)).Returns(state);

        // Act & Assert
        if (type == sensorType.Temp)
        {
            var response = await _service.getTemperature(new tempReq { ArduinoId = arduinoId }, null!);
            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(type, response.Reading.Type);
        }
        else if (type == sensorType.Light)
        {
            var response = await _service.getLight(new lightReq { ArduinoId = arduinoId }, null!);
            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(type, response.Reading.Type);
        }
        else if (type == sensorType.Water)
        {
            var response = await _service.getWaterLevel(new waterLevelReq { ArduinoId = arduinoId }, null!);
            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(type, response.Reading.Type);
        }
        else if (type == sensorType.Co2)
        {
            var response = await _service.getCO2(new co2Req { ArduinoId = arduinoId }, null!);

            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(type, response.Reading.Type);
}
    }

    [Theory]
    [InlineData(1, 250.0f)] // Specific amount
    [InlineData(1, null)]   // Default amount
    public async Task FillCup_SendsCommandToQueue(int id, float? amount)
    {
        // Arrange
        var request = new fillCupReq { ArduinoId = id };
        if (amount.HasValue) request.Amount = amount.Value;

        // Act
        var response = await _service.fillCup(request, null!);

        // Assert
        Assert.True(response.Status.Success);
        // Here you would verify that your mock message queue received the call
        _mockQueue.Verify(m => m.EnqueueObjectAsync( It.IsAny<object>()), Times.Once);
    }
}
