import { useState } from "react";
import { Crown, User, History, Settings, TrendingUp, TextAlignStart } from "lucide-react";
import { Link } from 'react-router-dom'
import heroImg from '../assets/chess-bg.png'
import Header from '../components/Header';


function Home() {
  const [monitoringStarted, setMonitoringStarted] = useState(false)
  const [username, setUsername] = useState('')
  const [playerStats, setPlayerStats] = useState(null)
  const [playerError, setPlayerError] = useState('')
  const [playerLoading, setPlayerLoading] = useState(false)
  const [showSleepForm, setShowSleepForm] = useState(false)
  const [sleepTime, setSleepTime] = useState("")
  const [wakeTime, setWakeTime] = useState("")
  const [sleepResult, setSleepResult] = useState("")

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

  return (
    <main className="min-vh-100 bg-dark text-white" style={{ backgroundImage: `url(${heroImg})`, backgroundSize: 'auto 115vh', backgroundPosition: 'right top', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
      <Header />

      <section id="home" className="min-vh-100 d-flex align-items-center position-relative" style={{ padding: '120px 64px 80px' }}>
        <div className="container-fluid">
          <div className="row">
            <div className="col-lg-8 col-xl-6" style={{ marginLeft: '120px' }}>
              <p className="text-warning text-uppercase fw-bold mb-3" style={{ letterSpacing: '2px', fontSize: '20px' }}>Chess Performance Assistant</p>
              <h1 className="display-1 fw-bold lh-1 mb-5" style={{ fontSize: 'clamp(48px, 7vw, 92px)' }}>Track your environment. Improve your game.</h1>
              <button
                type="button"
                className="btn text-dark fw-bold px-4 py-3 rounded-pill border-0 text-black"
                style={{ background: 'linear-gradient(135deg, #d8aa55, #8f6425)', boxShadow: '0 20px 60px rgba(216, 170, 85, 0.22)' }}
                onClick={() => setMonitoringStarted(true)}
              >
                Start Monitoring
              </button>
            </div>
          </div>
        </div>
      </section>

      {monitoringStarted && (
        <section id="track" className="py-5" style={{ padding: '80px 64px' }}>
            {monitoringStarted && (
           <button
             className="btn text-dark fw-bold px-4 py-3 rounded-pill border-0 mb-5 d-block text-black"
             style={{ background: 'linear-gradient(135deg, #d8aa55, #8f6425)', transition: 'all 0.25s ease' }}
             onClick={() => setShowSleepForm(!showSleepForm)}
           >
            How much time did I sleep?
           </button>
)}
          <h2 className="h1 mb-4">Live Metrics</h2>

          <div className="row g-4 mb-4">
            <div className="col-lg-3 col-md-6">
              <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 h-100" >
                <span className="medium mb-3 d-block">Temperature</span>
                <strong className="h2 mb-3 d-block">22°C</strong>
                <p className="mb-0 lh-base">Optimal playing condition</p>
              </div>
            </div>

            <div className="col-lg-3 col-md-6">
              <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border-white border-opacity-10 rounded-4 p-4 h-100" >
                <span className="medium mb-3 d-block">CO2 Level</span>
                <strong className="h2 mb-3 d-block">820 ppm</strong>
                <p className="mb-0 lh-base">Room air quality is stable</p>
              </div>
            </div>
            <div className="col-lg-3 col-md-6">
              <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border-white border-opacity-10 rounded-4 p-4 h-100" >
                <span className="medium mb-3 d-block">Light Level</span>
                <strong className="h2 mb-3 d-block">74%</strong>
                <p className="mb-0 lh-base">Good visibility for focus</p>
              </div>
            </div>
            <div className="col-lg-3 col-md-6">
              <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border-white border-opacity-10 rounded-4 p-4 h-100" >
                <span className="medium mb-3 d-block">Focus Score</span>
                <strong className="h2 mb-3 d-block">86%</strong>
                <p className="mb-0 lh-base">Ready for a strong session</p>
              </div>
            </div>
          </div>

          <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border-white border-opacity-10 rounded-4 p-4">
            <div className="row g-4 align-items-center">
              <div className="col-lg-6">
                <p className="text-uppercase fw-bold mb-2 small">Current Session</p>
                <h2 className="h1 mb-3">Session Performance</h2>
                <p className="text-white-70 lh-base">Tracking your chess performance during this play session.</p>
              </div>
            
              <div className="col-lg-6">
                <div className="row g-4">
                  <div className="col-3 text-center">
                    <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                      <span className="text-white">Games</span>
                      <strong className="h3 text-white">5</strong>
                    </div>
                  </div>
                  <div className="col-3 text-center">
                    <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                      <span className="text-white">Wins</span>
                      <strong className="h3 text-white">3</strong>
                    </div>
                  </div>
                  <div className="col-3 text-center">
                    <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                      <span className="text-white">Losses</span>
                      <strong className="h3 text-white">2</strong>
                    </div>
                  </div>
                  <div className="col-3 text-center">
                    <div className="card p-3 rounded-3 bg-transparent border border-white border-opacity-10 rounded-4 p-4">
                      <span className="text-white">Win Rate</span>
                      <strong className="h3 text-white">60%</strong>
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

export default Home