from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import joblib, json, math, numpy as np, os
import pandas as pd
import psycopg2
import requests

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
    raise RuntimeError(f"model_pipeline.pkl not found at {MODEL_PATH}")

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
# Environment recommendation
# ---------------------------------------------------------------------------

def calculate_recommendation_env_score(temperature_celsius: float, co2: float) -> float:
    temp_dist = abs(temperature_celsius - 20)
    co2_norm = (co2 - 400) / 1600
    return 1 - (co2_norm * 0.7 + (temp_dist / 5) * 0.3)


def build_recommendation_winrate_frame(
    minutes_slept: float,
    minutes_awake: float,
    temperature_celsius: float,
    co2: float,
    light: float,
) -> pd.DataFrame:
    env_score = calculate_recommendation_env_score(temperature_celsius, co2)
    return pd.DataFrame(
        [[minutes_slept, minutes_awake, env_score, light]],
        columns=['minutes_slept', 'minutes_awake', 'env_score', 'light'],
    )


def predict_recommendation_win_probability(
    minutes_slept: float,
    minutes_awake: float,
    temperature_celsius: float,
    co2: float,
    light: float,
) -> float:
    X = build_recommendation_winrate_frame(
        minutes_slept,
        minutes_awake,
        temperature_celsius,
        co2,
        light,
    )
    return float(pipeline.predict_proba(X)[0][1])


def round_probability(value: float) -> float:
    return round(float(value), 3)


def round_percentage_points(value: float) -> float:
    return round(float(value), 2)


@app.post("/recommend-environment")
def recommend_environment(data: ChanceWinrateFeatures):
    current_probability = predict_recommendation_win_probability(
        data.minutes_slept,
        data.minutes_awake,
        data.temperature_celsius,
        data.co2,
        data.light,
    )

    candidates = [
        ("temperature_celsius", data.temperature_celsius, 20),
        ("co2", data.co2, 500),
        ("light", data.light, 1500),
    ]

    all_candidates = []
    for factor, current_value, recommended_value in candidates:
        candidate_values = {
            "minutes_slept": data.minutes_slept,
            "minutes_awake": data.minutes_awake,
            "temperature_celsius": data.temperature_celsius,
            "co2": data.co2,
            "light": data.light,
        }
        candidate_values[factor] = recommended_value

        win_probability = predict_recommendation_win_probability(**candidate_values)
        increase = win_probability - current_probability
        all_candidates.append({
            "factor": factor,
            "current_value": float(current_value),
            "recommended_value": float(recommended_value),
            "win_probability": round_probability(win_probability),
            "increase": round_probability(increase),
            "increase_percentage_points": round_percentage_points(increase * 100),
        })

    positive_candidates = [candidate for candidate in all_candidates if candidate["increase"] > 0]
    if not positive_candidates:
        return {
            "current_win_probability": round_probability(current_probability),
            "recommended_factor": None,
            "message": "No environmental improvement increased the prediction according to the model.",
            "all_candidates": all_candidates,
        }

    best_candidate = max(positive_candidates, key=lambda candidate: candidate["increase"])
    return {
        "current_win_probability": round_probability(current_probability),
        "recommended_factor": best_candidate["factor"],
        "current_value": best_candidate["current_value"],
        "recommended_value": best_candidate["recommended_value"],
        "improved_win_probability": best_candidate["win_probability"],
        "increase": best_candidate["increase"],
        "increase_percentage_points": best_candidate["increase_percentage_points"],
        "message": (
            f"Changing {best_candidate['factor']} from {best_candidate['current_value']} "
            f"to {best_candidate['recommended_value']} may increase your win probability by "
            f"{best_candidate['increase_percentage_points']:.1f} percentage points."
        ),
        "all_candidates": all_candidates,
    }

# ---------------------------------------------------------------------------
# Angriness model
# ---------------------------------------------------------------------------

ANGRINESS_MODEL_PATH = os.getenv(
    "ANGRINESS_MODEL_PATH",
    "../trainers/trainer-angriness-predictor/models/model.pkl",
)
ANGRINESS_BINS_PATH = os.getenv(
    "ANGRINESS_BINS_PATH",
    "../trainers/trainer-angriness-predictor/models/angriness_bins.json",
)
DATABASE_URL = os.getenv("DATABASE_URL", "")

angriness_model = None
angriness_bin_edges: list[float] = []

ANGRINESS_FEATURES = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
]

if os.path.exists(ANGRINESS_MODEL_PATH):
    angriness_model = joblib.load(ANGRINESS_MODEL_PATH)
    with open(ANGRINESS_BINS_PATH) as f:
        bins_data = json.load(f)
    angriness_bin_edges = bins_data["bin_edges"]

