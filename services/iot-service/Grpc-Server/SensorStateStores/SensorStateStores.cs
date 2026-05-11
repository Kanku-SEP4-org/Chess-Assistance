namespace IoTGrpcServer;

public class SensorStateStores
{
    private readonly Dictionary<string, IIoTStateStore> _stores;

    public SensorStateStores()
    {
        _stores = new Dictionary<string, IIoTStateStore>
        {
            {"temp", new TemperatureStateStore()},
            {"light", new LightStateStore()}
        };
    }
    public IIoTStateStore GetStore(string type)
    {   
    return _stores[type];
    }
}