import { useState } from 'react';
import { Link } from 'react-router-dom';
import '../App.css';

function PlayerPreferences() {
  const [preferences, setPreferences] = useState({
    daily_game_limit: '',
    daily_playtime_limit_min: '',
    break_interval_min: '',
    recommend_rest_min: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Assuming there's an API endpoint to save preferences
      const response = await fetch('/api/player-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          daily_game_limit: parseInt(preferences.daily_game_limit),
          daily_playtime_limit_min: parseInt(preferences.daily_playtime_limit_min),
          break_interval_min: parseInt(preferences.break_interval_min),
          recommend_rest_min: parseInt(preferences.recommend_rest_min)
        })
      });

      if (response.ok) {
        setMessage('Preferences saved successfully!');
        setPreferences({
          daily_game_limit: '',
          daily_playtime_limit_min: '',
          break_interval_min: '',
          recommend_rest_min: ''
        });
      } else {
        setMessage('Failed to save preferences. Please try again.');
      }
    } catch (error) {
      setMessage('Error saving preferences. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app" style={{ backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <nav className="navbar">
        <div className="logo">ChessTrack™</div>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/chesstrack">ChessTrack</Link>
          <Link to="/iot">IoT Dashboard</Link>
        </div>
      </nav>

      <div className="container" style={{ maxWidth: '600px', margin: '2rem auto', padding: '2rem', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '2rem', color: '#333' }}>Player Preferences</h1>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="daily_game_limit" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', color: '#555' }}>
              Daily Game Limit:
            </label>
            <input
              type="number"
              id="daily_game_limit"
              name="daily_game_limit"
              value={preferences.daily_game_limit}
              onChange={handleChange}
              min="1"
              required
              style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '1rem' }}
              placeholder="Enter maximum games per day"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="daily_playtime_limit_min" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', color: '#555' }}>
              Daily Playtime Limit (minutes):
            </label>
            <input
              type="number"
              id="daily_playtime_limit_min"
              name="daily_playtime_limit_min"
              value={preferences.daily_playtime_limit_min}
              onChange={handleChange}
              min="1"
              required
              style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '1rem' }}
              placeholder="Enter maximum playtime in minutes"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="break_interval_min" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', color: '#555' }}>
              Break Interval (minutes):
            </label>
            <input
              type="number"
              id="break_interval_min"
              name="break_interval_min"
              value={preferences.break_interval_min}
              onChange={handleChange}
              min="1"
              required
              style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '1rem' }}
              placeholder="Enter break interval in minutes"
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label htmlFor="recommend_rest_min" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', color: '#555' }}>
              Recommended Rest (minutes):
            </label>
            <input
              type="number"
              id="recommend_rest_min"
              name="recommend_rest_min"
              value={preferences.recommend_rest_min}
              onChange={handleChange}
              min="1"
              required
              style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '1rem' }}
              placeholder="Enter recommended rest time in minutes"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Saving...' : 'Save Preferences'}
          </button>
        </form>

        {message && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            borderRadius: '4px',
            backgroundColor: message.includes('successfully') ? '#d4edda' : '#f8d7da',
            color: message.includes('successfully') ? '#155724' : '#721c24',
            border: `1px solid ${message.includes('successfully') ? '#c3e6cb' : '#f5c6cb'}`
          }}>
            {message}
          </div>
        )}

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <Link to="/" style={{ color: '#007bff', textDecoration: 'none' }}>
            ← Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}

export default PlayerPreferences;