from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, json, numpy as np, os
import pandas as pd
import psycopg2

app = FastAPI(title="Chess Assistance Models API")

# ---------------------------------------------------------------------------
# Winrate model
# ---------------------------------------------------------------------------

MODEL_PATH = os.getenv("MODEL_PATH", "../trainers/trainer-winrate/models/model.pkl")

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"model.pkl not found at {MODEL_PATH}")

pipeline = joblib.load(MODEL_PATH)

class ChanceWinrateFeatures(BaseModel):
    minutes_slept: float
    minutes_awake:  float
    temperature_celsius: float
    co2:  float
    light:  float

@app.post("/predict")
def predict(data: ChanceWinrateFeatures):

    temp_dist = abs(data.temperature_celsius - 20)
    co2_norm = (data.co2 - 400) / 1600
    env_score = 1 - (co2_norm * 0.7 + (temp_dist / 5)* 0.3)

    X = pd.DataFrame([[
    data.minutes_slept,
    data.minutes_awake,
    env_score,
    data.light
    ]], columns=['minutes_slept','minutes_awake', 'env_score','light'])
    prediction_proba = pipeline.predict_proba(X)
    return {
        "prediction": prediction_proba[0][1]
    }

# ---------------------------------------------------------------------------
# Angriness model
# ---------------------------------------------------------------------------

ANGRINESS_MODEL_PATH = os.getenv(
    "ANGRINESS_MODEL_PATH",
    "../trainers/trainer-angriness-predictor/models/model.pkl",
)
ANGRINESS_SCALER_PATH = os.getenv(
    "ANGRINESS_SCALER_PATH",
    "../trainers/trainer-angriness-predictor/models/scaler.pkl",
)
ANGRINESS_BINS_PATH = os.getenv(
    "ANGRINESS_BINS_PATH",
    "../trainers/trainer-angriness-predictor/models/angriness_bins.json",
)
DATABASE_URL = os.getenv("DATABASE_URL", "")

angriness_model = None
angriness_scaler = None
angriness_bin_edges: list[float] = []

if os.path.exists(ANGRINESS_MODEL_PATH):
    angriness_model = joblib.load(ANGRINESS_MODEL_PATH)
    angriness_scaler = joblib.load(ANGRINESS_SCALER_PATH)
    with open(ANGRINESS_BINS_PATH) as f:
        angriness_bin_edges = json.load(f)["bin_edges"]

FEATURE_ORDER = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
    "elo",
    "elo_diff",
    "opponent_elo",
    "elo_gap",
    "time_control_initial",
    "time_control_increment",
    "move_cnt",
    "move_cnt_player",
    "sleep_duration",
    "awaken_duration",
    "avg_ppm",
    "avg_celsius",
    "water_intake_ml",
    "avg_lux",
    "is_black",
]

TIME_CONTROL_SECONDS = {
    "bullet": 60,
    "blitz": 300,
    "rapid": 600,
    "classical": 1800,
}

DATASET_QUERY = """
SELECT
    d.consecutive_losses_pregame,
    d.avg_tpm_seconds,
    d.blunder_cnt,
    d.mistake_cnt,
    d.inaccuracy_cnt,
    d.acpl,
    d.accuracy,
    d.user_rating,
    d.rating_diff,
    d.opp_rating,
    d.user_rating - d.opp_rating AS elo_gap,
    d.time_control,
    d.time_increase_sec,
    d.total_ply,
    d.player_move_count,
    EXTRACT(EPOCH FROM d.sleep_duration) / 3600.0 AS sleep_hours,
    EXTRACT(EPOCH FROM d.awake_duration) / 3600.0 AS awake_hours,
    d.avg_ppm,
    d.avg_celsius,
    d.water_intake_ml,
    d.avg_lux,
    d.is_player_piece_black
FROM chess_assistant.dataset d
WHERE d.match_id = %s
"""


def _get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    return psycopg2.connect(DATABASE_URL)


def _score_to_angriness(score: float) -> int:
    for i in range(len(angriness_bin_edges) - 1):
        if score <= angriness_bin_edges[i + 1]:
            return 5 - i
    return 1


class AngrinessPredictionRequest(BaseModel):
    match_id: int


@app.post("/predict-angriness")
def predict_angriness(data: AngrinessPredictionRequest):
    if angriness_model is None:
        raise HTTPException(status_code=503, detail="Angriness model not loaded")

    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(DATASET_QUERY, (data.match_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No dataset row for match_id={data.match_id}")

    (
        consecutive_losses_pregame,
        avg_tpm_seconds,
        blunder_cnt,
        mistake_cnt,
        inaccuracy_cnt,
        acpl,
        accuracy,
        user_rating,
        rating_diff,
        opp_rating,
        elo_gap,
        time_control,
        time_increase_sec,
        total_ply,
        player_move_count,
        sleep_hours,
        awake_hours,
        avg_ppm,
        avg_celsius,
        water_intake_ml,
        avg_lux,
        is_player_piece_black,
    ) = row

    features = {
        "consecutive_losses_pregame": consecutive_losses_pregame or 0,
        "avg_tpm_seconds_player": float(avg_tpm_seconds or 0),
        "blunder_cnt_player": blunder_cnt or 0,
        "mistake_cnt_player": mistake_cnt or 0,
        "inaccuracy_cnt_player": inaccuracy_cnt or 0,
        "acpl_player": acpl or 0,
        "accuracy_player": accuracy or 0,
        "elo": user_rating or 0,
        "elo_diff": rating_diff or 0,
        "opponent_elo": opp_rating or 0,
        "elo_gap": elo_gap or 0,
        "time_control_initial": TIME_CONTROL_SECONDS.get(time_control, 600),
        "time_control_increment": time_increase_sec or 0,
        "move_cnt": total_ply or 0,
        "move_cnt_player": player_move_count or 0,
        "sleep_duration": float(sleep_hours or 7.0),
        "awaken_duration": float(awake_hours or 4.0),
        "avg_ppm": float(avg_ppm or 1549),
        "avg_celsius": float(avg_celsius or 25.17),
        "water_intake_ml": water_intake_ml or 700,
        "avg_lux": float(avg_lux or 400),
        "is_black": int(is_player_piece_black) if is_player_piece_black is not None else 0,
    }

    X = pd.DataFrame([features], columns=FEATURE_ORDER)
    X_scaled = angriness_scaler.transform(X)
    score = float(angriness_model.decision_function(X_scaled)[0])
    angriness = _score_to_angriness(score)

    return {"angriness": angriness, "score": round(score, 4)}


@app.get("/health")
def health():
    return {"status": "ok"}
