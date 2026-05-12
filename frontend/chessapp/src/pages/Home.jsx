
import { useState, useRef, useEffect } from "react";
import { Crown, User, History, Settings, TrendingUp } from "lucide-react";
import { Link } from 'react-router-dom'
import heroImg from '../assets/chess-bg.png'
import knightLogo from "../assets/knight-logo.png";
import '../App.css'

function Home() {
  const [monitoringStarted, setMonitoringStarted] = useState(false)
  const [username, setUsername] = useState('')
  const [playerStats, setPlayerStats] = useState(null)
  const [playerError, setPlayerError] = useState('')
  const [playerLoading, setPlayerLoading] = useState(false)

  const handlePlayerSearch = async (e) => {
  e.preventDefault()

  if (!username.trim()) {
    setPlayerError('Please enter a Chess.com username.')
    return
  }

  setPlayerLoading(true)
  setPlayerError('')
  setPlayerStats(null)

  try {
    const response = await fetch(
      `https://api.chess.com/pub/player/${username.trim().toLowerCase()}/stats`
    )

    if (!response.ok) {
      throw new Error('Player not found')
    }

    const data = await response.json()
    setPlayerStats(data)
  } catch (error) {
    setPlayerError('Could not find this Chess.com player.')
  } finally {
    setPlayerLoading(false)
  }
}
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
    <img
      src={knightLogo}
      alt="Knight Menu"
      className="knight-icon"
    />
  </button>

  {menuOpen && (
    <div className="profile-dropdown">
      <button>👤 My Profile</button>
      <button>📈 View Sessions</button>
      <button>♟️ Elo Boosting</button>
      <button>⚙️ Settings</button>
    </div>
  )}
</div>
        </div>
      </nav>

      <section id="home" className="hero-section">
    

        <div className="hero-content">
          <p className="eyebrow">Chess Performance Assistant</p>
          <h1>Track your environment. Improve your game.</h1>
          


          <button
            className="start-btn"
            onClick={() => setMonitoringStarted(true)}
          >
            Start Monitoring
          </button>
        </div>
      </section>

      {monitoringStarted && (
        <section id="track" className="dashboard">
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
              <div><span>Games</span><strong>5</strong></div>
              <div><span>Wins</span><strong>3</strong></div>
              <div><span>Losses</span><strong>2</strong></div>
              <div><span>Win Rate</span><strong>60%</strong></div>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}

export default Home