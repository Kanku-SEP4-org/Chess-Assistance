FROM python:3.11-slim AS builder

WORKDIR /build

COPY machine_learning/trainers/trainer-winrate/requirements.txt /tmp/winrate-req.txt
COPY machine_learning/trainers/trainer-angriness-predictor/requirements.txt /tmp/angriness-req.txt
COPY machine_learning/trainers/trainer-ap/requirements.txt /tmp/ap-req.txt
COPY machine_learning/trainers/trainer-factor-imp/requirements.txt /tmp/factor-imp-req.txt
COPY machine_learning/api/requirements.txt /tmp/api-req.txt
RUN pip install --no-cache-dir \
    -r /tmp/winrate-req.txt \
    -r /tmp/angriness-req.txt \
    -r /tmp/ap-req.txt \
    -r /tmp/factor-imp-req.txt \
    -r /tmp/api-req.txt \
    fastapi

COPY machine_learning/trainers/trainer-winrate/ /build/trainer-winrate/
WORKDIR /build/trainer-winrate
RUN python run_pipeline.py

COPY machine_learning/trainers/trainer-angriness-predictor/ /build/trainer-angriness/
WORKDIR /build/trainer-angriness
RUN python run_pipeline.py

COPY machine_learning/trainers/trainer-ap/ /build/trainer-ap/
WORKDIR /build/trainer-ap
RUN python run_pipeline.py

COPY machine_learning/trainers/trainer-factor-imp/ /build/trainer-factor-imp/
WORKDIR /build/trainer-factor-imp
RUN python run_pipeline.py

FROM python:3.11-slim

WORKDIR /app

COPY machine_learning/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi

COPY machine_learning/api/main.py .

COPY --from=builder /build/trainer-winrate/models/ /app/models/
COPY --from=builder /build/trainer-angriness/models/ /app/angriness_models/
COPY --from=builder /build/trainer-ap/models/model_pipeline.pkl /app/ap_models/model_pipeline.pkl
COPY machine_learning/trainers/trainer-ap/data/eco_frequency_map.json /app/ap_models/eco_frequency_map.json
COPY --from=builder /build/trainer-factor-imp/models/ /app/factor_impact_models/

ENV MODEL_PATH=/app/models/model.pkl
ENV ANGRINESS_MODEL_PATH=/app/angriness_models/model.pkl
ENV ANGRINESS_SCALER_PATH=/app/angriness_models/scaler.pkl
ENV ANGRINESS_BINS_PATH=/app/angriness_models/angriness_bins.json
ENV AP_PIPELINE_PATH=/app/ap_models/model_pipeline.pkl
ENV AP_ECO_MAP_PATH=/app/ap_models/eco_frequency_map.json
ENV FACTOR_IMPACT_REPORT_PATH=/app/factor_impact_models/factor_impact_report.json
ENV FACTOR_IMPACT_COMPARISON_PATH=/app/factor_impact_models/model_comparison.json
ENV FACTOR_IMPACT_VALIDATION_PATH=/app/factor_impact_models/factor_impact_validation.json

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
