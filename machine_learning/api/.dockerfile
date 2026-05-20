FROM python:3.11-slim

WORKDIR /app

COPY machine_learning/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi

COPY machine_learning/api/main.py .
COPY machine_learning/trainers/trainer-winrate/models/ /app/models/
COPY machine_learning/trainers/trainer-angriness-predictor/models/ /app/angriness_models/

ENV MODEL_PATH=/app/models/model.pkl
ENV ANGRINESS_MODEL_PATH=/app/angriness_models/model.pkl
ENV ANGRINESS_SCALER_PATH=/app/angriness_models/scaler.pkl
ENV ANGRINESS_BINS_PATH=/app/angriness_models/angriness_bins.json

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
