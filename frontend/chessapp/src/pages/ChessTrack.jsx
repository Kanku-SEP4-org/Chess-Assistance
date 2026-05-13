import { useState } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/Header'
import heroImg from '../assets/chess-bg.png'

function ChessTrack() {
  const [username, setUsername] = useState('')
  const [playerStats, setPlayerStats] = useState(null)
  const [playerError, setPlayerError] = useState('')
  const [playerLoading, setPlayerLoading] = useState(false)

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

  const rapid = getModeStats('chess_rapid')
  const blitz = getModeStats('chess_blitz')
  const bullet = getModeStats('chess_bullet')

  return (
    <main className="min-vh-100 bg-dark text-white" style={{ backgroundImage: `url(${heroImg})`, backgroundSize: 'auto 115vh', backgroundPosition: 'right top', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
      <Header />

      <section className="py-5" style={{ padding: '80px 64px' }}>
        <div className="container-fluid">
          <div className="row justify-content-center">
            <div className="col-lg-8 col-xl-6 text-center">
              <p className="text-warning text-uppercase fw-bold mb-3" style={{ letterSpacing: '2px', fontSize: '20px' }}>Chess.com Player Lookup</p>
              <h1 className="display-4 fw-bold mb-4">Search player performance</h1>
              <p className="text-white-70 mb-5 fs-5">
                Enter a Chess.com username to view public ratings, records and win ratios.
              </p>

              <form className="d-flex gap-3 justify-content-center mb-4" onSubmit={handlePlayerSearch}>
                <input
                  type="text"
                  className="form-control bg-black bg-opacity-10 border border-white border-opacity-15 text-white rounded-pill px-4 py-3"
                  style={{ minWidth: '300px' }}
                  placeholder="Example: Hikaru"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />

                <button
                  type="submit"
                  className="btn text-dark fw-bold px-4 py-3 rounded-pill border-0"
                  style={{ background: 'linear-gradient(135deg, #d8aa55, #8f6425)' }}
                >
                  {playerLoading ? 'Searching...' : 'Search Player'}
                </button>
              </form>

              {playerError && (
                <div className="alert alert-danger bg-danger bg-opacity-10 border border-danger border-opacity-25 text-danger rounded-3">
                  {playerError}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {playerStats && (
        <section className="py-5" style={{ padding: '0 64px 80px' }}>
          <div className="container-fluid">
            <h2 className="h1 mb-5 text-center">{username} Stats</h2>

            <div className="row g-4 mb-5">
              <div className="col-lg-3 col-md-6">
                <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 h-100 text-center" >
                  <span className="medium mb-3 d-block">Rapid Rating</span>
                  <strong className="h2 mb-3 d-block">{rapid.rating}</strong>
                  <p className="mb-0 lh-base">Win Rate: {rapid.winRate}%</p>
                </div>
              </div>

              <div className="col-lg-3 col-md-6">
                <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 h-100 text-center" >
                  <span className="medium mb-3 d-block">Blitz Rating</span>
                  <strong className="h2 mb-3 d-block">{blitz.rating}</strong>
                  <p className="mb-0 lh-base">Win Rate: {blitz.winRate}%</p>
                </div>
              </div>

              <div className="col-lg-3 col-md-6">
                <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 h-100 text-center" >
                  <span className="medium mb-3 d-block">Bullet Rating</span>
                  <strong className="h2 mb-3 d-block">{bullet.rating}</strong>
                  <p className="mb-0 lh-base">Win Rate: {bullet.winRate}%</p>
                </div>
              </div>

              <div className="col-lg-3 col-md-6">
                <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 h-100 text-center" style={{ boxShadow: '0 20px 80px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255,255,255,0.04)' }}>
                  <span className="medium mb-3 d-block">Total Bullet Games</span>
                  <strong className="h2 mb-3 d-block">{bullet.wins + bullet.losses + bullet.draws}</strong>
                  <p className="text-white-70 mb-0">
                    {rapid.wins}W / {rapid.losses}L / {rapid.draws}D
                  </p>
                </div>
              </div>
            </div>

            <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border-white border-opacity-10 rounded-4 p-4">
              <div className="row g-4 align-items-center">
                <div className="col-lg-6">
                  <p className="text-uppercase fw-bold mb-2 small">Player Summary</p>
                  <h2 className="h1 mb-3">Performance Overview</h2>
                  <p className="text-white-70 lh-base">
                    Public Chess.com stats loaded successfully. These values are fetched directly from the Chess.com PubAPI.
                  </p>
                </div>

                <div className="col-lg-6">
                  <div className="row g-4">
                    <div className="col-3 text-center">
                    <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                      <span className="text-white">Rapid WR</span>
                      <strong className="h3 text-white">{rapid.winRate}%</strong>
                    </div>
                  </div>
                    <div className="col-3 text-center">
                      <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                        <span className="text-white">Blitz WR</span>
                        <strong className="h4 text-white">{blitz.winRate}%</strong>
                      </div>
                    </div>
                    <div className="col-3 text-center">
                      <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                        <span className="text-white">Bullet WR</span>
                        <strong className="h4 text-white">{bullet.winRate}%</strong>
                      </div>
                    </div>
                    <div className="col-3 text-center">
                      <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                        <span className="text-white">Best Rating</span>
                        <strong className="h4 text-white">
                          {Math.max(
                            rapid.rating === 'N/A' ? 0 : rapid.rating,
                            blitz.rating === 'N/A' ? 0 : blitz.rating,
                            bullet.rating === 'N/A' ? 0 : bullet.rating
                          )}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}

export default ChessTrack