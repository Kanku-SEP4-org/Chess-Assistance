import { useEffect, useRef, useState } from "react";
import Navbar from "../components/Navbar";
import heroImg from "../assets/chess-bg.png";
import "../App.css";
import { API_URL } from "../config";

const heroTexts = ["Track your environment.", "Improve your game."];

function Home() {
  const [monitoringStarted, setMonitoringStarted] = useState(false);
  const [showSleepForm, setShowSleepForm] = useState(false);
  const [sleepTime, setSleepTime] = useState("");
  const [wakeTime, setWakeTime] = useState("");
  const [waterIntake, setWaterIntake] = useState("");
  const [alerts, setAlerts] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [endingSession, setEndingSession] = useState(false);
  const [lichessUser, setLichessUser] = useState(null);
  const [heroIndex, setHeroIndex] = useState(0);
  const [temperature, setTemperature] = useState(null);
  const [lightLevel, setLightLevel] = useState(null);
  const [co2Level, setCo2Level] = useState(null);
  const [totalWater, setTotalWater] = useState(0);
  const [addWaterAmount, setAddWaterAmount] = useState("");
  const [showAddWater, setShowAddWater] = useState(false);

  const sessionDates = useRef(null);

  useEffect(() => {
    const saved = localStorage.getItem("lichess_user");
    if (saved) {
      setLichessUser(JSON.parse(saved));
      fetch(`${API_URL}/auth/me`, { credentials: "include" })
        .then((r) => {
          if (!r.ok) {
            localStorage.removeItem("lichess_user");
            setLichessUser(null);
          }
        })
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setHeroIndex((prev) => (prev === heroTexts.length - 1 ? 0 : prev + 1));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

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
          setTemperature(tempData.value.toFixed(1));
        }
        if (lightRes.ok && lightData.value != null) {
          setLightLevel(lightData.value.toFixed(1));
        }
        if (co2Res.ok && co2Data.value != null) {
          setCo2Level(co2Data.value.toFixed(1));
        }
      } catch (err) {
        console.error("Failed to fetch sensor data:", err);
      }
    };

    fetchSensorData();
    const interval = setInterval(fetchSensorData, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handlePageHide = () => {
      if (!sessionId) return;
      const body = JSON.stringify({ session_id: sessionId });
      navigator.sendBeacon(
        `${API_URL}/session/end`,
        new Blob([body], { type: "application/json" }),
      );
    };

    window.addEventListener("pagehide", handlePageHide);
    return () => window.removeEventListener("pagehide", handlePageHide);
  }, [sessionId]);

  const buildDates = () => {
    const now = new Date();
    const [wh, wm] = wakeTime.split(":").map(Number);
    const [sh, sm] = sleepTime.split(":").map(Number);

    const wake = new Date(now);
    wake.setHours(wh, wm, 0, 0);
    if (wake > now) wake.setDate(wake.getDate() - 1);

    const sleep = new Date(wake);
    sleep.setHours(sh, sm, 0, 0);
    if (sleep >= wake) sleep.setDate(sleep.getDate() - 1);

    return { sleep, wake, now };
  };

  const handleStartSession = async () => {
    if (!sleepTime || !wakeTime) return;

    const dates = buildDates();
    sessionDates.current = dates;

    try {
      const res = await fetch(`${API_URL}/session/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sleep_time: dates.sleep.toISOString(),
          awaken_time: dates.wake.toISOString(),
          water_intake_ml: Number(waterIntake) || 0,
        }),
      });
      const data = await res.json();

      setAlerts({
        items: data.alerts,
        sleepDuration: data.sleep_duration,
        awakeDuration: data.awake_duration,
      });

      if (data.alerts.length === 0) {
        startSession();
      }
    } catch (err) {
      console.error("Evaluate error:", err);
      alert("Failed to evaluate readiness");
    }
  };

  const startSession = async () => {
    if (!lichessUser) return;
    setSessionLoading(true);

    const { sleep, wake, now } = sessionDates.current || buildDates();

    try {
      const res = await fetch(`${API_URL}/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          sleep_time: sleep.toISOString(),
          awaken_time: wake.toISOString(),
          confirmed_at: now.toISOString(),
          water_intake_initial_ml: Number(waterIntake) || 0,
        }),
      });
      if (res.status === 401) {
        localStorage.removeItem("lichess_user");
        setLichessUser(null);
        setShowSleepForm(false);
        setAlerts(null);
        alert("Your session expired — please log in again");
        return;
      }
      const data = await res.json();
      if (data.success) {
        setSessionId(data.session_id);
        setMonitoringStarted(true);
        setShowSleepForm(false);
        setAlerts(null);
        setTotalWater(Number(waterIntake) || 0);

        // Save minutes slept for Environment Recommendation page
        const { sleep, wake } = sessionDates.current || buildDates();
        const minutesSlept = Math.round((wake - sleep) / 60000);
        localStorage.setItem("session_minutes_slept", minutesSlept);
        const minutesAwake = Math.round((now - wake) / 60000);
        localStorage.setItem("session_minutes_awake", minutesAwake);
      } else {
        alert(data.message || "Failed to start session");
      }
    } catch (err) {
      console.error("StartSession error:", err);
      alert("Failed to connect to server");
    } finally {
      setSessionLoading(false);
    }
  };

  const handleEndSession = async () => {
    setEndingSession(true);
    try {
      const res = await fetch(`${API_URL}/session/end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (data.success) {
        setSessionId(null);
        setMonitoringStarted(false);

      } else {
        alert(data.message || "Failed to end session");
      }
    } catch (err) {
      console.error("EndSession error:", err);
      alert("Failed to connect to server");
    } finally {
      setEndingSession(false);
    }
  };

  return (
    <main className="app" style={{ backgroundImage: `url(${heroImg})` }}>
      <Navbar />

      <section
        id="home"
        className="hero-section"
        style={{ minHeight: monitoringStarted ? "auto" : "100vh" }}
      >
        <div className="hero-content">
          <p className="eyebrow">Chess Performance Assistant</p>
          <h1 className="hero-title-split">
            <span className="hero-line-wrapper">
              <span
                className={heroIndex === 0 ? "hero-line active" : "hero-line"}
              >
                Track
              </span>
              <span
                className={heroIndex === 1 ? "hero-line active" : "hero-line"}
              >
                Improve
              </span>
            </span>

            <span className="hero-static-line">Your</span>

            <span className="hero-line-wrapper">
              <span
                className={heroIndex === 0 ? "hero-line active" : "hero-line"}
              >
                Environment.
              </span>
              <span
                className={heroIndex === 1 ? "hero-line active" : "hero-line"}
              >
                Game.
              </span>
            </span>
          </h1>

          {!monitoringStarted && (
            <button
              className="start-btn"
              onClick={() => setMonitoringStarted(true)}
            >
              Start Monitoring
            </button>
          )}
        </div>
      </section>

      {showSleepForm && (
        <section className="sleep-card">
          <h2>Start Chess Session</h2>

          {!alerts ? (
            <>
              <div className="sleep-inputs">
                <div>
                  <p>Time you went to sleep</p>
                  <input
                    type="time"
                    value={sleepTime}
                    onChange={(e) => setSleepTime(e.target.value)}
                  />
                </div>

                <div>
                  <p>Time you woke up</p>
                  <input
                    type="time"
                    value={wakeTime}
                    onChange={(e) => setWakeTime(e.target.value)}
                  />
                </div>

                <div>
                  <p>Water intake so far (ml)</p>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    placeholder="e.g. 500"
                    value={waterIntake}
                    onChange={(e) => setWaterIntake(e.target.value)}
                  />
                </div>

                <button onClick={handleStartSession}>Start Session</button>
              </div>
            </>
          ) : (
            <div>
              <h3>Session Readiness Check</h3>
              <p>
                You slept <strong>{alerts.sleepDuration}</strong> and have been
                awake <strong>{alerts.awakeDuration}</strong>
              </p>

              {alerts.items.length === 0 ? (
                <p style={{ color: "#4caf50" }}>
                  All good — you're ready to play!
                </p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0, margin: "16px 0" }}>
                  {alerts.items.map((a, i) => (
                    <li
                      key={i}
                      style={{
                        color: a.level === "red" ? "#ff5252" : "#ffb300",
                        marginBottom: "8px",
                      }}
                    >
                      ● {a.message}
                    </li>
                  ))}
                </ul>
              )}

              <div className="sleep-inputs">
                <button onClick={startSession} disabled={sessionLoading}>
                  {sessionLoading
                    ? "Starting..."
                    : alerts.items.length > 0
                      ? "Start Anyway"
                      : "Start Session"}
                </button>
                {alerts.items.length > 0 && (
                  <button onClick={() => setAlerts(null)}>Cancel</button>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {monitoringStarted && (
        <section id="track" className="dashboard">
          {lichessUser && !sessionId ? (
            <button
              className="sleep-toggle-btn"
              onClick={() => setShowSleepForm(!showSleepForm)}
            >
              Start Chess Session
            </button>
          ) : !lichessUser ? (
            <p style={{ color: "#ffb300", marginBottom: "24px" }}>
              Log in with Lichess to start a session.
            </p>
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                marginBottom: "24px",
              }}
            >
              <p style={{ color: "#d8aa55", margin: 0 }}>
                Session #{sessionId} is active
              </p>
              <button
                className="sleep-toggle-btn"
                onClick={handleEndSession}
                disabled={endingSession}
              >
                {endingSession ? "Ending..." : "End Session"}
              </button>
            </div>
          )}

          <h2>Live Metrics</h2>

          <div className="cards-grid">
            <div className="metric-card">
              <span>Temperature</span>
              <strong>{temperature != null ? `${temperature}°C` : "—"}</strong>
            </div>

            <div className="metric-card">
              <span>Light Level</span>
              <strong>{lightLevel != null ? `${lightLevel} lux` : "—"}</strong>
            </div>

            <div className="metric-card">
              <span>CO2 Level</span>
              <strong>{co2Level != null ? `${co2Level} ppm` : "—"}</strong>
            </div>

            <div className="metric-card">
              <span>Water Drank</span>
              <strong>{totalWater} ml</strong>
              <div
                style={{
                  marginTop: "10px",
                  display: "flex",
                  gap: "8px",
                  alignItems: "center",
                }}
              >
                {showAddWater ? (
                  <>
                    <input
                      type="number"
                      min="0"
                      step="50"
                      placeholder="ml"
                      value={addWaterAmount}
                      onChange={(e) => setAddWaterAmount(e.target.value)}
                      style={{
                        width: "90px",
                        padding: "6px 10px",
                        borderRadius: "8px",
                        border: "1px solid rgba(255,255,255,0.14)",
                        background: "rgba(255,255,255,0.08)",
                        color: "white",
                        outline: "none",
                      }}
                    />
                    <button
                      aria-label="confirm water"
                      onClick={() => {
                        setTotalWater(
                          (prev) => prev + (Number(addWaterAmount) || 0),
                        );
                        setAddWaterAmount("");
                        setShowAddWater(false);
                      }}
                      style={{
                        padding: "6px 12px",
                        borderRadius: "8px",
                        border: "none",
                        background: "linear-gradient(135deg, #d8aa55, #8f6425)",
                        color: "#111",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      ✓
                    </button>
                    <button
                      aria-label="cancel water"
                      onClick={() => setShowAddWater(false)}
                      style={{
                        padding: "6px 10px",
                        borderRadius: "8px",
                        border: "1px solid rgba(255,255,255,0.14)",
                        background: "transparent",
                        color: "white",
                        cursor: "pointer",
                      }}
                    >
                      ✕
                    </button>
                  </>
                ) : (
                  <button
                    aria-label="add water"
                    onClick={() => setShowAddWater(true)}
                    style={{
                      padding: "4px 12px",
                      borderRadius: "8px",
                      border: "1px solid rgba(216,170,85,0.5)",
                      background: "transparent",
                      color: "#d8aa55",
                      fontWeight: 800,
                      cursor: "pointer",
                      fontSize: "18px",
                    }}
                  >
                    +
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="session-card">
            <div>
              <p className="eyebrow">Current Session</p>
              <h2>Session Performance</h2>
              <p>Tracking your chess performance during this play session.</p>
            </div>

            <div className="session-stats">
              <div>
                <span>Games</span>
                <strong>5</strong>
              </div>
              <div>
                <span>Wins</span>
                <strong>3</strong>
              </div>
              <div>
                <span>Losses</span>
                <strong>2</strong>
              </div>
              <div>
                <span>Win Rate</span>
                <strong>60%</strong>
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

export default Home;
