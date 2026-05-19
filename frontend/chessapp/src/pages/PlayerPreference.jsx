import { useState } from "react";
import Navbar from "../components/Navbar";
import heroImg from "../assets/chess-bg.png";
import "../App.css";

function PlayerPreference() {
  const [preferences, setPreferences] = useState({
    daily_game_limit: "",
    daily_playtime_limit_min: "",
    break_interval_min: "",
    recommend_rest_min: "",
    player_id: "",
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (e) => {
    setPreferences({
      ...preferences,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    console.log("Saved Preferences:", preferences);

    setSaved(true);

    setTimeout(() => {
      setSaved(false);
    }, 3000);
  };

  return (
    <main
      className="app"
      style={{ backgroundImage: `url(${heroImg})` }}
    >
      <Navbar />

      <section className="dashboard">
        <div className="session-card preference-card">
          <div>
            <p className="eyebrow">Player Settings</p>
            <h2>Player Preferences</h2>
            <p>
              Customize your chess session limits and rest recommendations.
            </p>
          </div>

          <form className="preferences-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="input-group">
                <label>Daily Game Limit</label>
                <input
                  type="number"
                  name="daily_game_limit"
                  value={preferences.daily_game_limit}
                  onChange={handleChange}
                  placeholder="Enter game limit"
                />
              </div>

              <div className="input-group">
                <label>Daily Playtime Limit (min)</label>
                <input
                  type="number"
                  name="daily_playtime_limit_min"
                  value={preferences.daily_playtime_limit_min}
                  onChange={handleChange}
                  placeholder="Minutes"
                />
              </div>

              <div className="input-group">
                <label>Break Interval (min)</label>
                <input
                  type="number"
                  name="break_interval_min"
                  value={preferences.break_interval_min}
                  onChange={handleChange}
                  placeholder="Minutes"
                />
              </div>

              <div className="input-group">
                <label>Recommended Rest (min)</label>
                <input
                  type="number"
                  name="recommend_rest_min"
                  value={preferences.recommend_rest_min}
                  onChange={handleChange}
                  placeholder="Minutes"
                />
              </div>

              <div className="input-group">
                <label>Player ID</label>
                <input
                  type="number"
                  name="player_id"
                  value={preferences.player_id}
                  onChange={handleChange}
                  placeholder="Player ID"
                />
              </div>
            </div>

            <button className="start-btn" type="submit">
              Save Preferences
            </button>

            {saved && (
              <p className="success-text">
                Preferences saved successfully!
              </p>
            )}
          </form>
        </div>
      </section>
    </main>
  );
}

export default PlayerPreference;