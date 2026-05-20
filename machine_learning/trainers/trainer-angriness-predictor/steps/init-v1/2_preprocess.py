"""
Step 2: Preprocessing and feature engineering for the Angriness Predictor.

Drops identifiers/timestamps, encodes categoricals, handles nulls,
scales numeric features, and saves the processed dataset.

Run from trainer-angriness-predictor/:
    python steps/init/2_preprocess.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
LEGACY_DIR = ROOT / "data" / "legacy"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

DIVERSE_CSV = RAW_DIR / "angriness_dataset_diverse.csv"
ORIGINAL_CSV = LEGACY_DIR / "angriness_dataset.csv"
CSV_PATH = DIVERSE_CSV if DIVERSE_CSV.exists() else ORIGINAL_CSV

DROP_COLS = ["game_id", "username", "created_at", "last_move_at"]

# consecutive_losses and consecutive_losses_pregame are identical;
# avg_tpm and avg_tpm_seconds_player are near-identical (different denominators).
# Keep the player-specific versions.
REDUNDANT_COLS = ["consecutive_losses", "avg_tpm"]

TILT_BEHAVIORAL = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
]

TILT_CONTEXT = [
    "elo",
    "elo_diff",
    "opponent_elo",
    "elo_gap",
    "time_control_initial",
    "time_control_increment",
    "move_cnt",
    "move_cnt_player",
]

TILT_PHYSIOLOGICAL = [
    "sleep_duration",
    "awaken_duration",
    "avg_ppm",
    "avg_celsius",
    "water_intake_ml",
    "avg_lux",
]

CATEGORICAL_COLS = ["player_color"]


def main():
    print(f"Loading: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Raw shape: {df.shape}")

    # --- Drop identifiers and redundant columns ---
    to_drop = [c for c in DROP_COLS + REDUNDANT_COLS if c in df.columns]
    df.drop(columns=to_drop, inplace=True)
    print(f"After dropping identifiers/redundant: {df.shape}")

    # --- Encode player_color (white=0, black=1) ---
    if "player_color" in df.columns:
        df["is_black"] = (df["player_color"] == "black").astype(int)
        df.drop(columns=["player_color"], inplace=True)

    # --- Handle nulls ---
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if len(null_cols) > 0:
        print(f"\nNull columns before fill:\n{null_cols.to_string()}")
        for col in null_cols.index:
            if df[col].dtype in [np.float64, np.int64, float, int]:
                df[col].fillna(df[col].median(), inplace=True)
            else:
                df[col].fillna(0, inplace=True)

    print(f"Nulls after fill: {df.isnull().sum().sum()}")

    # --- Save unscaled (for inspection) ---
    df.to_csv(OUTPUT_DIR / "features_unscaled.csv", index=False)
    print(f"Saved: {OUTPUT_DIR / 'features_unscaled.csv'}")

    # --- Scale numeric features ---
    all_features = TILT_BEHAVIORAL + TILT_CONTEXT + TILT_PHYSIOLOGICAL + ["is_black"]
    available = [c for c in all_features if c in df.columns]
    missing = [c for c in all_features if c not in df.columns]
    if missing:
        print(f"Warning: missing features: {missing}")

    df_features = df[available].copy()

    numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
    scaler = StandardScaler()
    df_features[numeric_cols] = scaler.fit_transform(df_features[numeric_cols])

    df_features.to_csv(OUTPUT_DIR / "features_scaled.csv", index=False)
    print(f"Saved: {OUTPUT_DIR / 'features_scaled.csv'}")

    # --- Summary ---
    print(f"\nFinal feature set ({len(available)} features):")
    print(f"  Behavioral:    {[c for c in TILT_BEHAVIORAL if c in available]}")
    print(f"  Context:       {[c for c in TILT_CONTEXT if c in available]}")
    print(f"  Physiological: {[c for c in TILT_PHYSIOLOGICAL if c in available]}")
    print(f"  Categorical:   ['is_black']")
    print(f"  Total rows: {len(df_features)}")

    print("\nPreprocessing complete.")


if __name__ == "__main__":
    main()
