using Microsoft.EntityFrameworkCore;
using IoTGrpcServer;

namespace MockDatabase;

public class MockDbContext : DbContext
{
    public MockDbContext(DbContextOptions<MockDbContext> options) : base(options)
    {
    }

    public DbSet<Room> Rooms => Set<Room>();
    public DbSet<Sensor> Sensors => Set<Sensor>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        const string schema = "chess_assistant";

        modelBuilder.Entity<Room>(entity =>
        {
            entity.ToTable("room", schema);
            entity.HasKey(r => r.Id);

            entity.Property(r => r.Id).HasColumnName("id");
            entity.Property(r => r.Perimeter).HasColumnName("perimeter");
            entity.Property(r => r.PlayerId).HasColumnName("player_id");
        });

        modelBuilder.Entity<Sensor>(entity =>
        {
            entity.ToTable("sensor", schema);
            entity.HasKey(s => s.Id);

            entity.Property(s => s.Id).HasColumnName("id");
            entity.Property(s => s.RoomId).HasColumnName("room_id");
            entity.Property(s => s.Type).HasColumnName("type");
            entity.Property(s => s.Value).HasColumnName("value");
            entity.Property(s => s.TimeStamp).HasColumnName("time_stamp");

            entity.HasOne(s => s.Room)
                .WithMany(r => r.Sensors)
                .HasForeignKey(s => s.RoomId);
        });
    }
}