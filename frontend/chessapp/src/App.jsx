import { useState } from 'react';
import './App.css';
import PredForm from './PredForm';

const BASE_URL = 'http://localhost:3001';

function App() {
  const [sleepMinutes, setSleepMinutes] = useState('');
  const [awakeMinutes, setAwakeMinutes] = useState('');
  const [arduinoId, setArduinoId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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
    </div>
  );
}

export default App;