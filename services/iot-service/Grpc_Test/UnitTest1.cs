namespace Grpc_Test;

using Xunit;
using IoTGrpcServer;
using Microsoft.VisualBasic;
using Microsoft.EntityFrameworkCore;
using IoTGrpcServer.Contracts;


public class UnitTest1
{
    //mock dbContext
    public class FakeDbContext : DbContext
    {
        public FakeDbContext(DbContextOptions options) : base(options) { }

        public DbSet<Sensor> Sensors { get; set; }
    }

    [Fact]
    public void IoTStateStore_InitialState_ShouldBeEmpty()
    {
        var options = new DbContextOptionsBuilder<FakeDbContext>()
            .UseInMemoryDatabase(databaseName: "test")
            .Options;

        // Arrange
        var store = new IoTStateStore(new FakeDbContext(options));

        // Act
        var result = store.GetLatest(1, "temp");

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void IoTStateStore_Update_ShouldStoreNewValues()
    {
        var options = new DbContextOptionsBuilder<FakeDbContext>()
            .UseInMemoryDatabase(databaseName: "test")
            .Options;

        // Arrange
        var store = new IoTStateStore(new FakeDbContext(options));
        float expectedValue = 25.5f;
        long expectedTimestamp = 123456789;
        string expectedType = "temp";
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