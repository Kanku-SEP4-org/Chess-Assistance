from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, numpy as np, os

app = FastAPI(title="Chess Asistance Models API")

MODEL_PATH  = "../trainer/models/model.pkl"
SCALER_PATH = "../trainer/models/scaler.pkl"

if not os.path.exists(MODEL_PATH):
    raise RuntimeError("model.pkl not found in /models/")

model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

class ChanceWinrateFeatures(BaseModel):
    minutes_slept: float
    minutes_awake:  float
    temperature_celsius: float
    co2:  float
    light:  float

@app.post("/predict")
def predict(data: ChanceWinrateFeatures):
    X = np.array([[
        data.minutes_slept, data.minutes_awake,
        data.temperature, data.co2
    ]])
    X_scaled = scaler.transform(X)
    proba = model.predict_proba(X_scaled)[0]
    return {
        "Chance": 100
    }

@app.get("/health")
def health():
    return {"status": "ok"}