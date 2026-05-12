//testing out more DRY-abiding tests for the IoTServiceImpl class, using xUnit's
//Theory and InlineData attributes to run the same test with different inputs.

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
    private readonly IoTServiceImpl _service;

    public IoTServiceImplTheoryTests()
    {
        _mockStore = new Mock<IIoTStateStore>();
        _service = new IoTServiceImpl(_mockStore.Object);
    }

    [Theory]
    [InlineData("temp", 1)]
    [InlineData("light", 1)]
    [InlineData("waterLevel", 1)]
    //[InLineData("humidity", 1)]
    //etc
    public async Task GetSensorData_WhenStoreEmpty_ReturnsFailureStatus(string sensorTypeKey, int arduinoId)
    {
        // Arrange
        // Setup the mock to return null for whatever type is being tested
        _mockStore.Setup(s => s.GetLatest(arduinoId, sensorTypeKey)).Returns((SensorState)null!);

        // Act & Assert
        // check each method based on the sensorTypeKey passed by the Theory
        if (sensorTypeKey == "temp")
        {
            var response = await _service.getTemperature(new tempReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
            Assert.Equal(0, response.Reading.Value);
        }
        else if (sensorTypeKey == "light")
        {
            var response = await _service.getLight(new lightReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
        }
        else if (sensorTypeKey == "waterLevel")
        {
            var response = await _service.getWaterLevel(new waterLevelReq { ArduinoId = arduinoId }, null!);
            Assert.False(response.Status.Success);
        }
    }

    [Theory]
    [InlineData("temp", 23.5f, sensorType.Temp)]
    [InlineData("light", 500f, sensorType.Light)]
    [InlineData("waterLevel", 75.0f, sensorType.WaterLevel)]
    public async Task GetSensorData_WhenDataExists_ReturnsCorrectValue(string key, float val, sensorType expectedType)
    {
        // Arrange
        int arduinoId = 1;
        var state = new SensorState
        {
            Value = val,
            Type = key,
            Timestamp = 123456789
        };

        // Configure the mock to return the fake state
        _mockStore.Setup(s => s.GetLatest(arduinoId, key)).Returns(state);

        // Act & Assert
        // Because gRPC uses different response classes, test each branch
        if (key == "temp")
        {
            var response = await _service.getTemperature(new tempReq { ArduinoId = arduinoId }, null!);

            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(expectedType, response.Reading.Type);
        }
        else if (key == "light")
        {
            var response = await _service.getLight(new lightReq { ArduinoId = arduinoId }, null!);

            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(expectedType, response.Reading.Type);
        }
        else if (key == "waterLevel")
        {
            var response = await _service.getWaterLevel(new waterLevelReq { ArduinoId = arduinoId }, null!);

            Assert.True(response.Status.Success);
            Assert.Equal(val, response.Reading.Value);
            Assert.Equal(expectedType, response.Reading.Type);
        }
    }
}