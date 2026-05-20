import { useEffect, useState } from 'react'
import heroImg from '../assets/chess-bg.png'
import Navbar from '../components/Navbar'

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

  const rawJson = iotData
    ? JSON.stringify(iotData, null, 2)
    : ''

  return (
    <>
     <Navbar />

     <main

      className="min-vh-100 text-white"
      style={{
        backgroundImage: `url(${heroImg})`,
        backgroundSize: 'auto 115vh',
        backgroundPosition: 'right top',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >

      <section
        className="py-5"
        style={{ padding: '80px 64px' }}
      >

        <div>

          <div>

            <div>

              <p
                className="text-warning text-uppercase fw-bold mb-3"
                style={{
                  letterSpacing: '2px',
                  fontSize: '20px'
                }}
              >
                IoT System Monitor
              </p>

              <h1 className="display-4 fw-bold mb-4">
                Live IoT sensor data from your environment
              </h1>

              <p className="text-white-70 mb-5 fs-5">
                This dashboard pulls the latest data from the API gateway
                and the IoT service. It refreshes automatically every 10 seconds.
              </p>

              <div className="d-flex gap-3 justify-content-center mb-4">

                <button
                  className="btn text-dark fw-bold px-4 py-3 rounded-pill border-0 text-black"
                  style={{
                    background: 'linear-gradient(135deg, #d8aa55, #8f6425)'
                  }}
                  onClick={fetchIotData}
                >
                  Refresh Data
                </button>

              </div>

              {error && (

                <div className="alert alert-danger bg-danger bg-opacity-10 border border-danger border-opacity-25 text-danger rounded-3">

                  {error}

                </div>

              )}

            </div>

          </div>

        </div>

      </section>

      <section
        className="py-5"
        style={{ padding: '0 64px 80px' }}
      >

        <div className="container-fluid">

          <h2 className="h1 mb-5 text-center">
            Sensor Summary
          </h2>

          <div className="row g-4 mb-5">

            <div className="col-lg-3 col-md-6">

              <div className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 h-100 text-center">

                <span className="medium mb-3 d-block">
                  Temperature
                </span>

                <strong className="h2 mb-3 d-block">

                  {loading
                    ? 'Loading…'
                    : iotData?.value != null
                    ? `${iotData.value.toFixed(1)}°C`
                    : 'N/A'}

                </strong>

                <p className="text-white-70 mb-0 lh-base">
                  Current reading for the connected temperature sensor.
                </p>

              </div>

            </div>

            <div className="col-lg-3 col-md-6">

              <div className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 h-100 text-center">

                <span className="medium mb-3 d-block">
                  Sensor Type
                </span>

                <strong className="h2 mb-3 d-block">

                  {iotData
                    ? sensorTypeLabel(iotData.type)
                    : 'N/A'}

                </strong>

                <p className="text-white-70 mb-0 lh-base">
                  Detected IoT sensor type from the backend.
                </p>

              </div>

            </div>

            <div className="col-lg-3 col-md-6">

              <div className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 h-100 text-center">

                <span className="medium mb-3 d-block">
                  Last Update
                </span>

                <strong className="h2 mb-3 d-block">

                  {loading ? '...' : lastSeen}

                </strong>

                <p className="text-white-70 mb-0 lh-base">
                  Timestamp when the sensor data was last received.
                </p>

              </div>

            </div>

            <div className="col-lg-3 col-md-6">

              <div
                className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 h-100 text-center"
                style={{
                  boxShadow:
                    '0 20px 80px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255,255,255,0.04)'
                }}
              >

                <span className="medium mb-3 d-block">
                  Environment Status
                </span>

                <strong className="h2 mb-3 d-block">

                  {loading
                    ? '...'
                    : comfortStatus(iotData?.value)}

                </strong>

                <p className="text-white-70 mb-0 lh-base">
                  Basic comfort state based on temperature readings.
                </p>

              </div>

            </div>

          </div>

          <div
            className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 mb-5"
            style={{
              boxShadow:
                '0 20px 80px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255,255,255,0.04)'
            }}
          >

            <div className="row g-4 align-items-center">

              <div className="col-lg-6">

                <p className="text-warning text-uppercase fw-bold mb-2 small">
                  IoT Service
                </p>

                <h2 className="h1 mb-3">
                  Connected Device Health
                </h2>

                <p className="text-white-70 lh-base">
                  The dashboard is connected to the API gateway at
                  <strong> {BASE_URL}</strong> and displays the most recent sensor values.
                </p>

              </div>

              <div className="col-lg-6">

                <div className="row g-4">

                  <div className="card bg-transparent border border-white border-opacity-10 rounded-4 p-4">

                    <span className="text-white-50 small d-block">
                      Success
                    </span>

                    <strong className="h4 text-white">
                      {iotData?.success ? 'Yes' : 'No'}
                    </strong>

                  </div>

                  <div className="card bg-transparent border border-white border-opacity-10 rounded-4 p-4">

                    <span className="text-white-50 small d-block">
                      Message
                    </span>

                    <strong className="h4 text-white">
                      {iotData?.message || 'No message'}
                    </strong>

                  </div>

                </div>

              </div>

            </div>

          </div>

          <div className="card text-white bg-black bg-opacity-50 border border-white border-opacity-10 rounded-4 p-4 mb-5">

            <div className="row g-4">

              <div className="col-12">

                <p className="text-warning text-uppercase fw-bold mb-2 small">
                  Full Backend Payload
                </p>

                <h2 className="h1 mb-3">
                  IoT Response JSON
                </h2>

                <p className="text-white-70 lh-base mb-4">
                  This shows the full response the backend sends to the frontend.
                </p>

              </div>

              <div className="col-12">

                <div className="bg-dark bg-opacity-35 border border-white border-opacity-10 rounded-3 p-4">

                  <pre
                    className="text-white-70 mb-0 small"
                    style={{ fontFamily: 'monospace' }}
                  >

                    {loading
                      ? 'Loading payload…'
                      : rawJson || 'No payload available'}

                  </pre>

                </div>

              </div>

            </div>

          </div>

        </div>

      </section>

    </main>
    </>
  )
}

export default IotDashboard