namespace IoTGrpcServer;
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options){}
    public DbSet<Sensor> Sensors {get; set;}
    public DbSet<Room> Rooms {get; set;}

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.HasDefaultSchema("chess_assistant");
        
        modelBuilder.Entity<Sensor>(entity =>
        {
            entity.ToTable("sensor");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.TimeStamp).HasColumnName("timestamp");
            entity.Property(e => e.Value).HasColumnName("value");
            entity.Property(e => e.RoomId).HasColumnName("room_id");
            entity.Property(e => e.Type).HasColumnName("type");

            entity.HasOne(e => e.Room).WithMany(r => r.Sensors).HasForeignKey(e => e.Room);
        });

        modelBuilder.Entity<Room>(entity =>
        {
            entity.ToTable("room");
            entity.HasKey(e => e.Id);

            entity.Property(e => e.Perimeter).HasColumnName("perimeter");
            entity.Property(e => e.PlayerId).HasColumnName("player_id");
            entity.HasMany(e => e.Sensors);
        });
    }
}