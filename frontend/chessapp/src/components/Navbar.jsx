import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import knightLogo from '../assets/knight-logo.png'
import { API_URL } from '../config'

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [lichessUser, setLichessUser] = useState(null)

  useEffect(() => {
    const savedUser = localStorage.getItem('lichess_user')
    if (savedUser) {
      setLichessUser(JSON.parse(savedUser))
    }
  }, [])

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/lichess/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch (_) {}
    localStorage.removeItem('lichess_user')
    setLichessUser(null)
  }

  return (
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
                <button>👤 {lichessUser.player_username}</button>
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
              <Link to="/preferences">
                <button>🎮 Player Preference</button>
              </Link>
              {lichessUser && (
                <button onClick={handleLogout}>🚪 Logout</button>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar