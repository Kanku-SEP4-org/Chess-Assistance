import { useEffect, useState } from 'react';
import './App.css';
import PredForm from './PredForm';
import LightSensor from './LightSensor';

const BASE_URL = 'http://localhost:3001';

function App() {
  const [sleepMinutes, setSleepMinutes] = useState('');
  const [awakeMinutes, setAwakeMinutes] = useState('');
  const [arduinoId, setArduinoId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [co2Level] = useState(1200);
  const [co2Threshold] = useState(1000);
  const [windowState, setWindowState] = useState('Closed');
  const [windowNotification, setWindowNotification] = useState('');
  const [lastOpeningAngle, setLastOpeningAngle] = useState(0);

  useEffect(() => {
  if (co2Level > co2Threshold) {
    setWindowNotification('Window is going to open...');

    setTimeout(() => {
      setWindowState('Open');
      setLastOpeningAngle(45);
      setWindowNotification('Window is open');
    }, 5000);
  }
}, [co2Level, co2Threshold]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const [predictionRes, tempRes] = await Promise.all([
        fetch(`${BASE_URL}/model/winrate/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            minutes_slept: Number(sleepMinutes),
            minutes_awake: Number(awakeMinutes),
            arduino_id: Number(arduinoId),
          }),
        }),
        fetch(`${BASE_URL}/iot/temp?id=${arduinoId}`),
      ]);

      const predictionData = await predictionRes.json();
      const tempData = await tempRes.json();

      setResult({ chance: predictionData.predictionWinrate, temperature: tempData });
    } catch (err) {
      setError('Failed to fetch data. Make sure the API is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container d-flex flex-column align-items-center justify-content-center min-vh-100">
      <h1 className="mb-4 text-center">Chess Win Predictor</h1>

      <div className="card mx-auto" style={{ maxWidth: '480px' }}>
        <div className="card-body">
          <PredForm
            sleepMinutes={sleepMinutes}
            setSleepMinutes={setSleepMinutes}
            awakeMinutes={awakeMinutes}
            setAwakeMinutes={setAwakeMinutes}
            arduinoId={arduinoId}
            setArduinoId={setArduinoId}
handleSubmit={handleSubmit}
            loading={loading}
          />
        </div>
      </div>

      {error && <div className="alert alert-danger mt-3">{error}</div>}

      {result && (
        <div className="card mt-4 mx-auto text-center" style={{ maxWidth: '480px' }}>
          <div className="card-body">
            <h4>Win Rate: {result.chance}%</h4>
            <p>Temperature: {result.temperature?.value ?? 'N/A'} °C</p>
          </div>
        </div>
      )} 

      <div className="card mt-4 mx-auto text-center" style={{ maxWidth: '480px' }}>
  <div className="card-body">
    <h4>Window</h4>

    <p>
      <strong>Window State:</strong> {windowState}
    </p>

    <p>
      <strong>CO2 Level:</strong> {co2Level} ppm
    </p>

    <p>
      <strong>Threshold:</strong> {co2Threshold} ppm
    </p>

    <p>
      <strong>Last Opening Angle:</strong> {lastOpeningAngle}°
    </p>

    <p>
      <strong>Notification:</strong> {windowNotification}
    </p>
  </div>
</div>
<LightSensor />
    </div>
  );
}

export default App;