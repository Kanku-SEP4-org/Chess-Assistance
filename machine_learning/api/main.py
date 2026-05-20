from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, numpy as np, os
import pandas as pd

app = FastAPI(title="Chess Asistance Models API")

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

@app.get("/health")
def health():
    return {"status": "ok"}
