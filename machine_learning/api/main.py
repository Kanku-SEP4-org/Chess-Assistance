from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import joblib, json, math, numpy as np, os
import pandas as pd
import psycopg2

app = FastAPI(title="Chess Assistance Models API")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
angriness_model_features: list[str] | None = None
angriness_is_supervised: bool = False

if os.path.exists(ANGRINESS_MODEL_PATH):
    angriness_model = joblib.load(ANGRINESS_MODEL_PATH)
    angriness_scaler = joblib.load(ANGRINESS_SCALER_PATH)
    with open(ANGRINESS_BINS_PATH) as f:
        bins_data = json.load(f)
    angriness_bin_edges = bins_data["bin_edges"]
    angriness_model_features = bins_data.get("model_features")
    angriness_is_supervised = bins_data.get("supervised", False)

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


def _run_prediction(features: dict) -> dict:
    X = pd.DataFrame([features], columns=FEATURE_ORDER)
    X_scaled = pd.DataFrame(angriness_scaler.transform(X), columns=FEATURE_ORDER)
    if angriness_model_features:
        X_scaled = X_scaled[angriness_model_features]

    if angriness_is_supervised:
        angriness = int(angriness_model.predict(X_scaled.values)[0])
        return {"angriness": angriness}
    else:
        score = float(angriness_model.decision_function(X_scaled.values)[0])
        angriness = _score_to_angriness(score)
        return {"angriness": angriness, "score": round(score, 4)}


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

    return _run_prediction(features)


class AngrinessPredictionRawRequest(BaseModel):
    consecutive_losses_pregame: int = 0
    avg_tpm_seconds_player: float = 0
    blunder_cnt_player: int = 0
    mistake_cnt_player: int = 0
    inaccuracy_cnt_player: int = 0
    acpl_player: int = 0
    accuracy_player: int = 0
    elo: int = 0
    elo_diff: int = 0
    opponent_elo: int = 0
    elo_gap: int = 0
    time_control_initial: int = 600
    time_control_increment: int = 0
    move_cnt: int = 0
    move_cnt_player: int = 0
    sleep_duration: float = 7.0
    awaken_duration: float = 4.0
    avg_ppm: float = 1549.0
    avg_celsius: float = 25.17
    water_intake_ml: int = 700
    avg_lux: float = 400.0
    is_black: int = 0


@app.post("/predict-angriness-raw")
def predict_angriness_raw(data: AngrinessPredictionRawRequest):
    if angriness_model is None:
        raise HTTPException(status_code=503, detail="Angriness model not loaded")

    features = {k: v for k, v in data.model_dump().items()}
    return _run_prediction(features)


def _compute_features_from_lichess(game: dict, side: str) -> dict:
    other_side = "black" if side == "white" else "white"
    player = game["players"][side]
    opponent = game["players"][other_side]

    elo = player.get("rating", 0)
    opponent_elo = opponent.get("rating", 0)
    moves = game.get("moves", "").split()
    move_cnt = len(moves)
    is_black = 1 if side == "black" else 0
    move_cnt_player = math.floor(move_cnt / 2) if is_black else math.ceil(move_cnt / 2)
    duration_sec = (game.get("lastMoveAt", 0) - game.get("createdAt", 0)) / 1000
    avg_tpm = duration_sec / move_cnt_player if move_cnt_player > 0 else 0

    analysis = player.get("analysis", {})
    clock = game.get("clock", {})

    return {
        "consecutive_losses_pregame": 0,
        "avg_tpm_seconds_player": avg_tpm,
        "blunder_cnt_player": analysis.get("blunder", 0),
        "mistake_cnt_player": analysis.get("mistake", 0),
        "inaccuracy_cnt_player": analysis.get("inaccuracy", 0),
        "acpl_player": analysis.get("acpl", 0),
        "accuracy_player": analysis.get("accuracy", 0),
        "elo": elo,
        "elo_diff": player.get("ratingDiff", 0),
        "opponent_elo": opponent_elo,
        "elo_gap": elo - opponent_elo,
        "time_control_initial": clock.get("initial", 600),
        "time_control_increment": clock.get("increment", 0),
        "move_cnt": move_cnt,
        "move_cnt_player": move_cnt_player,
        "is_black": is_black,
    }


