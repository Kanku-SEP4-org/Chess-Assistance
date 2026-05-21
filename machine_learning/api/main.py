from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, numpy as np, os
import pandas as pd

app = FastAPI(title="Chess Asistance Models API")

MODEL_PATH  = os.getenv("MODEL_PATH", "../trainer/models/model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "../trainer/models/scaler.pkl")

ARTIFACT_PATH = os.getenv("MODEL_V2_PATH", "models_v2/chess_ai_v2.pkl")

if not os.path.exists(ARTIFACT_PATH):
    raise RuntimeError(f"Model artifact not found at {ARTIFACT_PATH}")


artifacts = joblib.load(ARTIFACT_PATH)
model = artifacts['model']
km_env = artifacts['km_env']
km_game = artifacts['km_game']
scaler_env = artifacts['scaler_env']
scaler_game = artifacts['scaler_game']

class ChessPredictionInput(BaseModel):
    avg_lumen: float
    avg_celsius: float
    avg_ppm: float
    avg_ml: float
    rating_diff: int
    total_ply: int
    opening_ply: int
    player_move_count: int
    duration_min: int
    player_opening_win_rate: float
    sleep_hours: float
    eco_code: str
    time_control: str
    is_berserk: bool
    is_player_piece_black: bool

@app.post("/predict")
def predict(data: ChessPredictionInput):
    env_data = pd.DataFrame([[
        data.avg_lumen, data.avg_celsius, data.avg_ppm, data.avg_ml
    ]], columns=['avg_lumen', 'avg_celsius', 'avg_ppm', 'avg_ml'])

    game_data = pd.DataFrame([[
        data.rating_diff, data.total_ply, data.opening_ply, 
        data.player_move_count, data.duration_min, 
        data.player_opening_win_rate, data.sleep_hours
    ]], columns=[
        'rating_diff', 'total_ply', 'opening_ply', 'player_move_count', 
        'duration_min', 'player_opening_win_rate', 'sleep_hours'
    ])

    env_scaled = scaler_env.transform(env_data)
    game_scaled = scaler_game.transform(game_data)
    
    env_cluster = km_env.predict(env_scaled)[0]
    game_cluster = km_game.predict(game_scaled)[0]

  
    X_final = pd.DataFrame([{
        **env_data.iloc[0].to_dict(),
        **game_data.iloc[0].to_dict(),
        'eco_code': data.eco_code,
        'time_control': data.time_control,
        'is_berserk': data.is_berserk,
        'is_player_piece_black': data.is_player_piece_black,
        'env_cluster': env_cluster,
        'game_cluster': game_cluster
    }])

    prediction_proba = model.predict_proba(X_final)
    
    return {
        "win_probability": round(float(prediction_proba[0][1]), 4),
        "environmental_profile": int(env_cluster),
        "performance_profile": int(game_cluster)
    }

@app.get("/health")
def health():
    return {"status": "ok"}
