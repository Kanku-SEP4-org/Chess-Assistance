import { useState } from 'react';
import './App.css';

const BASE_URL = 'http://localhost:8000';

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
            sleep_minutes: Number(sleepMinutes),
            awake_minutes: Number(awakeMinutes),
          }),
        }),
        fetch(`${BASE_URL}/iot/temp?id=${arduinoId}`),
      ]);

      const predictionData = await predictionRes.json();
      const tempData = await tempRes.json();

      setResult({ chance: predictionData.chance, temperature: tempData });
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
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Sleep Duration (minutes)</label>
              <input
                type="number"
                className="form-control"
                value={sleepMinutes}
                onChange={(e) => setSleepMinutes(e.target.value)}
                min="0"
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Time Awake (minutes)</label>
              <input
                type="number"
                className="form-control"
                value={awakeMinutes}
                onChange={(e) => setAwakeMinutes(e.target.value)}
                min="0"
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Arduino ID</label>
              <input
                type="number"
                className="form-control"
                value={arduinoId}
                onChange={(e) => setArduinoId(e.target.value)}
                min="0"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-100" disabled={loading}>
              {loading ? 'Loading...' : 'Get Prediction'}
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mx-auto mt-4" style={{ maxWidth: '480px' }}>
          {error}
        </div>
      )}

      {result && (
        <div className="row justify-content-center mt-4 g-3" style={{ maxWidth: '480px', margin: '1rem auto 0' }}>
          <div className="col-6">
            <div className="card text-center">
              <div className="card-body">
                <h6 className="card-subtitle mb-1 text-muted">Win Chance</h6>
                <h2 className="card-title text-success">{result.chance}%</h2>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="card text-center">
              <div className="card-body">
                <h6 className="card-subtitle mb-1 text-muted">Temperature</h6>
                <h2 className="card-title text-info">{JSON.stringify(result.temperature)}</h2>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
