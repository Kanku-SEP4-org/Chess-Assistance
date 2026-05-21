import { useState } from 'react'
import '../App.css'
import Navbar from '../components/Navbar'

function ChessTrack() {
  const [username, setUsername] = useState('')
  const [playerStats, setPlayerStats] = useState(null)
  const [playerError, setPlayerError] = useState('')
  const [playerLoading, setPlayerLoading] = useState(false)
  const [lichessUsername, setLichessUsername] = useState('');
  const [lichessStats, setLichessStats] = useState(null);
  const [lichessLoading, setLichessLoading] = useState(false);
  const [lichessError, setLichessError] = useState('');

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
    <main className="track-page container py-4">
      <section className="track-hero text-center py-5">
        <p className="eyebrow">Chess.com Player Lookup</p>
        <h1>Search player performance</h1>
        <p>
          Enter a Chess.com username to view public ratings, records and win ratios.
        </p>

        <form className="player-search row justify-content-center align-items-center g-3 mt-4" onSubmit={handlePlayerSearch}>
           <div className="col-12 col-md-7 col-lg-5">
          <input
            className="form-control"
            type="text"
            placeholder="Example: hikaru"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          </div>

           
            <button className="search-btn" type="submit">
            {playerLoading ? 'Searching...' : 'Search Player'}
          </button>
      
        </form>

        {playerError && <p className="player-error">{playerError}</p>}
      </section>

      {playerStats && (
        <section className="player-results">
          <h2>{username} Stats</h2>

          <div className="row g-4 mt-3">
           <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
              <span>Rapid Rating</span>
              <strong>{rapid.rating}</strong>
              <p>Win Rate: {rapid.winRate}%</p>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
              <span>Blitz Rating</span>
              <strong>{blitz.rating}</strong>
              <p>Win Rate: {blitz.winRate}%</p>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
              <span>Bullet Rating</span>
              <strong>{bullet.rating}</strong>
              <p>Win Rate: {bullet.winRate}%</p>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg-3">
             <div className="metric-card h-100 text-center p-4">
              <span>Total Rapid Games</span>
              <strong>{rapid.wins + rapid.losses + rapid.draws}</strong>
              <p>
                {rapid.wins}W / {rapid.losses}L / {rapid.draws}D
              </p>
            </div>
            </div>

          </div>

          <div className="session-card row align-items-center g-4 mt-4">
            <div>
              <p className="eyebrow">Player Summary</p>
              <h2>Performance Overview</h2>
              <p>
                Public Chess.com stats loaded successfully. These values are fetched directly from the Chess.com PubAPI.
              </p>
            </div>

            <div className="session-stats row text-center">
              <div className="col-6 col-md-3 mb-3">
                <span>Rapid WR</span>
                <strong>{rapid.winRate}%</strong>
              </div>
              <div className="col-6 col-md-3 mb-3">
                <span>Blitz WR</span>
                <strong>{blitz.winRate}%</strong>
              </div>
              <div className="col-6 col-md-3 mb-3">
                <span>Bullet WR</span>
                <strong>{bullet.winRate}%</strong>
              </div>
              <div className="col-6 col-md-3 mb-3">
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
        <section className="track-hero lichess-section py-5 text-center">
           <p className="eyebrow">Lichess Player Lookup</p>

           <h1>Search Lichess performance</h1>

           <p>
             Enter a Lichess username to view public ratings and player performance.
           </p>

           <form className="player-search row justify-content-center align-items-center g-3 mt-4" onSubmit={handleLichessSearch}>
            <div className="col-12 col-md-7 col-lg-5">
            <input
              className="form-control"
              type="text"
              placeholder="Example: drnykterstein"
              value={lichessUsername}
              onChange={(e) => setLichessUsername(e.target.value)}
            />
            </div>

            
            <button className="search-btn" type="submit">
              {lichessLoading ? 'Searching...' : 'Search Player'}
           </button>
           
          </form>

          {lichessError && (
            <p className="player-error">{lichessError}</p>
          )}
          {lichessStats && (
  <section className="player-results">
    <h2>{lichessStats.username} Stats</h2>

    <div className="row g-4 mt-3">
      <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
       <span>Rapid Rating</span>
       <strong>{lichessStats.perfs?.rapid?.rating || 'N/A'}</strong>
       <p>Games: {lichessStats.perfs?.rapid?.games || 0}</p>
     </div>
     </div>

      <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
        <span>Blitz Rating</span>
        <strong>{lichessStats.perfs?.blitz?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.blitz?.games || 0}</p>
      </div>
      </div>

      <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
        <span>Bullet Rating</span>
        <strong>{lichessStats.perfs?.bullet?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.bullet?.games || 0}</p>
      </div>
      </div>

      <div className="col-12 col-sm-6 col-lg-3">
            <div className="metric-card h-100 text-center p-4">
        <span>Classical Rating</span>
        <strong>{lichessStats.perfs?.classical?.rating || 'N/A'}</strong>
        <p>Games: {lichessStats.perfs?.classical?.games || 0}</p>
      </div>
      </div>
    </div>

    <div className="session-card row align-items-center g-4 mt-4">
      <div>
        <p className="eyebrow">Player Summary</p>
        <h2>Lichess Performance Overview</h2>

        <p>
          Public Lichess stats loaded successfully.
        </p>
      </div>

      <div className="session-stats row text-center">
        <div className="col-6 col-md-3 mb-3">
          <span>Puzzle</span>
          <strong>
            {lichessStats.perfs?.puzzle?.rating || 'N/A'}
          </strong>
        </div>

        <div className="col-6 col-md-3 mb-3">
          <span>Storm</span>
          <strong>
            {lichessStats.perfs?.storm?.score || 'N/A'}
          </strong>
        </div>

        <div className="col-6 col-md-3 mb-3">
          <span>Patron</span>
          <strong>
            {lichessStats.patron ? 'Yes' : 'No'}
          </strong>
        </div>

        <div className="col-6 col-md-3 mb-3">
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
    </main>
    </>
  )
}

export default ChessTrack