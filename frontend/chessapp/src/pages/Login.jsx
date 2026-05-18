import React from 'react'
import './Login.css'

const CLIENT_ID = 'chess-assistance'
const REDIRECT_URI = 'http://localhost:3000/callback'

function generateCodeVerifier() {
  const array = new Uint8Array(64)
  window.crypto.getRandomValues(array)

  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

async function generateCodeChallenge(codeVerifier) {
  const encoder = new TextEncoder()
  const data = encoder.encode(codeVerifier)
  const digest = await window.crypto.subtle.digest('SHA-256', data)

  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

function Login() {
  const handleLichessLogin = async () => {
    const codeVerifier = generateCodeVerifier()
    const codeChallenge = await generateCodeChallenge(codeVerifier)

    sessionStorage.setItem('lichess_code_verifier', codeVerifier)

    const params = new URLSearchParams({
      response_type: 'code',
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      scope: '',
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    })

    window.location.href = `https://lichess.org/oauth?${params.toString()}`
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