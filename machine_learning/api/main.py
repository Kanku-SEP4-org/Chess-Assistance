from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib, numpy as np, os
import pandas as pd

app = FastAPI(title="Chess Asistance Models API")

# Enable CORS for frontend access
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
    temperature_celsius: float = 20.0  # Default optimal temperature
    co2:  float = 400.0  # Default ambient CO2
    light:  float = 0.5  # Default light level

@app.post("/predict")
def predict(data: ChanceWinrateFeatures):
    """
    Predict chess win rate based on physical condition
    Takes: minutes_slept, minutes_awake, and optional environmental factors
    Returns: predictionWinrate (0-100)
    """
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
    
    # Convert to 0-100 scale for win percentage
    win_percentage = max(0, min(100, int(prediction * 100)))

    print(f"Input: sleep={data.minutes_slept}, awake={data.minutes_awake}, temp={data.temperature_celsius}, co2={data.co2}, light={data.light}")
    print(f"Model features: {model.feature_names_in_}")
    print(f"Prediction: {prediction}, Win %: {win_percentage}")
    
    return {
        "predictionWinrate": win_percentage,
        "prediction": prediction
    }


@app.get("/health")
def health():
    return {"status": "ok"}