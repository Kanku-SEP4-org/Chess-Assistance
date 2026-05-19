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
    <>
      <Navbar />

      <main
        className="min-vh-100 text-white d-flex align-items-center py-5"
        style={{
          backgroundImage: `url(${heroImg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >

        <div className="container">

          <div className="row justify-content-center">

            <div className="col-12 col-md-10 col-lg-8">

              <div
                className="card bg-dark bg-opacity-50 border border-light border-opacity-10 shadow-lg rounded-4 p-4 p-md-5"
                style={{
                  backdropFilter: "blur(12px)",
                }}
              >

                <div className="text-center mb-5">

                  <p
                    className="text-warning text-uppercase fw-bold mb-2"
                    style={{
                      letterSpacing: "2px",
                    }}
                  >
                    Player Settings
                  </p>

                  <h2 className="fw-bold mb-3">
                    Player Preferences
                  </h2>

                  <p className="text-light opacity-75 mb-0">
                    Customize your chess session limits and
                    rest recommendations.
                  </p>

                </div>

                <form onSubmit={handleSubmit}>

                  <div className="row g-4">

                    <div className="col-12 col-md-6">
                      <label className="form-label fw-semibold">
                        Daily Game Limit
                      </label>

                      <input
                        type="number"
                        className="form-control form-control-lg"
                        name="daily_game_limit"
                        value={preferences.daily_game_limit}
                        onChange={handleChange}
                        placeholder="Enter game limit"
                      />
                    </div>

                    <div className="col-12 col-md-6">
                      <label className="form-label fw-semibold">
                        Daily Playtime Limit (min)
                      </label>

                      <input
                        type="number"
                        className="form-control form-control-lg"
                        name="daily_playtime_limit_min"
                        value={preferences.daily_playtime_limit_min}
                        onChange={handleChange}
                        placeholder="Enter minutes"
                      />
                    </div>

                    <div className="col-12 col-md-6">
                      <label className="form-label fw-semibold">
                        Break Interval (min)
                      </label>

                      <input
                        type="number"
                        className="form-control form-control-lg"
                        name="break_interval_min"
                        value={preferences.break_interval_min}
                        onChange={handleChange}
                        placeholder="Enter break interval"
                      />
                    </div>

                    <div className="col-12 col-md-6">
                      <label className="form-label fw-semibold">
                        Recommended Rest (min)
                      </label>

                      <input
                        type="number"
                        className="form-control form-control-lg"
                        name="recommend_rest_min"
                        value={preferences.recommend_rest_min}
                        onChange={handleChange}
                        placeholder="Enter rest duration"
                      />
                    </div>

                    <div className="col-12">
                      <label className="form-label fw-semibold">
                        Player ID
                      </label>

                      <input
                        type="number"
                        className="form-control form-control-lg"
                        name="player_id"
                        value={preferences.player_id}
                        onChange={handleChange}
                        placeholder="Enter player ID"
                      />
                    </div>

                  </div>

                  <div className="d-grid mt-5">

                    <button
                      className="btn btn-warning btn-lg fw-bold rounded-pill"
                      type="submit"
                    >
                      Save Preferences
                    </button>

                  </div>

                  {saved && (
                    <div className="alert alert-success mt-4 text-center">
                      Preferences saved successfully!
                    </div>
                  )}

                </form>

              </div>

            </div>

          </div>

        </div>

      </main>
    </>
  );
}

export default PlayerPreference;