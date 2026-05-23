import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './Login.css'
import { API_URL } from '../config'

function Callback() {
  const [status, setStatus] = useState('Completing Lichess login...')
  const [username, setUsername] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const completeLogin = async () => {
      const params = new URLSearchParams(window.location.search)

      const code = params.get('code')
      const error = params.get('error')

      if (error) {
        setStatus(`Lichess login failed: ${error}`)
        return
      }

      if (!code) {
        setStatus('No authorization code found.')
        return
      }

      const codeVerifier = sessionStorage.getItem('lichess_code_verifier')

      if (!codeVerifier) {
        setStatus('Missing PKCE code verifier.')
        return
      }

      // Clear verifier immediately so it can't be reused
      sessionStorage.removeItem('lichess_code_verifier')

      try {
        const response = await fetch(`${API_URL}/auth/lichess/callback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ code, code_verifier: codeVerifier }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.error || 'Lichess login failed')
        }

        localStorage.setItem('lichess_user', JSON.stringify({
          player_id: data.player_id,
          player_username: data.player_username,
        }))
        setUsername(data.player_username)
        setStatus('Successfully logged into Lichess.')

        // Redirect home after short delay so user sees the success message
        setTimeout(() => navigate('/'), 1500)

      } catch (err) {
        console.error(err)
        if (err instanceof TypeError) {
          setStatus(`Cannot reach the API gateway at ${API_URL} — is it running?`)
        } else {
          setStatus(err.message)
        }
      }
    }

    completeLogin()
  }, [])

  return (
    <main className="login-page">
      <div className="login-card">
        <p className="login-eyebrow">ChessTrack™</p>

        <h1>Lichess Login</h1>

        <p className="login-text">{status}</p>

        {username && (
          <p className="login-text">
            Logged in as: <strong>{username}</strong>
          </p>
        )}
        <Link to="/">
          <button className="login-button">
            Go back home
          </button>
        </Link>
      </div>
    </main>
  )
}

export default Callback