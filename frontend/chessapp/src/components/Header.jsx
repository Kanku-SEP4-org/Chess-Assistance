import { useState } from 'react';
import { Link } from 'react-router-dom';
import knightLogo from '../assets/knight-logo.png';

function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="navbar navbar-expand-lg fixed-top bg-black backdrop-blur border-bottom border-white border-opacity-10" style={{ padding: '24px 64px' }}>
      <div className="navbar-brand fw-bold fs-4 text-white">
        <a href="/" className="nav-link text-white">ChessTrack™</a>
      </div>

      <div className="navbar-nav ms-auto d-flex align-items-center gap-4" >
        <Link to="/chesstrack" className="nav-link text-white">ChessTrack</Link>
        <Link to="/iot" className="nav-link text-white">IoT Dashboard</Link>
        <Link to="/iot" className="nav-link text-white">About</Link>

        <div className="dropdown position-relative">
          <button
            className="btn btn-link text-white p-0"
            onClick={() => setMenuOpen(!menuOpen)}
            style={{ fontSize: '20px' }}
          >
            <img
              src={knightLogo}
              alt="Knight Menu"
              style={{ width: '50px', height: '50px', objectFit: 'contain', transition: 'transform 0.2s ease' }}
              className="hover-scale"
            />
          </button>

          {menuOpen && (
            <div className="dropdown-menu show position-absolute end-0 mt-2 p-2 bg-black bg-opacity-90 backdrop-blur border border-white border-opacity-10 rounded-3 shadow-lg" style={{ width: '230px', zIndex: 1000 }}>
              <Link to="/iot" className="dropdown-item text-white d-flex align-items-center gap-2 py-3 px-3 rounded-2 text-decoration-none" onClick={() => setMenuOpen(false)}>👤 My Profile</Link>
              <Link to="/iot" className="dropdown-item text-white d-flex align-items-center gap-2 py-3 px-3 rounded-2 text-decoration-none" onClick={() => setMenuOpen(false)}>📈 View Sessions</Link>
              <Link to="/iot" className="dropdown-item text-white d-flex align-items-center gap-2 py-3 px-3 rounded-2 text-decoration-none" onClick={() => setMenuOpen(false)}>📡 IoT Dashboard</Link>
              <Link to="/preferences" className="dropdown-item text-white d-flex align-items-center gap-2 py-3 px-3 rounded-2 text-decoration-none" onClick={() => setMenuOpen(false)}>⚙️ Preferences</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Header;