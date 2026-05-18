import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import heroImg from "../assets/chess-bg.png";
import knightLogo from "../assets/knight-logo.png";
import "../App.css";

const heroTexts = ["Track your environment.", "Improve your game."]

function Home() {
  const [monitoringStarted, setMonitoringStarted] = useState(false);
  const [showSleepForm, setShowSleepForm] = useState(false);
  const [sleepTime, setSleepTime] = useState("");
  const [wakeTime, setWakeTime] = useState("");
  const [sleepResult, setSleepResult] = useState("");

  const [heroIndex, setHeroIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setHeroIndex((prev) => (prev === heroTexts.length - 1 ? 0 : prev + 1));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const calculateSleepTime = () => {
    if (!sleepTime || !wakeTime) return;

    const [sleepHour, sleepMinute] = sleepTime.split(":").map(Number);
    const [wakeHour, wakeMinute] = wakeTime.split(":").map(Number);

    let sleepTotal = sleepHour * 60 + sleepMinute;
    let wakeTotal = wakeHour * 60 + wakeMinute;

    if (wakeTotal <= sleepTotal) {
      wakeTotal += 24 * 60;
    }

    const totalMinutes = wakeTotal - sleepTotal;
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    setSleepResult(`${hours}h ${minutes}m`);
  };

  // const handlePlayerSearch = async (e) => {
  //   e.preventDefault()
  //   if (!username.trim()) {
  //     setPlayerError('Please enter a Chess.com username.')
  //     return
  //   }
  //   setPlayerLoading(true)
  //   setPlayerError('')
  //   setPlayerStats(null)
  //   try {
  //     const response = await fetch(
  //       `https://api.chess.com/pub/player/${username.trim().toLowerCase()}/stats`
  //     )
  //     if (!response.ok) throw new Error('Player not found')
  //     const data = await response.json()
  //     setPlayerStats(data)
  //   } catch (error) {
  //     setPlayerError('Could not find this Chess.com player.')
  //   } finally {
  //     setPlayerLoading(false)
  //   }
  // }

  const [lichessUser, setLichessUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("lichess_user");

    if (savedUser) {
      setLichessUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("lichess_user");
    setLichessUser(null);
  };

  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <main className="app" style={{ backgroundImage: `url(${heroImg})` }}>
      <nav className="navbar">
        <div className="logo">ChessTrack™</div>

        <div className="nav-links">
          <Link to="/">Home</Link>
          <a href="#about">About</a>
          <Link to="/chesstrack">ChessTrack</Link>

          <div className="profile-menu-container">
            <button
              className="settings-btn"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              <img src={knightLogo} alt="Knight Menu" className="knight-icon" />
            </button>

            {menuOpen && (
              <div className="profile-dropdown">
                {lichessUser ? (
                  <>
                    <button>👤 {lichessUser.player_username}</button>
                  </>
                ) : (
                  <Link to="/login">
                    <button>👤 Login</button>
                  </Link>
                )}
                <button>📈 View Sessions</button>
                <button>♟️ Elo Boosting</button>
                <button>⚙️ Settings</button>
                <Link to="/iot-dashboard">
                  <button>🌐 IoT Dashboard</button>
                </Link>
                {lichessUser && (
                  <button onClick={handleLogout}>🚪 Logout</button>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>

      <section id="home" className="hero-section">
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

          <button
            className="start-btn"
            onClick={() => setMonitoringStarted(true)}
          >
            Start Monitoring
          </button>
        </div>
      </section>

      {showSleepForm && (
        <section className="sleep-card">
          <h2>Sleep Tracker</h2>

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

            <button onClick={calculateSleepTime}>Calculate Sleep</button>
          </div>

          {sleepResult && (
            <p>
              You slept for: <strong>{sleepResult}</strong>
            </p>
          )}
        </section>
      )}

      {monitoringStarted && (
        <section id="track" className="dashboard">
          {monitoringStarted && (
            <button
              className="sleep-toggle-btn"
              onClick={() => setShowSleepForm(!showSleepForm)}
            >
              How much time did I sleep?
            </button>
          )}
          <h2>Live Metrics</h2>

          <div className="cards-grid">
            <div className="metric-card">
              <span>Temperature</span>
              <strong>22°C</strong>
              <p>Optimal playing condition</p>
            </div>

            <div className="metric-card">
              <span>CO2 Level</span>
              <strong>820 ppm</strong>
              <p>Room air quality is stable</p>
            </div>

            <div className="metric-card">
              <span>Light Level</span>
              <strong>74%</strong>
              <p>Good visibility for focus</p>
            </div>

            <div className="metric-card">
              <span>Focus Score</span>
              <strong>86%</strong>
              <p>Ready for a strong session</p>
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
