using Google.Protobuf.WellKnownTypes;
using IoTGrpcServer;
using Microsoft.Net.Http.Headers;

public class AppDbContext : DbContext
{
    public DbSet<CO2SensorEntity> CO2s {get; set;}
    public DbSet<LightSensorEntity> Lights {get; set;}
    public DbSet<TemperatureSensorEntity> Temperatures {get; set;}
    public DbSet<WaterSensorEntity> Waters {get; set;}

    protected override void OnConfiguring(DbContextOptionsBuilder optionBuilder)
    {
        optionBuilder.UseSQL("Data Source"); //not sure how to do this
    }
}