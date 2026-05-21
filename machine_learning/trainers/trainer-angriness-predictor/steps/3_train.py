import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

PROCESSED_DIR = os.path.join("data", "processed")
INPUT_CSV = os.path.join(PROCESSED_DIR, "features.csv")
MODEL_PATH = os.path.join("models", "model.pkl")
BINS_PATH = os.path.join("models", "angriness_bins.json")
METRICS_PATH = os.path.join("models", "metrics.json")

UNSCALED_CSV = os.path.join(PROCESSED_DIR, "raw_validated.csv")

PERCENTILE_EDGES = [0, 10, 35, 65, 90, 100]


def score_to_angriness(score: float, bin_edges: list[float]) -> int:
    for i in range(len(bin_edges) - 1):
        if score <= bin_edges[i + 1]:
            return 5 - i
    return 1


def main():
    print(f"Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Shape: {df.shape}")

    model = IsolationForest(
        contamination=0.03,
        n_estimators=200,
        max_features=0.75,
        random_state=42,
    )

    print("Training Isolation Forest...")
    model.fit(df.values)

    scores = model.decision_function(df.values)
    labels = model.predict(df.values)
    n_anomalies = (labels == -1).sum()
    print(f"  Anomalies: {n_anomalies} / {len(df)} ({n_anomalies / len(df):.1%})")

    bin_edges = [float(np.percentile(scores, p)) for p in PERCENTILE_EDGES]
    print(f"  Bin edges: {[round(e, 4) for e in bin_edges]}")

    angriness_levels = np.array([score_to_angriness(s, bin_edges) for s in scores])

    print(f"\n  Angriness distribution:")
    for level in range(1, 6):
        count = (angriness_levels == level).sum()
        print(f"    Level {level}: {count:,} rows ({count / len(df):.1%})")

    # Sanity check: compare angriness levels against unscaled features
    tilt_cols = ["acpl_player", "blunder_cnt_player", "consecutive_losses_pregame"]
    if os.path.exists(UNSCALED_CSV):
        raw = pd.read_csv(UNSCALED_CSV)
        available_tilt = [c for c in tilt_cols if c in raw.columns]
        if available_tilt and len(raw) == len(df):
            raw["_angriness"] = angriness_levels
            print(f"\n  Sanity check (unscaled means by angriness level):")
            grouped = raw.groupby("_angriness")[available_tilt].mean().round(1)
            print(grouped.to_string())

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n  Saved: {MODEL_PATH}")

    bins_data = {
        "percentiles": PERCENTILE_EDGES,
        "bin_edges": bin_edges,
    }
    with open(BINS_PATH, "w") as f:
        json.dump(bins_data, f, indent=2)
    print(f"  Saved: {BINS_PATH}")

    metrics = {
        "model_type": "Isolation Forest",
        "contamination": 0.03,
        "n_estimators": 200,
        "max_features": 0.75,
        "n_rows": len(df),
        "n_features": len(df.columns),
        "n_anomalies": int(n_anomalies),
        "anomaly_rate": round(n_anomalies / len(df), 4),
        "angriness_distribution": {
            str(level): int((angriness_levels == level).sum())
            for level in range(1, 6)
        },
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Saved: {METRICS_PATH}")

    print(f"\nTraining complete.")


if __name__ == "__main__":
    main()
