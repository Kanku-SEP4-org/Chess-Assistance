import os

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = os.path.join("data", "processed")
INPUT_CSV = os.path.join(PROCESSED_DIR, "raw_validated.csv")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "features.csv")
RAW_CLEANED_CSV = os.path.join(PROCESSED_DIR, "raw_cleaned.csv")
SCALER_PATH = os.path.join("models", "scaler.pkl")

FEATURE_ORDER = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "mistake_cnt_player",
    "inaccuracy_cnt_player",
    "acpl_player",
    "accuracy_player",
    "elo",
]

IQR_MULTIPLIER = 1.5


def remove_outliers_iqr(df, columns, multiplier=IQR_MULTIPLIER):
    mask = pd.Series(True, index=df.index)
    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            upper = df[col].quantile(0.99)
            if upper == 0:
                print(f"    {col}: IQR=0, P99=0 — skipped")
                continue
            col_mask = df[col] <= upper
            flagged = (~col_mask).sum()
            print(f"    {col}: IQR=0, fallback P99 upper={upper:.2f} — {flagged} outliers")
            mask &= col_mask
            continue
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        col_mask = (df[col] >= lower) & (df[col] <= upper)
        flagged = (~col_mask).sum()
        print(f"    {col}: [{lower:.2f}, {upper:.2f}] — {flagged} outliers")
        mask &= col_mask
    return mask


def main():
    print(f"Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Shape: {df.shape}")

    available = [c for c in FEATURE_ORDER if c in df.columns]
    missing = [c for c in FEATURE_ORDER if c not in df.columns]
    if missing:
        print(f"  Warning: missing features: {missing}")

    df_features = df[available].copy()

    for col in df_features.columns:
        if df_features[col].isnull().any():
            df_features[col] = df_features[col].fillna(df_features[col].median())

    print(f"\n  Outlier removal (IQR × {IQR_MULTIPLIER}):")
    keep_mask = remove_outliers_iqr(df_features, available)
    n_removed = (~keep_mask).sum()
    print(f"  Total: {n_removed} rows removed ({n_removed / len(df):.1%}), "
          f"{keep_mask.sum()} rows kept")

    df_features = df_features.loc[keep_mask].reset_index(drop=True)
    df_cleaned = df.loc[keep_mask].reset_index(drop=True)

    scaler = StandardScaler()
    df_features[available] = scaler.fit_transform(df_features[available])

    os.makedirs("models", exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)

    df_features.to_csv(OUTPUT_CSV, index=False)
    df_cleaned.to_csv(RAW_CLEANED_CSV, index=False)
    print(f"  Saved: {OUTPUT_CSV} ({len(df_features)} rows, {len(available)} features)")
    print(f"  Saved: {RAW_CLEANED_CSV} ({len(df_cleaned)} rows, all columns)")
    print(f"  Saved: {SCALER_PATH}")
    print(f"  Features: {available}")


if __name__ == "__main__":
    main()
