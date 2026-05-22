import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split

PROCESSED_DIR = os.path.join("data", "processed")
INPUT_CSV = os.path.join(PROCESSED_DIR, "features.csv")
MODEL_PATH = os.path.join("models", "model.pkl")
IF_MODEL_PATH = os.path.join("models", "if_model.pkl")
BINS_PATH = os.path.join("models", "angriness_bins.json")
METRICS_PATH = os.path.join("models", "metrics.json")

UNSCALED_CSV = os.path.join(PROCESSED_DIR, "raw_validated.csv")

TRAIN_FEATURES_CSV = os.path.join(PROCESSED_DIR, "features_train.csv")
VAL_FEATURES_CSV = os.path.join(PROCESSED_DIR, "features_val.csv")
TEST_FEATURES_CSV = os.path.join(PROCESSED_DIR, "features_test.csv")
TRAIN_RAW_CSV = os.path.join(PROCESSED_DIR, "raw_train.csv")
VAL_RAW_CSV = os.path.join(PROCESSED_DIR, "raw_val.csv")
TEST_RAW_CSV = os.path.join(PROCESSED_DIR, "raw_test.csv")

IF_FEATURES = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
]

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

    raw = pd.read_csv(UNSCALED_CSV) if os.path.exists(UNSCALED_CSV) else None

    indices = np.arange(len(df))
    trainval_idx, test_idx = train_test_split(indices, test_size=0.20, random_state=42)
    train_idx, val_idx = train_test_split(trainval_idx, test_size=0.20, random_state=42)

    df_train = df.iloc[train_idx].reset_index(drop=True)
    df_val = df.iloc[val_idx].reset_index(drop=True)
    df_test = df.iloc[test_idx].reset_index(drop=True)

    print(f"  Split: {len(df_train)} train / {len(df_val)} val / {len(df_test)} test "
          f"({len(df_train)/len(df):.0%}/{len(df_val)/len(df):.0%}/{len(df_test)/len(df):.0%})")

    raw_train = raw_val = raw_test = None
    if raw is not None and len(raw) == len(df):
        raw_train = raw.iloc[train_idx].reset_index(drop=True)
        raw_val = raw.iloc[val_idx].reset_index(drop=True)
        raw_test = raw.iloc[test_idx].reset_index(drop=True)

    df_train.to_csv(TRAIN_FEATURES_CSV, index=False)
    df_val.to_csv(VAL_FEATURES_CSV, index=False)
    df_test.to_csv(TEST_FEATURES_CSV, index=False)
    print(f"  Saved splits: features_{{train,val,test}}.csv")

    if raw_train is not None:
        raw_train.to_csv(TRAIN_RAW_CSV, index=False)
        raw_val.to_csv(VAL_RAW_CSV, index=False)
        raw_test.to_csv(TEST_RAW_CSV, index=False)
        print(f"  Saved splits: raw_{{train,val,test}}.csv")

    # --- Stage 1: Isolation Forest (label generation) ---
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
    n_anomalies = (if_model.predict(df_train[IF_FEATURES].values) == -1).sum()
    print(f"  Anomalies: {n_anomalies} / {len(df_train)} ({n_anomalies / len(df_train):.1%})")

    bin_edges = [float(np.percentile(scores_train, p)) for p in PERCENTILE_EDGES]
    print(f"  Bin edges: {[round(e, 4) for e in bin_edges]}")

    y_train = np.array([score_to_angriness(s, bin_edges) for s in scores_train])

    print(f"\n  Angriness distribution (train):")
    for level in range(1, 6):
        count = (y_train == level).sum()
        print(f"    Level {level}: {count:,} rows ({count / len(df_train):.1%})")

    # --- Stage 2: Random Forest Classifier (supervised, all features) ---
    all_features = list(df_train.columns)
    print(f"\nStage 2: Training Random Forest Classifier ({len(all_features)} features)...")

    rf_model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    rf_model.fit(df_train.values, y_train)

    rf_pred_train = rf_model.predict(df_train.values)
    rf_accuracy = (rf_pred_train == y_train).mean()
    print(f"  Train accuracy (vs IF labels): {rf_accuracy:.4f}")

    tilt_cols = ["acpl_player", "blunder_cnt_player", "consecutive_losses_pregame"]
    if raw_train is not None:
        available_tilt = [c for c in tilt_cols if c in raw_train.columns]
        if available_tilt:
            raw_train["_angriness"] = rf_pred_train
            print(f"\n  Sanity check (unscaled means by angriness level, train set):")
            grouped = raw_train.groupby("_angriness")[available_tilt].mean().round(1)
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
        "model_features": all_features,
        "model_type": "random_forest",
        "supervised": True,
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
        "n_rows": len(df),
        "n_rows_train": len(df_train),
        "n_if_features": len(IF_FEATURES),
        "n_rf_features": len(all_features),
        "n_anomalies": int(n_anomalies),
        "anomaly_rate": round(n_anomalies / len(df_train), 4),
        "rf_train_accuracy": round(float(rf_accuracy), 4),
        "angriness_distribution": {
            str(level): int((y_train == level).sum())
            for level in range(1, 6)
        },
        "split": {
            "method": "two_stage_80_20",
            "random_state": 42,
            "total_rows": len(df),
            "train_rows": len(df_train),
            "val_rows": len(df_val),
            "test_rows": len(df_test),
            "train_pct": round(len(df_train) / len(df), 4),
            "val_pct": round(len(df_val) / len(df), 4),
            "test_pct": round(len(df_test) / len(df), 4),
        },
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Saved: {METRICS_PATH}")

    print(f"\nTraining complete.")


if __name__ == "__main__":
    main()
