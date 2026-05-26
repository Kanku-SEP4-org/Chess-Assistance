import { useState, useEffect } from 'react'
import '../App.css'
import Navbar from '../components/Navbar'
import { ML_API_URL } from '../config'

const ANGRINESS_LABELS = {
  1: 'Very Calm',
  2: 'Calm',
  3: 'Moderate',
  4: 'Tilted',
  5: 'Very Tilted',
}

const ANGRINESS_COLORS = {
  1: '#4caf50',
  2: '#8bc34a',
  3: '#ffb300',
  4: '#ff7043',
  5: '#ff5252',
}

function AngrinessPredictor() {
  const [gameId, setGameId] = useState('')
  const [playerUsername, setPlayerUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [prediction, setPrediction] = useState(null)
  const [analysisRequired, setAnalysisRequired] = useState(null)
  const [lichessUser, setLichessUser] = useState(null)
  const [recentGames, setRecentGames] = useState(null)
  const [recentLoading, setRecentLoading] = useState(false)
  const [recentUsername, setRecentUsername] = useState('')

  useEffect(() => {
    const saved = localStorage.getItem('lichess_user')
    if (saved) {
      const user = JSON.parse(saved)
      setLichessUser(user)
      setPlayerUsername(user.player_username || '')
      setRecentUsername(user.player_username || '')
    }
  }, [])

  const handlePredict = async (e) => {
    if (e) e.preventDefault()
    if (!gameId.trim() || !playerUsername.trim()) {
      setError('Please enter both a game ID and player username.')
      return
    }

    setLoading(true)
    setError('')
    setPrediction(null)
    setAnalysisRequired(null)

    try {
      const res = await fetch(`${ML_API_URL}/predictions/angriness/lichess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId.trim(),
          player_username: playerUsername.trim(),
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || data.error || 'Prediction failed.')
        return
      }

      if (data.status === 'analysis_required') {
        setAnalysisRequired({ ...data, _username: playerUsername.trim() })
        return
      }

      setPrediction(data)
    } catch {
      setError('Could not connect to the server.')
    } finally {
      setLoading(false)
    }
  }

  const handlePredictGame = (gId, lossStreak = 0) => {
    setGameId(gId)
    setAnalysisRequired(null)
    setPrediction(null)
    setError('')
    setTimeout(() => {
      handlePredictDirect(gId, recentUsername, lossStreak)
    }, 0)
  }

  const handlePredictDirect = async (gId, username, lossStreak = 0) => {
    setLoading(true)
    setError('')
    setPrediction(null)
    setAnalysisRequired(null)

    try {
      const res = await fetch(`${ML_API_URL}/predictions/angriness/lichess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gId.trim(),
          player_username: username.trim(),
          consecutive_losses_pregame: lossStreak,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || data.error || 'Prediction failed.')
        return
      }

      if (data.status === 'analysis_required') {
        setAnalysisRequired({ ...data, _username: username.trim() })
        return
      }

      setPrediction(data)
    } catch {
      setError('Could not connect to the server.')
    } finally {
      setLoading(false)
    }
  }

  const fetchRecentGames = async (username) => {
    setRecentLoading(true)
    setError('')
    setRecentGames(null)

    try {
      const res = await fetch(
        `${ML_API_URL}/angriness/recent-games/${encodeURIComponent(username)}`
      )

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || data.error || 'Failed to load recent games.')
        return
      }

      setRecentGames(data.games)
    } catch {
      setError('Could not connect to the server.')
    } finally {
      setRecentLoading(false)
    }
  }

  const loadRecentGamesSearch = () => {
    const username = recentUsername.trim()
    if (!username) {
      setError('Please enter a username to search.')
      return
    }
    fetchRecentGames(username)
  }

  const loadMyRecentGames = () => {
    if (lichessUser?.player_username) {
      setRecentUsername(lichessUser.player_username)
      fetchRecentGames(lichessUser.player_username)
    }
  }

  return (
    <>
      <Navbar />
      <main className="track-page">
        <section className="track-hero">
          <p className="eyebrow">Angriness Scale Predictor</p>
          <h1>Predict your tilt level</h1>
          <p>
            Enter a Lichess game ID and player username to predict the angriness
            scale (1-5) based on game analysis.
          </p>

          <form className="player-search" onSubmit={handlePredict}>
            <input
              type="text"
              placeholder="Game ID (e.g. 98aCDexV)"
              value={gameId}
              onChange={(e) => setGameId(e.target.value)}
            />
            <input
              type="text"
              placeholder="Player username"
              value={playerUsername}
              onChange={(e) => setPlayerUsername(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Predicting...' : 'Predict'}
            </button>
          </form>

          {error && <p className="player-error">{error}</p>}
        </section>

        <section style={{ padding: '0 2rem 2rem' }}>
          <p className="eyebrow">Or pick from recent games</p>
          <div className="player-search" style={{ marginBottom: '0.75rem' }}>
            <input
              type="text"
              placeholder="Search by username"
              value={recentUsername}
              onChange={(e) => setRecentUsername(e.target.value)}
            />
            <button
              type="button"
              onClick={loadRecentGamesSearch}
              disabled={recentLoading}
            >
              {recentLoading ? 'Loading...' : 'Search'}
            </button>
            {lichessUser && (
              <button
                type="button"
                onClick={loadMyRecentGames}
                disabled={recentLoading}
                style={{
                  background: 'rgba(216,170,85,0.15)',
                  border: '1px solid #d8aa55',
                  color: '#d8aa55',
                }}
              >
                {recentLoading ? 'Loading...' : 'My Games'}
              </button>
            )}
          </div>

          {recentGames && (
            <div className="game-list" style={{ marginTop: '1rem' }}>
              {recentGames.map((g) => (
                <div key={g.game_id} className="game-list-item">
                  <div style={{ flex: 1 }}>
                    <strong>{g.opening || 'Unknown opening'}</strong>
                    <span style={{ marginLeft: '0.75rem', opacity: 0.7 }}>
                      vs {g.opponent}
                    </span>
                    <span
                      style={{
                        marginLeft: '0.75rem',
                        color:
                          g.result === 'win'
                            ? '#4caf50'
                            : g.result === 'loss'
                              ? '#ff5252'
                              : '#ffb300',
                      }}
                    >
                      {g.result}
                    </span>
                    <span style={{ marginLeft: '0.75rem', opacity: 0.5, fontSize: '0.85rem' }}>
                      {g.time_control} {g.speed}
                    </span>
                    {g.consecutive_losses_before > 0 && (
                      <span style={{
                        marginLeft: '0.75rem',
                        color: '#ff7043',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                      }}>
                        {g.consecutive_losses_before} loss{g.consecutive_losses_before > 1 ? 'es' : ''} before
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {!g.has_analysis && (
                      <span style={{ color: '#ffb300', fontSize: '0.8rem' }}>
                        No analysis
                      </span>
                    )}
                    <button
                      onClick={() => handlePredictGame(g.game_id, g.consecutive_losses_before || 0)}
                      style={{
                        background: 'rgba(216,170,85,0.2)',
                        border: '1px solid #d8aa55',
                        color: '#d8aa55',
                        padding: '0.3rem 0.8rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                      }}
                    >
                      Predict
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {analysisRequired && (
          <section style={{ padding: '0 2rem 2rem' }}>
            <div className="analysis-warning">
              <p style={{ margin: '0 0 0.75rem', fontWeight: 600 }}>
                Game analysis required
              </p>
              <p style={{ margin: '0 0 1rem', opacity: 0.85 }}>
                {analysisRequired.message}
              </p>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <a
                  href={analysisRequired.game_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#d8aa55',
                    textDecoration: 'underline',
                  }}
                >
                  Open game on Lichess
                </a>
                <button
                  onClick={() => handlePredictDirect(analysisRequired.game_id, analysisRequired._username)}
                  style={{
                    background: 'transparent',
                    border: '1px solid #ffb300',
                    color: '#ffb300',
                    padding: '0.3rem 1rem',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  Retry
                </button>
              </div>
            </div>
          </section>
        )}

        {prediction && (
          <section className="player-results" style={{ padding: '0 2rem 2rem' }}>
            <div className="angriness-scale">
              {[1, 2, 3, 4, 5].map((level) => (
                <div
                  key={level}
                  className={`angriness-segment ${prediction.angriness === level ? 'angriness-level-active' : ''}`}
                  style={{
                    backgroundColor:
                      prediction.angriness === level
                        ? ANGRINESS_COLORS[level]
                        : 'rgba(255,255,255,0.08)',
                  }}
                >
                  <span className="angriness-segment-number">{level}</span>
                  <span className="angriness-segment-label">
                    {ANGRINESS_LABELS[level]}
                  </span>
                </div>
              ))}
            </div>

            <div className="cards-grid" style={{ marginTop: '1.5rem' }}>
              <div className="metric-card">
                <span className="eyebrow">Angriness Level</span>
                <strong
                  style={{
                    fontSize: '2rem',
                    color: ANGRINESS_COLORS[prediction.angriness],
                  }}
                >
                  {prediction.angriness}/5
                </strong>
                <p>{ANGRINESS_LABELS[prediction.angriness]}</p>
              </div>
              <div className="metric-card">
                <span className="eyebrow">Player Rating</span>
                <strong style={{ fontSize: '1.5rem' }}>
                  {prediction.player_rating}
                </strong>
                <p>vs {prediction.opponent_rating}</p>
              </div>
              <div className="metric-card">
                <span className="eyebrow">Opening</span>
                <strong style={{ fontSize: '1rem' }}>
                  {prediction.opening || 'Unknown'}
                </strong>
              </div>
              <div className="metric-card">
                <span className="eyebrow">Time Control</span>
                <strong style={{ fontSize: '1.5rem' }}>
                  {prediction.time_control}
                </strong>
                <p>{prediction.player_side} pieces</p>
              </div>
            </div>

            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              <a
                href={prediction.game_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#d8aa55', fontSize: '0.9rem' }}
              >
                View game on Lichess
              </a>
            </div>
          </section>
        )}
      </main>
    </>
  )
}

export default AngrinessPredictor
