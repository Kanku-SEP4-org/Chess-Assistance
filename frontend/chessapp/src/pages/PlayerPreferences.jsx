import { useState } from 'react';
import { Link } from 'react-router-dom';
import '../App.css';
import Header from '../components/Header';
import heroImg from '../assets/chess-bg.png';

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
      //idk havent checked if theres an endpoint like that
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
    <main className="min-vh-100 bg-dark text-white" style={{ backgroundImage: `url(${heroImg})`, backgroundSize: 'auto 115vh', backgroundPosition: 'right top', backgroundRepeat: 'no-repeat', backgroundAttachment: 'fixed' }}>
      <Header />

      <div className="container" style={{ maxWidth: '600px', marginTop: '2rem', marginBottom: '2rem' }}>
        <div className="card text-white bg-black bg-opacity-50 bg-dark.bg-gradient border border-white border-opacity-10 rounded-4 p-4 mb-5">
          <h1 className="card-title text-center mb-4">Player Preferences</h1>

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="daily_game_limit" className="form-label fw-bold text-white">
                  Daily Game Limit:
                </label>
                <input
                  type="number" 
                  className="form-control bg-black bg-opacity-10 border border-white border-opacity-15 text-white rounded-3 px-3 py-2"
                  id="daily_game_limit"
                  name="daily_game_limit"
                  value={preferences.daily_game_limit}
                  onChange={handleChange}
                  min="1"
                  required
                  placeholder="Enter maximum games per day"
                />
              </div>

              <div className="mb-3">
                <label htmlFor="daily_playtime_limit_min" className="form-label fw-bold text-white">
                  Daily Playtime Limit (minutes):
                </label>
                <input
                  type="number"
                  className="form-control bg-black bg-opacity-10 border border-white border-opacity-15 text-white rounded-3 px-3 py-2"
                  id="daily_playtime_limit_min"
                  name="daily_playtime_limit_min"
                  value={preferences.daily_playtime_limit_min}
                  onChange={handleChange}
                  min="1"
                  required
                  placeholder="Enter maximum playtime in minutes"
                />
              </div>

              <div className="mb-3">
                <label htmlFor="break_interval_min" className="form-label fw-bold text-white">
                  Break Interval (minutes):
                </label>
                <input
                  type="number"
                  className="form-control bg-black bg-opacity-10 border border-white border-opacity-15 text-white rounded-3 px-3 py-2"
                  id="break_interval_min"
                  name="break_interval_min"
                  value={preferences.break_interval_min}
                  onChange={handleChange}
                  min="1"
                  required
                  placeholder="Enter break interval in minutes"
                />
              </div>

              <div className="mb-4">
                <label htmlFor="recommend_rest_min" className="form-label fw-bold text-white">
                  Recommended Rest (minutes):
                </label>
                <input
                  type="number"
                  className="form-control bg-black bg-opacity-10 border border-white border-opacity-15 text-white rounded-3 px-3 py-2"
                  id="recommend_rest_min"
                  name="recommend_rest_min"
                  value={preferences.recommend_rest_min}
                  onChange={handleChange}
                  min="1"
                  required
                  placeholder="Enter recommended rest time in minutes"
                />
              </div>

              <button
                type="submit"
                className={`btn text-dark fw-bold px-4 py-3 rounded-pill border-0 w-100 text-black ${loading ? 'disabled' : ''}`}
                style={{ background: 'linear-gradient(135deg, #d8aa55, #8f6425)' }}
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Preferences'}
              </button>
            </form>

            {message && (
              <div className={`alert mt-3 ${message.includes('successfully') ? 'alert-success bg-success bg-opacity-10 border border-success border-opacity-25 text-success' : 'alert-danger bg-danger bg-opacity-10 border border-danger border-opacity-25 text-danger'} rounded-3`}>
                {message}
              </div>
            )}
          </div>
        </div>

    </main>
  );
}

export default PlayerPreferences;