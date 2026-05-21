from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, os, json, requests
import pandas as pd
from threading import Lock

app = FastAPI(title="Chess Asistance Models API")

PIPELINE_PATH    = os.getenv("PIPELINE_PATH",    "../trainer/models/model_pipeline.pkl")
AP_PIPELINE_PATH = os.getenv("AP_PIPELINE_PATH", "../trainers/trainer-ap/models/model_pipeline.pkl")
AP_ECO_MAP_PATH  = os.getenv("AP_ECO_MAP_PATH",  "../trainers/trainer-ap/data/eco_frequency_map.json")

if not os.path.exists(PIPELINE_PATH):
    raise RuntimeError("model_pipeline.pkl not found in /models/")
pipeline = joblib.load(PIPELINE_PATH)

if not os.path.exists(AP_PIPELINE_PATH):
    raise RuntimeError(f"AP model_pipeline.pkl not found at {AP_PIPELINE_PATH}")
ap_pipeline = joblib.load(AP_PIPELINE_PATH)

with open(AP_ECO_MAP_PATH) as f:
    eco_frequency_map: dict = json.load(f)

LICHESS_API = "https://lichess.org"
ALL_TCS = ["ultraBullet", "bullet", "blitz", "rapid", "classical", "correspondence"]

EMPTY_STATS = {
    "rapid_rating": None, "blitz_rating": None, "bullet_rating": None,
    "rapid_games": 0, "blitz_games": 0, "bullet_games": 0,
    "total_games": 0, "play_time_secs": 0,
}

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


def _lichess_get(path: str, params: dict = None) -> requests.Response:
    resp = requests.get(f"{LICHESS_API}{path}", params=params, timeout=10)
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Lichess API rate limit exceeded — try again in a moment")
    return resp


def _fetch_game(game_id: str) -> dict:
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
        f"{prefix}_rapid_rating":    rapid,
        f"{prefix}_blitz_rating":    blitz,
        f"{prefix}_bullet_rating":   bullet,
        f"{prefix}_rapid_games":     stats["rapid_games"],
        f"{prefix}_blitz_games":     stats["blitz_games"],
        f"{prefix}_bullet_games":    stats["bullet_games"],
        f"{prefix}_total_games":     total,
        f"{prefix}_play_time_secs":  ptime,
        f"{prefix}_avg_game_secs":   ptime / total if total > 0 else None,
        f"{prefix}_blitz_vs_rapid":  diff(blitz, rapid),
        f"{prefix}_bullet_vs_blitz": diff(bullet, blitz),
        f"{prefix}_bullet_vs_rapid": diff(bullet, rapid),
        f"{prefix}_rapid_ratio":     stats["rapid_games"]  / total if total > 0 else None,
        f"{prefix}_blitz_ratio":     stats["blitz_games"]  / total if total > 0 else None,
        f"{prefix}_bullet_ratio":    stats["bullet_games"] / total if total > 0 else None,
        f"{prefix}_profile_disabled": int(rapid is None or blitz is None or bullet is None),
    }


class ChanceWinrateFeatures(BaseModel):
    minutes_slept: float
    minutes_awake: float
    temperature_celsius: float
    co2: float
    light: float


@app.post("/predict")
def predict(data: ChanceWinrateFeatures):
    temp_dist = abs(data.temperature_celsius - 20)
    co2_norm  = (data.co2 - 400) / 1600
    env_score = 1 - (co2_norm * 0.7 + (temp_dist / 5) * 0.3)

    X = pd.DataFrame(
        [[data.minutes_slept, data.minutes_awake, env_score, data.light]],
        columns=["minutes_slept", "minutes_awake", "env_score", "light"],
    )
    return {"prediction": pipeline.predict_proba(X)[0][1]}

class AccuracyPredictorFeatures(BaseModel):
    game_id: str
    username: str
    opening_familiarity: int | None = None

@app.post("/predict/accuracy")
def predict_accuracy(data: AccuracyPredictorFeatures):
    game_id = data.game_id
    username = data.username
    game     = _fetch_game(game_id)
    players  = game.get("players", {})
    white    = players.get("white", {})
    black    = players.get("black", {})
    white_id = white.get("user", {}).get("id", "").lower()
    black_id = black.get("user", {}).get("id", "").lower()

    uname = username.lower()
    if uname == white_id:
        player_white, player_info, opponent_info, opponent_uname = 1, white, black, black_id
    elif uname == black_id:
        player_white, player_info, opponent_info, opponent_uname = 0, black, white, white_id
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Username '{username}' not found in game '{game_id}' (white: {white_id}, black: {black_id})",
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
        "opening_familiarity": data.opening_familiarity if data.opening_familiarity is not None else (_fetch_opening_familiarity(uname, eco, max_games=20) if eco else 0),
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
        "game_id":                  game_id,
        "username":                 username,
        "player_color":             "white" if player_white else "black",
        "predicted_centipawn_loss": prediction,
        "opening_eco":              eco,
        "opening_familiarity":      row["opening_familiarity"],
        "opening_ply" : row["opening_ply"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
