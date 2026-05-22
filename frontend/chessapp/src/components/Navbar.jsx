import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import knightLogo from '../assets/knight-logo.png'
import { API_URL } from '../config'

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
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

  const DropdownMenu = () => (
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
  )

  return (
    <nav className="navbar navbar-expand-md">
      <div className="container-fluid px-4">

        {/* Logo — always visible */}
        <div className="logo">ChessTrack™</div>

        {/* Mobile only: knight icon + hamburger always visible */}
        <div className="d-flex align-items-center gap-3 d-md-none">
          <div className="profile-menu-container">
            <button
              className="settings-btn"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              <img src={knightLogo} alt="Knight Menu" className="knight-icon" />
            </button>
            {menuOpen && <DropdownMenu />}
          </div>

          <button
            className="navbar-toggler border-0 shadow-none"
            type="button"
            onClick={() => setNavOpen(!navOpen)}
            style={{ filter: 'invert(1)' }}
          >
            <span className="navbar-toggler-icon" />
          </button>
        </div>

        {/* Collapsible links */}
        <div className={`collapse navbar-collapse ${navOpen ? 'show' : ''}`}>
          <div className="nav-links ms-auto">
            <Link to="/" onClick={() => setNavOpen(false)}>Home</Link>
            <a href="#about" onClick={() => setNavOpen(false)}>About</a>
            <Link to="/chesstrack" onClick={() => setNavOpen(false)}>ChessTrack</Link>
            <Link to="/angriness" onClick={() => setNavOpen(false)}>Tilt Predictor</Link>

            {/* Desktop only: knight icon inside nav links */}
            <div className="profile-menu-container d-none d-md-flex">
              <button
                className="settings-btn"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <img src={knightLogo} alt="Knight Menu" className="knight-icon" />
              </button>
              {menuOpen && <DropdownMenu />}
            </div>
          </div>
        </div>

      </div>
    </nav>
  )
}

export default Navbar