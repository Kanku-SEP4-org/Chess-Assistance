using IotService;

namespace Grpc_Test;

using Xunit;
using IoTGrpcServer;

public class UnitTest1
{
    [Fact]
    public void IoTStateStore_InitialState_ShouldBeEmpty()
    {
        // Arrange
        var store = new IoTStateStore();

        // Act
        var result = store.GetLatest(1, sensorType.Temp);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void IoTStateStore_Update_ShouldStoreNewValues()
    {
        // Arrange
        var store = new IoTStateStore();
        float expectedValue = 25.5f;
        long expectedTimestamp = 123456789;
        sensorType expectedType = sensorType.Temp;
        int arduinoId = 1;

        // Act
        store.Update(arduinoId, expectedValue, expectedTimestamp, expectedType);
        var result = store.GetLatest(arduinoId, expectedType);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(arduinoId, result.ArduinoId);
        Assert.Equal(expectedValue, result.Value);
        Assert.Equal(expectedTimestamp, result.Timestamp);
        Assert.Equal(expectedType, result.Type);
    }
}