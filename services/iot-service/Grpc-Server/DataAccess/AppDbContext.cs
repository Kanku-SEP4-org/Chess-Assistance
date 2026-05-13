namespace IoTGrpcServer;
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options){}
    public DbSet<CO2Sensor> CO2s {get; set;}
    public DbSet<LightSensor> Lights {get; set;}
    public DbSet<TemperatureSensor> Temperatures {get; set;}
    public DbSet<WaterSensor> Waters {get; set;}
    public DbSet<Room> Rooms {get; set;}

    public DbSet<Match> Matches {get; set;}

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.HasDefaultSchema("chess_assistant");
        
        modelBuilder.Entity<CO2Sensor>(entity =>
        {
            entity.ToTable("co2_sensor");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.TimeStamp).HasColumnName("time_stamp");
            entity.Property(e => e.Ppm).HasColumnName("ppm");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.MatchId).HasColumnName("match_id");

            entity.HasOne(e => e.Room).WithMany(r => r.CO2Sensors).HasForeignKey(e => e.RoomId);
            entity.HasOne(e => e.Match).WithMany(m => m.CO2Sensors).HasForeignKey(e => e.MatchId);
        });

        modelBuilder.Entity<LightSensor>(entity =>
        {
            entity.ToTable("light_sensor");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.TimeStamp).HasColumnName("time_stamp");
            entity.Property(e => e.Lumen).HasColumnName("lumen");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.MatchId).HasColumnName("match_id");

            entity.HasOne(e => e.Room).WithMany(r => r.LightSensors).HasForeignKey(e => e.RoomId);
            entity.HasOne(e => e.Match).WithMany(m => m.LightSensors).HasForeignKey(e => e.MatchId);
        });

        modelBuilder.Entity<TemperatureSensor>(entity =>
        {
            entity.ToTable("temperature_sensor");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.TimeStamp).HasColumnName("time_stamp");
            entity.Property(e => e.Celsius).HasColumnName("celsius");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.MatchId).HasColumnName("match_id");

            entity.HasOne(e => e.Room).WithMany(r => r.TemperatureSensors).HasForeignKey(e => e.RoomId);
            entity.HasOne(e => e.Match).WithMany(m => m.TemperatureSensors).HasForeignKey(e => e.MatchId);
        });

        modelBuilder.Entity<WaterSensor>(entity =>
        {
            entity.ToTable("water_sensor");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.TimeStamp).HasColumnName("time_stamp");
            entity.Property(e => e.Ml).HasColumnName("ml");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.MatchId).HasColumnName("match_id");

            entity.HasOne(e => e.Room).WithMany(r => r.WaterSensors).HasForeignKey(e => e.RoomId);
            entity.HasOne(e => e.Match).WithMany(m => m.WaterSensors).HasForeignKey(e => e.MatchId);
        });
    }
}