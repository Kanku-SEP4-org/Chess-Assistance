import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import knightLogo from "../assets/knight-logo.png";
import { API_URL } from "../config";
import lichessLogo from "../assets/lichess-logo.png";

function Navbar({ onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [lichessUser, setLichessUser] = useState(null)

  useEffect(() => {
    const savedUser = localStorage.getItem("lichess_user");
    if (savedUser) {
      setLichessUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogout = async () => {
    const activeSessionId = localStorage.getItem('active_session_id')
    if (activeSessionId) {
      navigator.sendBeacon(
        `${API_URL}/session/end`,
        new Blob([JSON.stringify({ session_id: Number(activeSessionId) })], { type: 'text/plain' }),
      )
      localStorage.removeItem('active_session_id')
    }
    try {
      await fetch(`${API_URL}/auth/lichess/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (_) {}
    localStorage.removeItem('lichess_user')
    setLichessUser(null)
    onLogout?.()
  }

  const DropdownMenu = () => (
    <div className="profile-dropdown">
      {lichessUser ? (
         <button>
          <img
            src={lichessLogo}
            alt="Lichess"
            style={{ width: "18px", height: "18px", filter: "invert(1)" }}
          />
          {lichessUser.player_username}
        </button>
      ) : (
        <Link to="/login">
          <button>
            <img
              src={lichessLogo}
              alt="Lichess"
              style={{ width: "18px", height: "18px", filter: "invert(1)" }}
            />
            Login
          </button>
        </Link>
      )}
      <Link to="/iot-dashboard">
        <button>♜ IoT Dashboard</button>
      </Link>
      <Link to="/preferences">
        <button>⚙️ Player Preference</button>
      </Link>
      {lichessUser && <button onClick={handleLogout}>🚪 Logout</button>}
    </div>
  );

  return (
    <nav className="navbar navbar-expand-md">
      <div className="container-fluid px-4">
        {/* Logo — always visible */}
        <div className="logo">ChessTrack™</div>

        {/* Mobile only: knight icon + hamburger always visible */}
        <div className="d-flex align-items-center gap-3 d-md-none">
          <div className="profile-menu-container">
            <button
              aria-label="open menu"
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
            style={{ filter: "invert(1)" }}
          >
            <span className="navbar-toggler-icon" />
          </button>
        </div>

        {/* Collapsible links */}
        <div className={`collapse navbar-collapse ${navOpen ? "show" : ""}`}>
          <div className="nav-links ms-auto">
            <Link to="/" onClick={() => setNavOpen(false)}>
              Home
            </Link>
            <Link to="/chesstrack" onClick={() => setNavOpen(false)}>
              ChessTrack
            </Link>
            <Link to="/angriness" onClick={() => setNavOpen(false)}>
              Tilt Predictor
            </Link>
            <Link to="/recommend-environment" onClick={() => setNavOpen(false)}>
              Environment
            </Link>

            {/* Desktop only: knight icon inside nav links */}
            <div className="profile-menu-container d-none d-md-flex">
              <button
                aria-label="open menu"  
                className="settings-btn"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <img
                  src={knightLogo}
                  alt="Knight Menu"
                  className="knight-icon"
                />
              </button>
              {menuOpen && <DropdownMenu />}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