DATASET_QUERY = """
SELECT
    d.consecutive_losses_pregame,
    d.avg_tpm_seconds,
    d.blunder_cnt,
    d.mistake_cnt,
    d.inaccuracy_cnt,
    d.acpl,
    d.accuracy
FROM chess_assistant.dataset d
WHERE d.match_id = %s
"""


def _get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    return psycopg2.connect(DATABASE_URL)


def _run_prediction(features: dict) -> dict:
    X = pd.DataFrame([features], columns=ANGRINESS_FEATURES)
    angriness = int(angriness_model.predict(X.values)[0])
    return {"angriness": angriness}


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
    ) = row

    features = {
        "consecutive_losses_pregame": consecutive_losses_pregame or 0,
        "avg_tpm_seconds_player": float(avg_tpm_seconds or 0),
        "blunder_cnt_player": blunder_cnt or 0,
        "mistake_cnt_player": mistake_cnt or 0,
        "inaccuracy_cnt_player": inaccuracy_cnt or 0,
        "acpl_player": acpl or 0,
        "accuracy_player": accuracy or 0,
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


@app.post("/predict-angriness-raw")
def predict_angriness_raw(data: AngrinessPredictionRawRequest):
    if angriness_model is None:
        raise HTTPException(status_code=503, detail="Angriness model not loaded")

    features = {k: v for k, v in data.model_dump().items()}
    return _run_prediction(features)


def _compute_features_from_lichess(game: dict, side: str) -> dict:
    player = game["players"][side]
    moves = game.get("moves", "").split()
    move_cnt = len(moves)
    is_black = 1 if side == "black" else 0
    move_cnt_player = math.floor(move_cnt / 2) if is_black else math.ceil(move_cnt / 2)
    duration_sec = (game.get("lastMoveAt", 0) - game.get("createdAt", 0)) / 1000
    avg_tpm = duration_sec / move_cnt_player if move_cnt_player > 0 else 0

    analysis = player.get("analysis", {})

    return {
        "consecutive_losses_pregame": 0,
        "avg_tpm_seconds_player": avg_tpm,
        "blunder_cnt_player": analysis.get("blunder", 0),
        "mistake_cnt_player": analysis.get("mistake", 0),
        "inaccuracy_cnt_player": analysis.get("inaccuracy", 0),
        "acpl_player": analysis.get("acpl", 0),
        "accuracy_player": analysis.get("accuracy", 0),
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

# ---------------------------------------------------------------------------
# Accuracy predictor
# ---------------------------------------------------------------------------

LICHESS_API = "https://lichess.org"
ALL_TCS = ["ultraBullet", "bullet", "blitz", "rapid", "classical", "correspondence"]

EMPTY_STATS = {
    "rapid_rating": None, "blitz_rating": None, "bullet_rating": None,
    "rapid_games": 0, "blitz_games": 0, "bullet_games": 0,
    "total_games": 0, "play_time_secs": 0,
}

AP_PIPELINE_PATH = os.getenv("AP_PIPELINE_PATH", "../trainers/trainer-ap/models/model_pipeline.pkl")
AP_ECO_MAP_PATH  = os.getenv("AP_ECO_MAP_PATH",  "../trainers/trainer-ap/data/eco_frequency_map.json")

if not os.path.exists(AP_PIPELINE_PATH):
    raise RuntimeError(f"AP model_pipeline.pkl not found at {AP_PIPELINE_PATH}")
ap_pipeline = joblib.load(AP_PIPELINE_PATH)

with open(AP_ECO_MAP_PATH) as f:
    eco_frequency_map: dict = json.load(f)

AP_FEATURE_COLS = [
    "player_rating", "opponent_rating", "player_white", "opening_ply",
    "elo_delta_ratio", "opening_frequency", "opening_familiarity",
    "player_rapid_rating", "opponent_rapid_rating",
    "player_rapid_games", "opponent_rapid_games",
    "player_blitz_rating", "opponent_blitz_rating",
    "player_blitz_games", "opponent_blitz_games",
    "player_bullet_rating", "opponent_bullet_rating",
    "player_bullet_games", "opponent_bullet_games",
    "player_total_games", "opponent_total_games",
    "player_play_time_secs", "opponent_play_time_secs",
    "player_avg_game_secs", "opponent_avg_game_secs",
    "player_blitz_vs_rapid", "player_bullet_vs_blitz", "player_bullet_vs_rapid",
    "opponent_blitz_vs_rapid", "opponent_bullet_vs_blitz", "opponent_bullet_vs_rapid",
    "player_rapid_ratio", "player_blitz_ratio", "player_bullet_ratio",
    "opponent_rapid_ratio", "opponent_blitz_ratio", "opponent_bullet_ratio",
    "rapid_rating_gap", "blitz_rating_gap",
    "total_games_gap", "rapid_games_gap", "play_time_gap",
    "player_profile_disabled", "opponent_profile_disabled",
]


def _lichess_get(path: str, params: dict = None):
    import requests
    resp = requests.get(f"{LICHESS_API}{path}", params=params, timeout=10)
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Lichess API rate limit exceeded — try again in a moment")
    return resp


def _fetch_game(game_id: str) -> dict:
    import requests
    resp = requests.post(
        f"{LICHESS_API}/games/export/_ids",
        params={"moves": "false", "clocks": "false", "evals": "false", "opening": "true"},
        data=game_id[:8],
        headers={"Accept": "application/x-ndjson"},
        timeout=10,
    )
    if resp.status_code == 429:
        raise HTTPException(status_code=503, detail="Lichess API rate limit exceeded")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Lichess returned {resp.status_code} for game export")
    for line in resp.text.strip().split("\n"):
        if line:
            return json.loads(line)
    raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found on Lichess")


def _fetch_user_stats(username: str) -> dict:
    resp = _lichess_get(f"/api/user/{username}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found on Lichess")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Lichess returned {resp.status_code} for user '{username}'")
    data  = resp.json()
    perfs = data.get("perfs", {})
    return {
        "rapid_rating":   perfs.get("rapid",  {}).get("rating"),
        "rapid_games":    perfs.get("rapid",  {}).get("games", 0),
        "blitz_rating":   perfs.get("blitz",  {}).get("rating"),
        "blitz_games":    perfs.get("blitz",  {}).get("games", 0),
        "bullet_rating":  perfs.get("bullet", {}).get("rating"),
        "bullet_games":   perfs.get("bullet", {}).get("games", 0),
        "total_games":    sum(perfs.get(tc, {}).get("games", 0) for tc in ALL_TCS),
        "play_time_secs": data.get("playTime", {}).get("total", 0),
    }


def _fetch_opening_familiarity(username: str, eco: str, max_games: int = 200) -> int:
    resp = _lichess_get(
        f"/api/games/user/{username}",
        params={"max": max_games, "opening": "true", "moves": "false", "clocks": "false", "evals": "false"},
    )
    if resp.status_code != 200:
        return 0
    count = 0
    for line in resp.text.strip().split("\n"):
        try:
            if line and json.loads(line).get("opening", {}).get("eco") == eco:
                count += 1
        except json.JSONDecodeError:
            pass
    return count


def _build_player_features(stats: dict, prefix: str) -> dict:
    rapid, blitz, bullet = stats["rapid_rating"], stats["blitz_rating"], stats["bullet_rating"]
    total, ptime = stats["total_games"], stats["play_time_secs"]

    def diff(a, b):
        return (a - b) if (a is not None and b is not None) else None

    return {
        f"{prefix}_rapid_rating":     rapid,
        f"{prefix}_blitz_rating":     blitz,
        f"{prefix}_bullet_rating":    bullet,
        f"{prefix}_rapid_games":      stats["rapid_games"],
        f"{prefix}_blitz_games":      stats["blitz_games"],
        f"{prefix}_bullet_games":     stats["bullet_games"],
        f"{prefix}_total_games":      total,
        f"{prefix}_play_time_secs":   ptime,
        f"{prefix}_avg_game_secs":    ptime / total if total > 0 else None,
        f"{prefix}_blitz_vs_rapid":   diff(blitz, rapid),
        f"{prefix}_bullet_vs_blitz":  diff(bullet, blitz),
        f"{prefix}_bullet_vs_rapid":  diff(bullet, rapid),
        f"{prefix}_rapid_ratio":      stats["rapid_games"]  / total if total > 0 else None,
        f"{prefix}_blitz_ratio":      stats["blitz_games"]  / total if total > 0 else None,
        f"{prefix}_bullet_ratio":     stats["bullet_games"] / total if total > 0 else None,
        f"{prefix}_profile_disabled": int(rapid is None or blitz is None or bullet is None),
    }


class AccuracyPredictorFeatures(BaseModel):
    game_id: str
    username: str
    opening_familiarity: int | None = None


@app.post("/predict/accuracy")
def predict_accuracy(data: AccuracyPredictorFeatures):
    game     = _fetch_game(data.game_id)
    players  = game.get("players", {})
    white    = players.get("white", {})
    black    = players.get("black", {})
    white_id = white.get("user", {}).get("id", "").lower()
    black_id = black.get("user", {}).get("id", "").lower()

    uname = data.username.lower()
    if uname == white_id:
        player_white, player_info, opponent_info, opponent_uname = 1, white, black, black_id
    elif uname == black_id:
        player_white, player_info, opponent_info, opponent_uname = 0, black, white, white_id
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' not found in game '{data.game_id}' (white: {white_id}, black: {black_id})",
        )

    opening = game.get("opening", {})
    eco     = opening.get("eco", "")
    pr      = player_info.get("rating") or 0
    opr     = opponent_info.get("rating") or 0

    pf = _build_player_features(_fetch_user_stats(uname), "player")
    of = _build_player_features(
        _fetch_user_stats(opponent_uname) if opponent_uname else EMPTY_STATS, "opponent"
    )

    def gap(pk, ok):
        pv, ov = pf[pk], of[ok]
        return (pv - ov) if (pv is not None and ov is not None) else None

    row = {
        "player_rating":       pr,
        "opponent_rating":     opr,
        "player_white":        player_white,
        "opening_ply":         opening.get("ply", 0),
        "elo_delta_ratio":     (pr - opr) / ((pr + opr) / 2 or 1),
        "opening_frequency":   eco_frequency_map.get(eco, 2),
        "opening_familiarity": data.opening_familiarity if data.opening_familiarity is not None
                               else (_fetch_opening_familiarity(uname, eco, max_games=20) if eco else 0),
        **pf,
        **of,
        "rapid_rating_gap": gap("player_rapid_rating", "opponent_rapid_rating"),
        "blitz_rating_gap": gap("player_blitz_rating", "opponent_blitz_rating"),
        "total_games_gap":  pf["player_total_games"]    - of["opponent_total_games"],
        "rapid_games_gap":  pf["player_rapid_games"]    - of["opponent_rapid_games"],
        "play_time_gap":    pf["player_play_time_secs"] - of["opponent_play_time_secs"],
    }

    X          = pd.DataFrame([row])[AP_FEATURE_COLS]
    prediction = round(float(ap_pipeline.predict(X)[0]), 2)

    return {
        "game_id":                  data.game_id,
        "username":                 data.username,
        "player_color":             "white" if player_white else "black",
        "predicted_centipawn_loss": prediction,
        "opening_eco":              eco,
        "opening_familiarity":      row["opening_familiarity"],
        "opening_ply":              row["opening_ply"],
    }

# ---------------------------------------------------------------------------
# Factor impact reports
# ---------------------------------------------------------------------------

FACTOR_IMPACT_REPORT_PATH = os.getenv(
    "FACTOR_IMPACT_REPORT_PATH",
    "../trainers/trainer-factor-imp/models/factor_impact_report.json",
)
FACTOR_IMPACT_COMPARISON_PATH = os.getenv(
    "FACTOR_IMPACT_COMPARISON_PATH",
    "../trainers/trainer-factor-imp/models/model_comparison.json",
)
FACTOR_IMPACT_VALIDATION_PATH = os.getenv(
    "FACTOR_IMPACT_VALIDATION_PATH",
    "../trainers/trainer-factor-imp/models/factor_impact_validation.json",
)

factor_impact_report: dict | None = None
factor_impact_comparison: dict | None = None
factor_impact_validation: dict | None = None

if os.path.exists(FACTOR_IMPACT_REPORT_PATH):
    with open(FACTOR_IMPACT_REPORT_PATH) as f:
        factor_impact_report = json.load(f)

if os.path.exists(FACTOR_IMPACT_COMPARISON_PATH):
    with open(FACTOR_IMPACT_COMPARISON_PATH) as f:
        factor_impact_comparison = json.load(f)

if os.path.exists(FACTOR_IMPACT_VALIDATION_PATH):
    with open(FACTOR_IMPACT_VALIDATION_PATH) as f:
        factor_impact_validation = json.load(f)


@app.get("/factor-impact/report")
def get_factor_impact_report():
    if factor_impact_report is None:
        raise HTTPException(status_code=503, detail="Factor impact report not loaded")
    return factor_impact_report


@app.get("/factor-impact/comparison")
def get_factor_impact_comparison():
    if factor_impact_comparison is None:
        raise HTTPException(status_code=503, detail="Factor impact comparison not loaded")
    return factor_impact_comparison


@app.get("/factor-impact/validation")
def get_factor_impact_validation():
    if factor_impact_validation is None:
        raise HTTPException(status_code=503, detail="Factor impact validation not loaded")
    return factor_impact_validation


@app.get("/health")
def health():
    return {"status": "ok"}
