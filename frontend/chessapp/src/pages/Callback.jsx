import React, { useEffect, useState } from 'react'
import './Login.css'

function Callback() {
  const [status, setStatus] = useState('Reading Lichess callback...')
  const [codeFound, setCodeFound] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const error = params.get('error')

    if (error) {
      setStatus(`Lichess login failed: ${error}`)
      return
    }

    if (!code) {
      setStatus('No authorization code was found in the callback URL.')
      return
    }

    setCodeFound(true)
    setStatus('Authorization code received from Lichess.')
  }, [])

  return (
    <main className="login-page">
      <div className="login-card">
        <p className="login-eyebrow">ChessTrack™</p>

        <h1>Lichess Callback</h1>

        <p className="login-text">{status}</p>

        {codeFound && (
          <p className="login-text">
            Next step: exchange this code through the API Gateway.
          </p>
        )}
      </div>
    </main>
  )
}

export default Callback