# IoT Server to React App Connection Guide

This document describes the complete data flow from the React frontend through the IoT server to get chess win rate predictions.

## Architecture Overview

```
Frontend (React)
    ↓ POST /model/winrate/predict
    ↓ GET /iot/temp
    ↓
API Gateway (Node.js:3001)
    ↓ gRPC call
    ↓
gRPC Service (Node.js:50051)
    ↓ HTTP POST
    ↓
ML API (FastAPI:8000)
    ↓
Returns prediction (0-100)
```

## Setup Instructions

### 1. Start the ML Trainer (one-time only)

```bash
cd machine_learning/trainer
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python run_pipeline.py
```

This creates `models/model.pkl` and `models/scaler.pkl` required by the API.

### 2. Start the ML API Server

```bash
cd machine_learning/api
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Server runs on: `http://localhost:8000`
Health check: `http://localhost:8000/health`

### 3. Start the gRPC Service

```bash
cd services/grpc-service
npm install  # if not already installed
node server.js
```

Server runs on: `localhost:50051`
- `PredictWinrate` - calls ML API with sleep/awake data
- `GetTemperature` - returns mock temperature data

### 4. Start the API Gateway

```bash
cd api-gateway
npm install  # if not already installed
node server.js
```

Server runs on: `http://localhost:3001`
Endpoints:
- `POST /model/winrate/predict` - prediction endpoint
- `GET /iot/temp?id={deviceId}` - temperature endpoint

### 5. Start the React Frontend

```bash
cd frontend/chessapp
npm install  # if not already installed
npm run dev
```

Frontend runs on: `http://localhost:5173`

## Data Flow

### Request Flow
1. User enters sleep duration (minutes) and time awake (minutes)
2. Frontend sends POST request to `http://localhost:3001/model/winrate/predict`
3. Request body:
   ```json
   {
     "condition": {
       "minutes_slept": 480,
       "minutes_awake": 60
     }
   }
   ```

### API Gateway Processing
- Receives request and forwards to gRPC service at `localhost:50051`
- Uses protobuf message: `WinratePredictionInput` with `PhysicalCondition`

### gRPC Service Processing
- Converts gRPC request to HTTP POST to ML API
- Calls `http://localhost:8000/predict` with:
  ```json
  {
    "minutes_slept": 480,
    "minutes_awake": 60,
    "temperature_celsius": 20,
    "co2": 400,
    "light": 0.5
  }
  ```
- Note: Environmental factors use default values (optimal)

### ML API Processing
- Receives prediction request
- Calculates environmental score based on temperature, CO2, light
- Applies ML model to predict win rate
- Returns prediction as 0-100 percentage:
  ```json
  {
    "predictionWinrate": 72,
    "prediction": 0.72
  }
  ```

### Response Flow
1. gRPC service receives prediction from ML API
2. Returns gRPC response:
   ```
   predictionWinrate: 72
   isActive: true
   message: "Good condition for chess"
   ```
3. API Gateway forwards response to frontend
4. Frontend displays: "Win Rate: 72%"

### Temperature Data (Optional)
- Frontend also fetches temperature from `GET /iot/temp?id={arduinoId}`
- Displays: "Temperature: 24 °C"

## ML Model Features

The model takes 4 features:
1. **minutes_slept** - Sleep duration
2. **minutes_awake** - Time awake before match
3. **env_score** - Environmental quality (0-1)
   - Based on temperature (optimal: 20°C)
   - Based on CO2 levels (optimal: 400 ppm)
   - Weighted: 70% CO2, 30% temperature
4. **light** - Light level (0-1)

## Troubleshooting

### "Failed to fetch data" error
- Check that ML API is running on port 8000
- Check that gRPC service is running on port 50051
- Check that API Gateway is running on port 3001
- Check browser console for detailed error

### Model not found error
- Ensure you ran the trainer pipeline first
- Check that `models/model.pkl` exists in `machine_learning/trainer/models/`

### gRPC connection refused
- Ensure gRPC service is running: `node services/grpc-service/server.js`
- Check that port 50051 is not blocked

### CORS errors
- ML API has CORS enabled for all origins
- API Gateway has CORS enabled
- Check that all services are running on expected ports

## Testing with Mock Data

In the React app, you can enable "Mock Mode" to test without running all services:
- Uses hardcoded prediction: 72%
- Uses hardcoded temperature: 24°C
- No server calls needed

## Environment Variables

### ML API (uvicorn)
- Default port: 8000
- To change: `uvicorn main:app --host 0.0.0.0 --port 5000`

### API Gateway
- Default port: 3001
- To change: Edit `api-gateway/server.js`

### gRPC Service
- Default port: 50051
- Default host: 127.0.0.1
- To change: Edit `services/grpc-service/server.js`

### React Frontend
- Default port: 5173
- To change: `Edit vite.config.js` or run: `VITE_PORT=3001 npm run dev`
