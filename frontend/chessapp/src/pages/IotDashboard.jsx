import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

const BASE_URL = 'http://localhost:3001'

function IotDashboard() {
  const [iotData, setIotData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchIotData = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${BASE_URL}/iot/temp?id=1`)
      const data = await response.json()

      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to load IoT data')
      }

      setIotData(data)
    } catch (err) {
      setError(err.message || 'Unable to fetch IoT data')
      setIotData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIotData()
    const interval = setInterval(fetchIotData, 10000)
    return () => clearInterval(interval)
  }, [])

  const sensorTypeLabel = (type) => {
    if (type === 0) return 'Temperature'
    return 'Unknown Sensor'
  }

  const comfortStatus = (value) => {
    if (value == null) return 'Unknown'
    if (value < 18) return 'Cool'
    if (value <= 26) return 'Comfortable'
    return 'Warm'
  }

  const lastSeen = iotData?.timestamp
    ? new Date(Number(iotData.timestamp)).toLocaleString()
    : 'N/A'

  const rawJson = iotData ? JSON.stringify(iotData, null, 2) : ''

  return (
    <main className="track-page">
      <nav className="navbar">
        <div className="logo">IoT Dashboard</div>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/chesstrack">ChessTrack</Link>
          <Link to="/iot">IoT Dashboard</Link>
        </div>
      </nav>

      <section className="track-hero">
        <p className="eyebrow">IoT System Monitor</p>
        <h1>Live IoT sensor data from your environment</h1>
        <p>
          This dashboard pulls the latest data from the API gateway and the IoT service. It refreshes automatically every 10 seconds.
        </p>

        <div className="player-search" style={{ marginTop: '24px', gap: '12px' }}>
          <button className="sleep-toggle-btn" type="button" onClick={fetchIotData}>
            Refresh Data
          </button>
          <Link to="/" className="sleep-toggle-btn" style={{ textDecoration: 'none' }}>
            Back to Home
          </Link>
        </div>

        {error && <p className="player-error">{error}</p>}
      </section>

      <section className="dashboard">
        <h2>Sensor Summary</h2>
        <div className="cards-grid">
          <div className="metric-card">
            <span>Temperature</span>
            <strong>{loading ? 'Loading…' : iotData?.value != null ? `${iotData.value.toFixed(1)}°C` : 'N/A'}</strong>
            <p>Current reading for the connected temperature sensor.</p>
          </div>

          <div className="metric-card">
            <span>Sensor Type</span>
            <strong>{iotData ? sensorTypeLabel(iotData.type) : 'N/A'}</strong>
            <p>Detected IoT sensor type from the backend.</p>
          </div>

          <div className="metric-card">
            <span>Last Update</span>
            <strong>{loading ? '...' : lastSeen}</strong>
            <p>Timestamp when the sensor data was last received.</p>
          </div>

          <div className="metric-card">
            <span>Environment Status</span>
            <strong>{loading ? '...' : comfortStatus(iotData?.value)}</strong>
            <p>Basic comfort state based on temperature readings.</p>
          </div>
        </div>

        <div className="session-card">
          <div>
            <p className="eyebrow">IoT Service</p>
            <h2>Connected Device Health</h2>
            <p>
              The dashboard is connected to the API gateway at <strong>{BASE_URL}</strong> and displays the most recent sensor values from your IoT service.
            </p>
          </div>

          <div className="session-stats">
            <div>
              <span>Success</span>
              <strong>{iotData?.success ? 'Yes' : 'No'}</strong>
            </div>
            <div>
              <span>Message</span>
              <strong>{iotData?.message || 'No message'}</strong>
            </div>
            <div>
              <span>Value Type</span>
              <strong>{iotData?.type != null ? iotData.type : 'N/A'}</strong>
            </div>
            <div>
              <span>Data Age</span>
              <strong>{iotData?.timestamp ? `${Math.max(0, Math.round((Date.now() - Number(iotData.timestamp)) / 1000))}s` : 'N/A'}</strong>
            </div>
          </div>
        </div>

        <div className="session-card">
          <div>
            <p className="eyebrow">Full Backend Payload</p>
            <h2>IoT Response JSON</h2>
            <p>This shows the full response the backend sends to the frontend so the backend team can verify every field.</p>
          </div>

          <div className="json-card">
            <pre>{loading ? 'Loading payload…' : rawJson || 'No payload available'}</pre>
          </div>
        </div>
      </section>
    </main>
  )
}

export default IotDashboard
