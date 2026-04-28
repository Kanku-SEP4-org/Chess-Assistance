# Connection Implementation Summary

## Changes Made

### 1. ✅ ML API (`machine_learning/api/main.py`)
- **Added CORS support** - allows requests from frontend
- **Updated ChanceWinrateFeatures model** - environmental factors now have default values:
  - `temperature_celsius: float = 20.0` (optimal)
  - `co2: float = 400.0` (ambient)
  - `light: float = 0.5` (default)
- **Updated `/predict` endpoint** - returns win percentage (0-100):
  ```json
  {
    "predictionWinrate": 72,
    "prediction": 0.72
  }
  ```
- **Improved logging** - shows input values and prediction results

### 2. ✅ gRPC Service (`services/grpc-service/server.js`)
- **Updated `PredictWinrate` function** - now calls ML API instead of using dummy formula
- **Converts gRPC request to HTTP** - sends sleep/awake data to ML API on port 8000
- **Handles errors gracefully** - returns proper gRPC error codes on failure
- **Returns win prediction** - in gRPC format matching proto definition:
  ```
  predictionWinrate: 72
  isActive: true
  message: "Good condition for chess"
  ```

### 3. ✅ API Gateway (`api-gateway/server.js`)
- **No changes needed** - already correctly routes:
  - `POST /model/winrate/predict` → gRPC service at :50051
  - `GET /iot/temp` → sensor service at :50051

### 4. ✅ React Frontend (`frontend/chessapp/src/App.jsx`)
- **No changes needed** - already correctly:
  - Sends sleep duration and time awake
  - Fetches temperature data
  - Displays results with `predictionWinrate` and temperature

## Data Flow Verification

### Request Path
```
User Input (React)
  → POST /model/winrate/predict
    → API Gateway (port 3001)
      → gRPC call to WinrateService (port 50051)
        → HTTP POST to ML API (port 8000)
          → Returns prediction (0-100)
```

### Response Path
```
ML API Response
  → gRPC Service (port 50051)
    → API Gateway (port 3001)
      → React Frontend (port 3000)
        → Display: "Win Rate: X%"
```

## Required Services to Run (in order)

1. **ML Trainer** (one-time): `python run_pipeline.py` in `machine_learning/trainer/`
2. **ML API**: `uvicorn main:app --reload` in `machine_learning/api/` (port 8000)
3. **gRPC Service**: `node server.js` in `services/grpc-service/` (port 50051)
4. **API Gateway**: `node server.js` in `api-gateway/` (port 3001)
5. **React Frontend**: `npm start` in `frontend/chessapp/` (port 3000)

## Input/Output Examples

### Frontend sends:
```json
{
  "condition": {
    "minutes_slept": 480,
    "minutes_awake": 60
  }
}
```

### ML API processes:
- Receives 2 values (sleep, awake)
- Uses defaults for environment (temp=20°C, co2=400ppm, light=0.5)
- Calculates environment score
- Applies ML model
- Returns: `{"predictionWinrate": 72, ...}`

### Frontend displays:
```
Win Rate: 72%
Temperature: 24 °C
```

## Key Features

✅ **Automatic default values** - ML API works with just sleep/awake times
✅ **CORS enabled** - Frontend can communicate with API
✅ **Proper error handling** - Errors are logged and returned gracefully
✅ **Win percentage scaling** - Raw prediction converted to 0-100 scale
✅ **Mock mode available** - Frontend has mock mode for testing without servers

## Testing Checklist

- [ ] Run ML trainer pipeline
- [ ] Start ML API on port 8000
- [ ] Start gRPC service on port 50051
- [ ] Start API Gateway on port 3001
- [ ] Start React app on port 3000
- [ ] Enter sleep (480 min) and awake (60 min) times
- [ ] Verify win rate prediction displays (0-100)
- [ ] Verify temperature displays if Arduino ID provided
- [ ] Check browser console for any errors
- [ ] Check terminal logs for prediction details

## Notes

- Environmental factors use optimal defaults (no sensor data integration yet)
- Win percentage is rounded to integer (0-100)
- All services use localhost/127.0.0.1
- Modify ports in respective server.js and FastAPI files if needed
