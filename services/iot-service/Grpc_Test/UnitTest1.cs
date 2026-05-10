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
        var result = store.GetLatest();

        // Assert
        Assert.False(result.HasValue);
        Assert.False(store.HasValue);
    }

    [Fact]
    public void IoTStateStore_Update_ShouldStoreNewValues()
    {
        // Arrange
        var store = new IoTStateStore();
        float expectedValue = 25.5f;
        long expectedTimestamp = 123456789;
        string expectedType = "temp";

        // Act
        store.Update(expectedValue, expectedTimestamp, expectedType);
        var result = store.GetLatest();

        // Assert
        Assert.True(result.HasValue);
        Assert.Equal(expectedValue, result.Value);
        Assert.Equal(expectedTimestamp, result.Timestamp);
        Assert.Equal(expectedType, result.Type);
    }
}