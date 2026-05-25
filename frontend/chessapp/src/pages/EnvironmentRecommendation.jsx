import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import { ML_API_URL, API_URL } from "../config";
import "../App.css";

const initialForm = {
  minutes_slept: 540,
  minutes_awake: 120,
  temperature_celsius: 21,
  co2: 1300,
  light: 1500,
};

const FACTOR_LABELS = {
  temperature_celsius: "Temperature",
  co2: "CO2",
  light: "Light",
};

const FACTOR_UNITS = {
  temperature_celsius: "C",
  co2: "ppm",
  light: "lux",
};

function formatFactorValue(factor, value) {
  if (value == null) return "N/A";
  const unit = FACTOR_UNITS[factor];
  return unit ? `${value} ${unit}` : value;
}

function EnvironmentRecommendation() {
  const [form, setForm] = useState(initialForm);
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSensorData = async () => {
      try {
        const [tempRes, lightRes, co2Res] = await Promise.all([
          fetch(`${API_URL}/iot/temp?id=1`),
          fetch(`${API_URL}/iot/light?id=1`),
          fetch(`${API_URL}/iot/co2?id=1`),
        ]);
        const tempData = await tempRes.json();
        const lightData = await lightRes.json();
        const co2Data = await co2Res.json();
        if (tempRes.ok && tempData.value != null) {
          updateField("temperature_celsius", tempData.value.toFixed(1));
        }
        if (lightRes.ok && lightData.value != null) {
          updateField("light", lightData.value.toFixed(1));
        }
        if (co2Res.ok && co2Data.value != null) {
          updateField("co2", co2Data.value.toFixed(1));
        }
      } catch (err) {
        console.error("Failed to fetch sensor data:", err);
      }
    };
    fetchSensorData();
    const savedMinutesSlept = localStorage.getItem("session_minutes_slept");
    if (savedMinutesSlept) {
      updateField("minutes_slept", Number(savedMinutesSlept));
    }

    const savedMinutesAwake = localStorage.getItem("session_minutes_awake");
    if (savedMinutesAwake) {
      updateField("minutes_awake", Number(savedMinutesAwake));
    }
  }, []);

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setRecommendation(null);

    try {
      const response = await fetch(`${ML_API_URL}/recommendations/environment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          minutes_slept: Number(form.minutes_slept),
          minutes_awake: Number(form.minutes_awake),
          temperature_celsius: Number(form.temperature_celsius),
          co2: Number(form.co2),
          light: Number(form.light),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "Recommendation failed.");
      }

      setRecommendation(data);
    } catch (err) {
      setError(err.message || "Could not connect to the ML API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="track-page environment-page">
        <section className="track-hero">
          <p className="eyebrow">Environment Recommendation</p>
          <h1>Improve your playing setup</h1>
          <p>
            Enter your sleep and room conditions to see which single
            environmental factor may improve your predicted win probability.
          </p>

          <form className="recommendation-form" onSubmit={handleSubmit}>
            <div className="recommendation-grid">
              <label>
                <span>Minutes Slept</span>
                <input
                  type="number"
                  value={form.minutes_slept}
                  readOnly
                  min="0"
                  style={{ opacity: 0.7, cursor: "not-allowed" }}
                />
              </label>

              <label>
                <span>Minutes Awake</span>
                <input
                  type="number"
                  value={form.minutes_awake}
                  readOnly
                  onChange={(e) => updateField("minutes_awake", e.target.value)}
                  min="0"
                />
              </label>

              <label>
                <span>Temperature</span>
                <input
                  type="number"
                  value={form.temperature_celsius}
                  readOnly
                  step="0.1"
                  style={{ opacity: 0.7, cursor: "not-allowed" }}
                />
              </label>

              <label>
                <span>CO2</span>
                <input
                  type="number"
                  value={form.co2}
                  readOnly
                  min="0"
                  style={{ opacity: 0.7, cursor: "not-allowed" }}
                />
              </label>

              <label>
                <span>Light</span>
                <input
                  type="number"
                  value={form.light}
                  readOnly
                  min="0"
                  style={{ opacity: 0.7, cursor: "not-allowed" }}
                />
              </label>
            </div>

            <button type="submit" disabled={loading}>
              {loading ? "Checking..." : "Get Recommendation"}
            </button>
          </form>

          {error && <p className="player-error">{error}</p>}
        </section>

        {recommendation && (
          <section className="player-results">
            <div className="session-card recommendation-summary">
              <div>
                <p className="eyebrow">Recommended Action</p>
                <h2>
                  {recommendation.recommended_factor
                    ? FACTOR_LABELS[recommendation.recommended_factor]
                    : "No change recommended"}
                </h2>
                <p>{recommendation.message}</p>
              </div>

              <div className="session-stats recommendation-stats">
                <div>
                  <span>Current</span>
                  <strong>{recommendation.current_win_probability}</strong>
                </div>
                <div>
                  <span>Improved</span>
                  <strong>
                    {recommendation.improved_win_probability ?? "N/A"}
                  </strong>
                </div>
                <div>
                  <span>Increase</span>
                  <strong>
                    {recommendation.increase_percentage_points != null
                      ? `${recommendation.increase_percentage_points} pp`
                      : "0 pp"}
                  </strong>
                </div>
              </div>
            </div>

            {recommendation.recommended_factor && (
              <div className="cards-grid recommendation-cards">
                <div className="metric-card">
                  <span>Factor</span>
                  <strong>
                    {FACTOR_LABELS[recommendation.recommended_factor]}
                  </strong>
                  <p>Best positive model response.</p>
                </div>
                <div className="metric-card">
                  <span>Current Value</span>
                  <strong>
                    {formatFactorValue(
                      recommendation.recommended_factor,
                      recommendation.current_value,
                    )}
                  </strong>
                  <p>Current input value.</p>
                </div>
                <div className="metric-card">
                  <span>Recommended Value</span>
                  <strong>
                    {formatFactorValue(
                      recommendation.recommended_factor,
                      recommendation.recommended_value,
                    )}
                  </strong>
                  <p>Target tested by the model.</p>
                </div>
                <div className="metric-card">
                  <span>Probability Gain</span>
                  <strong>{recommendation.increase}</strong>
                  <p>Raw probability increase.</p>
                </div>
              </div>
            )}

            <div className="candidate-list">
              <p className="eyebrow">All Candidates</p>
              {recommendation.all_candidates?.map((candidate) => (
                <div key={candidate.factor} className="candidate-row">
                  <div>
                    <strong>{FACTOR_LABELS[candidate.factor]}</strong>
                    <p>
                      {formatFactorValue(
                        candidate.factor,
                        candidate.current_value,
                      )}
                      {" -> "}
                      {formatFactorValue(
                        candidate.factor,
                        candidate.recommended_value,
                      )}
                    </p>
                  </div>
                  <div>
                    <span>Win probability</span>
                    <strong>{candidate.win_probability}</strong>
                  </div>
                  <div>
                    <span>Increase</span>
                    <strong>{candidate.increase_percentage_points} pp</strong>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}

export default EnvironmentRecommendation;