class GamePredictionRequest(BaseModel):
    game_id: str
    player_username: str
    consecutive_losses_pregame: int = 0


@app.post("/angriness/predict-by-game-id")
async def predict_by_game_id(data: GamePredictionRequest):
    if angriness_model is None:
        raise HTTPException(status_code=503, detail="Angriness model not loaded")

    game_id = data.game_id.strip()
    player_username = data.player_username.strip()

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://lichess.org/game/export/{game_id}",
            params={"evals": "true", "opening": "true", "pgnInJson": "true"},
            headers={"Accept": "application/json"},
        )

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Game not found: {game_id}")
    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="Lichess rate limit reached. Please try again in a moment.")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="Failed to fetch game from Lichess")

    game = r.json()

    user_lower = player_username.lower()
    side = None
    for s in ("white", "black"):
        if (game.get("players", {}).get(s, {}).get("user", {}).get("id", "").lower() == user_lower):
            side = s
            break

    if side is None:
        raise HTTPException(
            status_code=400,
            detail=f'Player "{player_username}" is not a participant in game {game_id}',
        )

    other_side = "black" if side == "white" else "white"
    player_data = game["players"][side]

    if not player_data.get("analysis"):
        return {
            "status": "analysis_required",
            "game_id": game["id"],
            "game_url": f"https://lichess.org/{game['id']}",
            "message": "This game has not been analyzed yet. Please visit the game on Lichess and click 'Request a computer analysis', then try again.",
        }

    features = _compute_features_from_lichess(game, side)
    features["consecutive_losses_pregame"] = data.consecutive_losses_pregame
    prediction = _run_prediction(features)

    clock = game.get("clock")
    time_control = (
        f"{clock['initial'] // 60}+{clock['increment']}"
        if clock
        else game.get("speed", "unknown")
    )

    return {
        "status": "ok",
        "game_id": game["id"],
        "game_url": f"https://lichess.org/{game['id']}",
        "player_side": side,
        "player_rating": player_data.get("rating", 0),
        "opponent_rating": game["players"][other_side].get("rating", 0),
        "opening": game.get("opening", {}).get("name"),
        "time_control": time_control,
        "angriness": prediction["angriness"],
        "score": prediction.get("score"),
    }


@app.get("/angriness/recent-games/{username}")
async def recent_games(username: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://lichess.org/api/games/user/{username}",
            params={"max": "15", "sort": "dateDesc", "pgnInJson": "true", "opening": "true", "evals": "true"},
            headers={"Accept": "application/x-ndjson"},
        )

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User not found: {username}")
    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="Lichess rate limit reached. Please try again in a moment.")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="Failed to fetch games from Lichess")

    lines = [line for line in r.text.split("\n") if line.strip()]
    all_games = []
    user_lower = username.lower()

    for line in lines:
        g = json.loads(line)
        is_white = (g.get("players", {}).get("white", {}).get("user", {}).get("id", "").lower() == user_lower)
        side = "white" if is_white else "black"
        other_side = "black" if is_white else "white"

        winner = g.get("winner")
        if winner == side:
            result = "win"
        elif winner == other_side:
            result = "loss"
        else:
            result = "draw"

        clock = g.get("clock")
        time_control = (
            f"{clock['initial'] // 60}+{clock['increment']}"
            if clock
            else g.get("speed", "unknown")
        )

        all_games.append({
            "game_id": g["id"],
            "opponent": g.get("players", {}).get(other_side, {}).get("user", {}).get("name", "Anonymous"),
            "result": result,
            "opening": g.get("opening", {}).get("name"),
            "time_control": time_control,
            "speed": g.get("speed"),
            "has_analysis": bool(g.get("players", {}).get(side, {}).get("analysis")),
            "played_at": pd.Timestamp(g["createdAt"], unit="ms").isoformat(),
        })

    for i in range(min(10, len(all_games))):
        streak = 0
        for j in range(i + 1, len(all_games)):
            if all_games[j]["result"] == "loss":
                streak += 1
            else:
                break
        all_games[i]["consecutive_losses_before"] = streak

    return {"games": all_games[:10]}


@app.get("/health")
def health():
    return {"status": "ok"}
