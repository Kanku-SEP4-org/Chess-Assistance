import { useState } from 'react'
import '../App.css'
import Navbar from '../components/Navbar'
import { ML_API_URL } from '../config'

function ChessTrack() {
  const [username, setUsername] = useState('')
  const [playerStats, setPlayerStats] = useState(null)
  const [playerError, setPlayerError] = useState('')
  const [playerLoading, setPlayerLoading] = useState(false)
  const [lichessUsername, setLichessUsername] = useState('');
  const [lichessStats, setLichessStats] = useState(null);
  const [lichessLoading, setLichessLoading] = useState(false);
  const [lichessError, setLichessError] = useState('');
  const [historyUsername, setHistoryUsername] = useState('')
  const [recentGames, setRecentGames] = useState(null)
  const [recentLoading, setRecentLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [performanceResults, setPerformanceResults] = useState({})
  const [predictingGameId, setPredictingGameId] = useState(null)

  const calculateWinRate = (record) => {
    if (!record) return 0

    const wins = record.win || 0
    const losses = record.loss || 0
    const draws = record.draw || 0
    const total = wins + losses + draws

    if (total === 0) return 0

    return Math.round((wins / total) * 100)
  }

  const getModeStats = (mode) => {
    const stats = playerStats?.[mode]

    if (!stats) {
      return {
        rating: 'N/A',
        wins: 0,
        losses: 0,
        draws: 0,
        winRate: 0,
      }
    }

    return {
      rating: stats.last?.rating || 'N/A',
      wins: stats.record?.win || 0,
      losses: stats.record?.loss || 0,
      draws: stats.record?.draw || 0,
      winRate: calculateWinRate(stats.record),
    }
  }

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

  const handleRecentGamesSearch = async (e, explicitUsername = null) => {
    if (e) e.preventDefault()

    const targetUsername = (explicitUsername || historyUsername).trim()
    if (!targetUsername) {
      setHistoryError('Please enter a Lichess username.')
      return
    }

    setHistoryUsername(targetUsername)
    setRecentLoading(true)
    setHistoryError('')
    setRecentGames(null)
    setPerformanceResults({})

    try {
      const response = await fetch(
        `${ML_API_URL}/accuracy/recent-games/${encodeURIComponent(targetUsername)}`
      )
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Failed to load recent games.')
      }

      setRecentGames(data.games || [])
    } catch (error) {
      setHistoryError(error.message || 'Could not load recent games.')
    } finally {
      setRecentLoading(false)
    }
  }

  const handleMyRecentGames = () => {
    const saved = localStorage.getItem('lichess_user')
    if (!saved) {
      setHistoryError('Log in with Lichess first, or enter a username.')
      return
    }

    const user = JSON.parse(saved)
    const savedUsername = user.player_username || user.username || ''
    handleRecentGamesSearch(null, savedUsername)
  }

  const handlePredictPerformance = async (gameId) => {
    const targetUsername = historyUsername.trim()
    if (!targetUsername) {
      setHistoryError('Please enter a Lichess username.')
      return
    }

    setPredictingGameId(gameId)
    setHistoryError('')

    try {
      const response = await fetch(`${ML_API_URL}/predictions/accuracy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          username: targetUsername,
        }),
      })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Prediction failed.')
      }

      setPerformanceResults((prev) => ({
        ...prev,
        [gameId]: data,
      }))
    } catch (error) {
      setHistoryError(error.message || 'Prediction failed.')
    } finally {
      setPredictingGameId(null)
    }
  }

  const verdictLabel = (verdict) => {
    if (verdict === 'overperformed') return 'Overperformed'
    if (verdict === 'underperformed') return 'Underperformed'
    return 'Normal'
  }

  const verdictColor = (verdict) => {
    if (verdict === 'overperformed') return '#4caf50'
    if (verdict === 'underperformed') return '#ff5252'
    return '#ffb300'
  }

     const handleLichessSearch = async (e) => {
        if (e) e.preventDefault()

        if (!lichessUsername.trim()) {
           setLichessError('Please enter a Lichess username.')
           return
        }

        setLichessLoading(true)
        setLichessError('')
        setLichessStats(null)

        try {
           const response = await fetch(
             `https://lichess.org/api/user/${lichessUsername.trim()}`
           )

           if (!response.ok) {
              throw new Error('Player not found')
          }

          const data = await response.json()
          setLichessStats(data)
        } catch (error) {
          setLichessError('Could not find this Lichess player.')
        } finally {
          setLichessLoading(false)
        }
  }


  const rapid = getModeStats('chess_rapid')
  const blitz = getModeStats('chess_blitz')
  const bullet = getModeStats('chess_bullet')

  return (
    <>
    <Navbar />
    <main className="track-page">
      <section className="track-hero">
        <p className="eyebrow">Chess.com Player Lookup</p>
        <h1>Search player performance</h1>
        <p>
          Enter a Chess.com username to view public ratings, records and win ratios.
        </p>

        <form className="player-search" onSubmit={handlePlayerSearch}>
          <input
            type="text"
            placeholder="Example: hikaru"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <button type="submit">
            {playerLoading ? 'Searching...' : 'Search Player'}
          </button>
        </form>

        {playerError && <p className="player-error">{playerError}</p>}
      </section>

      {playerStats && (
        <section className="player-results">
          <h2>{username} Stats</h2>

          <div className="cards-grid">
            <div className="metric-card">
              <span>Rapid Rating</span>
              <strong>{rapid.rating}</strong>
              <p>Win Rate: {rapid.winRate}%</p>
            </div>

            <div className="metric-card">
              <span>Blitz Rating</span>
              <strong>{blitz.rating}</strong>
              <p>Win Rate: {blitz.winRate}%</p>
            </div>

            <div className="metric-card">
              <span>Bullet Rating</span>
              <strong>{bullet.rating}</strong>
              <p>Win Rate: {bullet.winRate}%</p>
            </div>

            <div className="metric-card">
              <span>Total Rapid Games</span>
              <strong>{rapid.wins + rapid.losses + rapid.draws}</strong>
              <p>
                {rapid.wins}W / {rapid.losses}L / {rapid.draws}D
              </p>
            </div>
          </div>

          <div className="session-card">
            <div>
              <p className="eyebrow">Player Summary</p>
              <h2>Performance Overview</h2>
              <p>
                Public Chess.com stats loaded successfully. These values are fetched directly from the Chess.com PubAPI.
              </p>
            </div>

            <div className="session-stats">
              <div>
                <span>Rapid WR</span>
                <strong>{rapid.winRate}%</strong>
              </div>
              <div>
                <span>Blitz WR</span>
                <strong>{blitz.winRate}%</strong>
              </div>
              <div>
                <span>Bullet WR</span>
                <strong>{bullet.winRate}%</strong>
              </div>
              <div>
                <span>Best Rating</span>
                <strong>
                  {Math.max(
                    rapid.rating === 'N/A' ? 0 : rapid.rating,
                    blitz.rating === 'N/A' ? 0 : blitz.rating,
                    bullet.rating === 'N/A' ? 0 : bullet.rating
                  )}
                </strong>
              </div>
            </div>
          </div>
        </section>
      )}
        <section className="track-hero lichess-section">
           <p className="eyebrow">Lichess Player Lookup</p>

           <h1>Search Lichess performance</h1>

           <p>
             Enter a Lichess username to view public ratings and player performance.
           </p>

           <form className="player-search" onSubmit={handleLichessSearch}>
            <input
              type="text"
              placeholder="Example: drnykterstein"
              value={lichessUsername}
              onChange={(e) => setLichessUsername(e.target.value)}
            />

            <button type="submit">
              {lichessLoading ? 'Searching...' : 'Search Player'}
           </button>
          </form>

          {lichessError && (
            <p className="player-error">{lichessError}</p>
          )}
          {lichessStats && (
  <section className="player-results">
    <h2>{lichessStats.username} Stats</h2>

    <div className="cards-grid">
      <div className="metric-card">
  <span>Rapid Rating</span>
  <strong>{lichessStats.perfs?.rapid?.rating || 'N/A'}</strong>
  <p>Games: {lichessStats.perfs?.rapid?.games || 0}</p>
</div>

      <div className="metric-card">
        <span>Blitz Rating</span>
        <strong>{lichessStats.perfs?.blitz?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.blitz?.games || 0}</p>
      </div>

      <div className="metric-card">
        <span>Bullet Rating</span>
        <strong>{lichessStats.perfs?.bullet?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.bullet?.games || 0}</p>
      </div>

      <div className="metric-card">
        <span>Classical Rating</span>
        <strong>{lichessStats.perfs?.classical?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.classical?.games || 0}</p>
      </div>
    </div>

    <div className="session-card">
      <div>
        <p className="eyebrow">Player Summary</p>
        <h2>Lichess Performance Overview</h2>

        <p>
          Public Lichess stats loaded successfully.
        </p>
      </div>

      <div className="session-stats">
        <div>
          <span>Puzzle</span>
          <strong>
            {lichessStats.perfs?.puzzle?.rating || 'N/A'}
          </strong>
        </div>

        <div>
          <span>Storm</span>
          <strong>
            {lichessStats.perfs?.storm?.score || 'N/A'}
          </strong>
        </div>

        <div>
          <span>Patron</span>
          <strong>
            {lichessStats.patron ? 'Yes' : 'No'}
          </strong>
        </div>

        <div>
          <span>Online</span>
          <strong>
            {lichessStats.online ? 'Yes' : 'No'}
          </strong>
        </div>
      </div>
    </div>
  </section>
)}
    </section>

      <section className="track-hero lichess-section">
        <p className="eyebrow">Game History Performance</p>

        <h1>Review recent analyzed games</h1>

        <p>
          Load your 10 most recent Lichess games, then compare actual
          performance with the model prediction for analyzed games.
        </p>

        <form className="player-search" onSubmit={handleRecentGamesSearch}>
          <input
            type="text"
            placeholder="Example: drnykterstein"
            value={historyUsername}
            onChange={(e) => setHistoryUsername(e.target.value)}
          />

          <button type="submit">
            {recentLoading ? 'Loading...' : 'Load Games'}
          </button>

          <button type="button" onClick={handleMyRecentGames} disabled={recentLoading}>
            My Games
          </button>
        </form>

        {historyError && (
          <p className="player-error">{historyError}</p>
        )}

        {recentGames && (
          <div className="game-list" style={{ marginTop: '1.5rem' }}>
            {recentGames.length === 0 ? (
              <p>No recent games found.</p>
            ) : recentGames.map((game) => {
              const result = performanceResults[game.game_id]
              return (
                <div className="game-list-item" key={game.game_id}>
                  <div style={{ flex: 1 }}>
                    <strong>{game.opening || 'Unknown opening'}</strong>
                    <span style={{ marginLeft: '0.75rem', opacity: 0.75 }}>
                      vs {game.opponent}
                    </span>
                    <span
                      style={{
                        marginLeft: '0.75rem',
                        color:
                          game.result === 'win'
                            ? '#4caf50'
                            : game.result === 'loss'
                              ? '#ff5252'
                              : '#ffb300',
                      }}
                    >
                      {game.result}
                    </span>
                    <span style={{ marginLeft: '0.75rem', opacity: 0.55, fontSize: '0.85rem' }}>
                      {game.time_control} {game.speed}
                    </span>

                    {result?.status === 'ok' && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <span style={{ marginRight: '1rem' }}>
                          Actual CPL: <strong>{result.actual_centipawn_loss}</strong>
                        </span>
                        <span style={{ marginRight: '1rem' }}>
                          Predicted CPL: <strong>{result.predicted_centipawn_loss}</strong>
                        </span>
                        <span style={{ color: verdictColor(result.verdict), fontWeight: 700 }}>
                          {verdictLabel(result.verdict)}
                        </span>
                      </div>
                    )}

                    {result?.status === 'analysis_required' && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <p style={{ color: '#ffb300', margin: '0 0 0.5rem' }}>
                          {result.message}
                        </p>
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                          <a
                            href={result.game_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#d8aa55', textDecoration: 'underline', fontSize: '0.85rem' }}
                          >
                            Open game on Lichess
                          </a>
                          <button
                            type="button"
                            onClick={() => handlePredictPerformance(game.game_id)}
                            style={{
                              background: 'transparent',
                              border: '1px solid #ffb300',
                              color: '#ffb300',
                              padding: '0.3rem 1rem',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '0.8rem',
                            }}
                          >
                            Retry
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {!game.has_analysis && (
                      <a
                        href={game.game_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#ffb300', fontSize: '0.8rem', textDecoration: 'underline' }}
                      >
                        Request analysis
                      </a>
                    )}
                    <button
                      type="button"
                      onClick={() => handlePredictPerformance(game.game_id)}
                      disabled={!game.has_analysis || predictingGameId === game.game_id}
                      style={{
                        background: 'rgba(216,170,85,0.2)',
                        border: '1px solid #d8aa55',
                        color: '#d8aa55',
                        padding: '0.3rem 0.8rem',
                        borderRadius: '6px',
                        cursor: game.has_analysis ? 'pointer' : 'not-allowed',
                        fontSize: '0.8rem',
                      }}
                    >
                      {predictingGameId === game.game_id ? 'Predicting...' : 'Predict'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </main>
    </>
  )
}

export default ChessTrack
