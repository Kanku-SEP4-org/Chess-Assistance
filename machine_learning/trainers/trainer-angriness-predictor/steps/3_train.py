"""
Step 3 — Semi-supervised training (Isolation Forest -> Random Forest surrogate).

The train/val/test split and all preprocessing now happen in 2_features.py, so this
step just consumes the train split. Stage 1 fits an Isolation Forest on the scaled
train features and turns its anomaly scores into 5 angriness levels by percentile.
Stage 2 trains a Random Forest on the unscaled train features to reproduce those
labels (a fast surrogate that does not need the IF at inference).
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier

PROCESSED_DIR = os.path.join("data", "processed")
FEATURES_TRAIN_CSV = os.path.join(PROCESSED_DIR, "features_train.csv")
FEATURES_VAL_CSV = os.path.join(PROCESSED_DIR, "features_val.csv")
FEATURES_TEST_CSV = os.path.join(PROCESSED_DIR, "features_test.csv")
RAW_TRAIN_CSV = os.path.join(PROCESSED_DIR, "raw_train.csv")

MODEL_PATH = os.path.join("models", "model.pkl")
IF_MODEL_PATH = os.path.join("models", "if_model.pkl")
BINS_PATH = os.path.join("models", "angriness_bins.json")
METRICS_PATH = os.path.join("models", "metrics.json")

IF_FEATURES = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
    "elo",
]

PERCENTILE_EDGES = [0, 10, 35, 65, 90, 100]


def score_to_angriness(score: float, bin_edges: list[float]) -> int:
    for i in range(len(bin_edges) - 1):
        if score <= bin_edges[i + 1]:
            return 5 - i
    return 1


def _row_count(path: str) -> int:
    return len(pd.read_csv(path)) if os.path.exists(path) else 0


def main():
    for path in (FEATURES_TRAIN_CSV, RAW_TRAIN_CSV):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing split artifact: {path}. Run 2_features.py first.")

    print(f"Loading train splits:\n  {FEATURES_TRAIN_CSV}\n  {RAW_TRAIN_CSV}")
    df_train = pd.read_csv(FEATURES_TRAIN_CSV)   # scaled features (IF input)
    raw_train = pd.read_csv(RAW_TRAIN_CSV)        # unscaled features (RF input)
    n_train, n_val, n_test = (
        len(df_train), _row_count(FEATURES_VAL_CSV), _row_count(FEATURES_TEST_CSV)
    )
    n_total = n_train + n_val + n_test
    print(f"  Train rows: {n_train}  (val {n_val} / test {n_test} held out by 2_features.py)")

    # --- Stage 1: Isolation Forest (label generation on scaled train features) ---
    print(f"\n  IF features ({len(IF_FEATURES)}): {IF_FEATURES}")
    if_model = IsolationForest(
        contamination=0.03,
        n_estimators=200,
        max_features=0.75,
        random_state=42,
    )

    print("Stage 1: Training Isolation Forest (label generation)...")
    if_model.fit(df_train[IF_FEATURES].values)

    scores_train = if_model.decision_function(df_train[IF_FEATURES].values)
    n_anomalies = int((if_model.predict(df_train[IF_FEATURES].values) == -1).sum())
    print(f"  Anomalies: {n_anomalies} / {len(df_train)} ({n_anomalies / len(df_train):.1%})")

    bin_edges = [float(np.percentile(scores_train, p)) for p in PERCENTILE_EDGES]
    print(f"  Bin edges: {[round(e, 4) for e in bin_edges]}")

    y_train = np.array([score_to_angriness(s, bin_edges) for s in scores_train])

    print("\n  Angriness distribution (train):")
    for level in range(1, 6):
        count = int((y_train == level).sum())
        print(f"    Level {level}: {count:,} rows ({count / len(df_train):.1%})")

    # --- Stage 2: Random Forest Classifier (unscaled behavioral features) ---
    print(f"\nStage 2: Training Random Forest Classifier ({len(IF_FEATURES)} unscaled features)...")
    rf_model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        max_depth=9,
        min_samples_leaf=9,
        max_features="sqrt",
        min_samples_split=10,
        n_jobs=-1,
    )
    rf_model.fit(raw_train[IF_FEATURES].values, y_train)

    rf_pred_train = rf_model.predict(raw_train[IF_FEATURES].values)
    rf_accuracy = float((rf_pred_train == y_train).mean())
    print(f"  Train accuracy (vs IF labels): {rf_accuracy:.4f}")

    tilt_cols = ["acpl_player", "blunder_cnt_player", "consecutive_losses_pregame"]
    available_tilt = [c for c in tilt_cols if c in raw_train.columns]
    if available_tilt:
        raw_train_copy = raw_train.copy()
        raw_train_copy["_angriness"] = rf_pred_train
        print("\n  Sanity check (unscaled means by angriness level, train set):")
        grouped = raw_train_copy.groupby("_angriness")[available_tilt].mean().round(1)
        print(grouped.to_string())

    os.makedirs("models", exist_ok=True)
    joblib.dump(rf_model, MODEL_PATH)
    print(f"\n  Saved: {MODEL_PATH} (Random Forest)")
    joblib.dump(if_model, IF_MODEL_PATH)
    print(f"  Saved: {IF_MODEL_PATH} (Isolation Forest)")

    bins_data = {
        "percentiles": PERCENTILE_EDGES,
        "bin_edges": bin_edges,
        "if_features": IF_FEATURES,
        "model_features": IF_FEATURES,
        "model_type": "random_forest",
        "supervised": True,
        "requires_scaling": False,
    }
    with open(BINS_PATH, "w") as f:
        json.dump(bins_data, f, indent=2)
    print(f"  Saved: {BINS_PATH}")

    metrics = {
        "model_type": "Semi-Supervised (IF + Random Forest)",
        "if_contamination": 0.03,
        "if_n_estimators": 200,
        "if_max_features": 0.75,
        "rf_n_estimators": 200,
        "rf_max_depth": 9,
        "rf_min_samples_leaf": 9,
        "rf_max_features": "sqrt",
        "rf_min_samples_split": 10,
        "n_rows": n_total,
        "n_rows_train": n_train,
        "n_if_features": len(IF_FEATURES),
        "n_rf_features": len(IF_FEATURES),
        "n_anomalies": n_anomalies,
        "anomaly_rate": round(n_anomalies / len(df_train), 4),
        "rf_train_accuracy": round(rf_accuracy, 4),
        "angriness_distribution": {
            str(level): int((y_train == level).sum()) for level in range(1, 6)
        },
        "split": {
            "method": "two_stage_80_20 (performed in 2_features.py, leak-free)",
            "random_state": 42,
            "total_rows": n_total,
            "train_rows": n_train,
            "val_rows": n_val,
            "test_rows": n_test,
            "train_pct": round(n_train / n_total, 4) if n_total else None,
            "val_pct": round(n_val / n_total, 4) if n_total else None,
            "test_pct": round(n_test / n_total, 4) if n_total else None,
        },
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Saved: {METRICS_PATH}")
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
