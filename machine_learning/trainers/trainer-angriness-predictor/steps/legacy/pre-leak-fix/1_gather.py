import os
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LEGACY_DIR = Path("data/legacy")

DIVERSE_CSV = RAW_DIR / "angriness_dataset_diverse.csv"
ORIGINAL_CSV = LEGACY_DIR / "angriness_dataset.csv"
OUTPUT_CSV = PROCESSED_DIR / "raw_validated.csv"

REQUIRED_COLUMNS = [
    "sleep_duration", "consecutive_losses", "awaken_duration", "avg_tpm",
    "move_cnt", "inaccuracy_cnt_player", "mistake_cnt_player",
    "blunder_cnt_player", "elo", "elo_diff", "game_id", "username",
    "created_at", "last_move_at", "player_color", "time_control_initial",
    "time_control_increment", "opponent_elo", "elo_gap", "move_cnt_player",
    "avg_tpm_seconds_player", "consecutive_losses_pregame", "acpl_player",
    "accuracy_player", "avg_ppm", "avg_celsius", "water_intake_ml", "avg_lux",
]

ANALYSIS_COLUMNS = [
    "acpl_player", "blunder_cnt_player", "mistake_cnt_player",
    "inaccuracy_cnt_player",
]


def main():
    csv_path = DIVERSE_CSV if DIVERSE_CSV.exists() else ORIGINAL_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"No dataset found. Expected {DIVERSE_CSV} or {ORIGINAL_CSV}")

    print(f"Loading: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"  Raw shape: {df.shape}")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    before = len(df)
    df = df.dropna(subset=ANALYSIS_COLUMNS)
    dropped = before - len(df)
    if dropped > 0:
        print(f"  Dropped {dropped} rows with null analysis -> {len(df)} remaining")

    bins = [0, 1200, 1600, 2000, 2400, 5000]
    labels = ["800-1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]
    brackets = pd.cut(df["elo"], bins=bins, labels=labels)
    print(f"\n  ELO distribution:")
    print(brackets.value_counts().sort_index().to_string())

    nulls = df[REQUIRED_COLUMNS].isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls) > 0:
        print(f"\n  Remaining nulls:\n{nulls.to_string()}")
    else:
        print(f"\n  Nulls: none")

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Saved: {OUTPUT_CSV} ({len(df)} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()
