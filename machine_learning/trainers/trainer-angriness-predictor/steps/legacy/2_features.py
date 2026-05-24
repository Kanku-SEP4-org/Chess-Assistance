import os

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = os.path.join("data", "processed")
INPUT_CSV = os.path.join(PROCESSED_DIR, "raw_validated.csv")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "features.csv")
SCALER_PATH = os.path.join("models", "scaler.pkl")

DROP_IDENTIFIERS = ["game_id", "username", "created_at", "last_move_at"]
DROP_REDUNDANT = ["consecutive_losses", "avg_tpm"]

FEATURE_ORDER = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
    "elo",
    "elo_diff",
    "opponent_elo",
    "elo_gap",
    "time_control_initial",
    "time_control_increment",
    "move_cnt",
    "move_cnt_player",
    "sleep_duration",
    "awaken_duration",
    "avg_ppm",
    "avg_celsius",
    "water_intake_ml",
    "avg_lux",
    "is_black",
]


def main():
    print(f"Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Shape: {df.shape}")

    to_drop = [c for c in DROP_IDENTIFIERS + DROP_REDUNDANT if c in df.columns]
    df.drop(columns=to_drop, inplace=True)

    if "player_color" in df.columns:
        df["is_black"] = (df["player_color"] == "black").astype(int)
        df.drop(columns=["player_color"], inplace=True)

    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    available = [c for c in FEATURE_ORDER if c in df.columns]
    missing = [c for c in FEATURE_ORDER if c not in df.columns]
    if missing:
        print(f"  Warning: missing features: {missing}")

    df_features = df[available].copy()

    scaler = StandardScaler()
    df_features[available] = scaler.fit_transform(df_features[available])

    os.makedirs("models", exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)

    df_features.to_csv(OUTPUT_CSV, index=False)
    print(f"  Saved: {OUTPUT_CSV} ({len(df_features)} rows, {len(available)} features)")
    print(f"  Saved: {SCALER_PATH}")
    print(f"  Features: {available}")


if __name__ == "__main__":
    main()
