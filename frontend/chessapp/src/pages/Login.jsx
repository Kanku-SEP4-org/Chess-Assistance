import React from 'react'
import './Login.css'

function Login() {
  const handleLichessLogin = () => {
    alert('Lichess OAuth coming next step')
  }

  return (
    <main className="login-page">
      <div className="login-card">
        <p className="login-eyebrow">ChessTrack™</p>

        <h1>Login with Lichess</h1>

        <p className="login-text">
          Connect your Lichess account to track your chess activity and
          performance.
        </p>

        <button
          className="login-button"
          onClick={handleLichessLogin}
        >
          Login with Lichess
        </button>
      </div>
    </main>
  )
}

export default Login