from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib, numpy as np, os
import pandas as pd

app = FastAPI(title="Chess Asistance Models API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    #compute env_score
    temp_dist = abs(data.temperature_celsius - 20)
    co2_norm = (data.co2 - 400) / 1600
    env_score = 1 - (co2_norm * 0.7 + (temp_dist / 5)* 0.3)

    X = pd.DataFrame([[
    data.minutes_slept,
    data.minutes_awake,
    env_score,
    data.light
    ]], columns=['minutes_slept','minutes_awake', 'env_score','light'])
    X_scaled = pd.DataFrame(
        scaler.transform(X),
        columns=X.columns
    )
    prediction = model.predict(X_scaled)[0]

    print(model.feature_names_in_)
    print(X_scaled)
    print(scaler.feature_names_in_)
    return {
        "prediction": prediction
    }

@app.get("/health")
def health():
    return {"status": "ok"}