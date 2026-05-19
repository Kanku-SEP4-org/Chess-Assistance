import { useEffect, useState } from 'react';

function LightSensor() {
  const [lightLevel, setLightLevel] = useState(40);
  const [preferredLight, setPreferredLight] = useState(60);

  const [lampBrightness, setLampBrightness] = useState(0);
  const [lampStatus, setLampStatus] = useState('OFF');

  const [notification, setNotification] = useState('');

  // Mock states
  const [sensorWorking] = useState(true);
  const [lampConnected] = useState(true);

  // Simulate sensor values
  useEffect(() => {
    const interval = setInterval(() => {
      const randomLight = Math.floor(Math.random() * 100);

      setLightLevel(randomLight);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Smart light logic
  useEffect(() => {
    if (!sensorWorking) {
      setNotification('Light sensor not responding');
      return;
    }

    if (!lampConnected) {
      setNotification('Lamp connection failed');
      return;
    }

    if (lightLevel < preferredLight) {
      const brightnessNeeded = preferredLight - lightLevel;

      setLampBrightness(brightnessNeeded);
      setLampStatus('ON');
      setNotification('Lamp brightness increased');
    } 
    
    else if (lightLevel > preferredLight) {
      setLampBrightness(0);
      setLampStatus('OFF');
      setNotification('Lamp turned off');
    } 
    
    else {
      setNotification('Light level is optimal');
    }
  }, [lightLevel, preferredLight, sensorWorking, lampConnected]);

  return (
    <div
      className="card mt-4 mx-auto"
      style={{maxwidth: '480px' }}
    >
      <div className="card-body text-center">
        <h4>Light</h4>

        <p>
          <strong>Current Light Level:</strong> {lightLevel}
        </p>

        <p>
          <strong>Preferred Level:</strong> {preferredLight}
        </p>

        <p>
          <strong>Lamp Status:</strong> {lampStatus}
        </p>

        <p>
          <strong>Brightness:</strong> {lampBrightness}%
        </p>

        <p>
          <strong>Notification:</strong> {notification}
        </p>

        <div className="mt-3">
          <label className="form-label">
            Preferred Light Level
          </label>

          <input
            type="range"
            min="0"
            max="100"
            value={preferredLight}
            onChange={(e) =>
              setPreferredLight(Number(e.target.value))
            }
            className="form-range"
          />
        </div>
      </div>
    </div>
  );
}

export default LightSensor;