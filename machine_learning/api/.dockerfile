FROM python:3.11-slim AS builder

WORKDIR /build

COPY machine_learning/trainers/trainer-winrate/requirements.txt /tmp/winrate-req.txt
COPY machine_learning/trainers/trainer-angriness-predictor/requirements.txt /tmp/angriness-req.txt
COPY machine_learning/api/requirements.txt /tmp/api-req.txt
RUN pip install --no-cache-dir -r /tmp/winrate-req.txt -r /tmp/angriness-req.txt -r /tmp/api-req.txt fastapi

COPY machine_learning/trainers/trainer-winrate/ /build/trainer-winrate/
WORKDIR /build/trainer-winrate
RUN python run_pipeline.py

COPY machine_learning/trainers/trainer-angriness-predictor/ /build/trainer-angriness/
WORKDIR /build/trainer-angriness
RUN python run_pipeline.py

FROM python:3.11-slim

WORKDIR /app

COPY machine_learning/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi

COPY machine_learning/api/main.py .
COPY --from=builder /build/trainer-winrate/models/ /app/models/
COPY --from=builder /build/trainer-angriness/models/ /app/angriness_models/

ENV MODEL_PATH=/app/models/model.pkl
ENV ANGRINESS_MODEL_PATH=/app/angriness_models/model.pkl
ENV ANGRINESS_SCALER_PATH=/app/angriness_models/scaler.pkl
ENV ANGRINESS_BINS_PATH=/app/angriness_models/angriness_bins.json

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
