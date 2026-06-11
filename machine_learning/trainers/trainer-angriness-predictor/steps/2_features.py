"""
Step 2 — Split first, then fit all transforms on TRAIN only (leak-free).

Previously this step imputed, computed IQR outlier bounds, and fit the
StandardScaler on the FULL dataset, and the train/val/test split happened later
in 3_train.py. That leaked val/test statistics into preprocessing. This version
splits first (the same two-stage 64/16/20 scheme that used to live in 3_train.py),
then fits median-imputation, IQR bounds and the scaler on the train split only and
applies them to val/test. Outliers are removed from train only — val/test are kept
intact (you never drop evaluation rows).
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = os.path.join("data", "processed")
INPUT_CSV = os.path.join(PROCESSED_DIR, "raw_validated.csv")
RAW_CLEANED_CSV = os.path.join(PROCESSED_DIR, "raw_cleaned.csv")
SCALER_PATH = os.path.join("models", "scaler.pkl")

FEATURES_TRAIN_CSV = os.path.join(PROCESSED_DIR, "features_train.csv")
FEATURES_VAL_CSV = os.path.join(PROCESSED_DIR, "features_val.csv")
FEATURES_TEST_CSV = os.path.join(PROCESSED_DIR, "features_test.csv")
RAW_TRAIN_CSV = os.path.join(PROCESSED_DIR, "raw_train.csv")
RAW_VAL_CSV = os.path.join(PROCESSED_DIR, "raw_val.csv")
RAW_TEST_CSV = os.path.join(PROCESSED_DIR, "raw_test.csv")

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


def compute_iqr_bounds(df, columns, multiplier=IQR_MULTIPLIER):
    """Compute (lower, upper) outlier bounds per column from TRAIN data only."""
    bounds = {}
    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            upper = df[col].quantile(0.99)
            bounds[col] = (None, upper if upper != 0 else None)
            print(f"    {col}: IQR=0, fallback P99 upper={bounds[col][1]}")
        else:
            bounds[col] = (q1 - multiplier * iqr, q3 + multiplier * iqr)
            print(f"    {col}: [{bounds[col][0]:.2f}, {bounds[col][1]:.2f}]")
    return bounds


def outlier_keep_mask(df, bounds):
    """Boolean mask of rows within the train-derived bounds (any-feature rule)."""
    mask = pd.Series(True, index=df.index)
    for col, (lower, upper) in bounds.items():
        if upper is None:
            continue
        if lower is None:
            mask &= df[col] <= upper
        else:
            mask &= (df[col] >= lower) & (df[col] <= upper)
    return mask


def main():
    print(f"Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Shape: {df.shape}")

    available = [c for c in FEATURE_ORDER if c in df.columns]
    missing = [c for c in FEATURE_ORDER if c not in df.columns]
    if missing:
        print(f"  Warning: missing features: {missing}")

    # --- Split FIRST (two-stage 64/16/20), before fitting anything ---
    indices = np.arange(len(df))
    trainval_idx, test_idx = train_test_split(indices, test_size=0.20, random_state=42)
    train_idx, val_idx = train_test_split(trainval_idx, test_size=0.20, random_state=42)
    print(f"\n  Split: {len(train_idx)} train / {len(val_idx)} val / {len(test_idx)} test "
          f"({len(train_idx)/len(df):.0%}/{len(val_idx)/len(df):.0%}/{len(test_idx)/len(df):.0%})")

    # --- Fit imputation medians + IQR bounds + scaler on TRAIN ONLY ---
    train_feat = df.iloc[train_idx][available].copy()
    medians = train_feat.median()
    train_feat = train_feat.fillna(medians)

    print(f"\n  Outlier bounds (IQR x {IQR_MULTIPLIER}, train only):")
    bounds = compute_iqr_bounds(train_feat, available)

    keep_train = outlier_keep_mask(train_feat, bounds)
    n_removed = int((~keep_train).sum())
    print(f"  Train outliers removed: {n_removed} ({n_removed/len(train_feat):.1%}), "
          f"{int(keep_train.sum())} kept. Val/test kept intact.")

    scaler = StandardScaler().fit(train_feat.loc[keep_train, available])

    def build_split(pos_idx, drop_outliers):
        feat = df.iloc[pos_idx][available].copy().fillna(medians)
        raw = df.iloc[pos_idx].copy()
        raw[available] = raw[available].fillna(medians)  # impute features for the RF too
        if drop_outliers:
            keep = outlier_keep_mask(feat, bounds)
            feat = feat.loc[keep]
            raw = raw.loc[keep]
        feat_scaled = pd.DataFrame(
            scaler.transform(feat[available]), columns=available, index=feat.index
        )
        return feat_scaled.reset_index(drop=True), raw.reset_index(drop=True)

    feat_train, raw_train = build_split(train_idx, drop_outliers=True)
    feat_val, raw_val = build_split(val_idx, drop_outliers=False)
    feat_test, raw_test = build_split(test_idx, drop_outliers=False)

    os.makedirs("models", exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)

    feat_train.to_csv(FEATURES_TRAIN_CSV, index=False)
    feat_val.to_csv(FEATURES_VAL_CSV, index=False)
    feat_test.to_csv(FEATURES_TEST_CSV, index=False)
    raw_train.to_csv(RAW_TRAIN_CSV, index=False)
    raw_val.to_csv(RAW_VAL_CSV, index=False)
    raw_test.to_csv(RAW_TEST_CSV, index=False)

    # Combined unscaled view (train+val+test), kept for continuity.
    pd.concat([raw_train, raw_val, raw_test], ignore_index=True).to_csv(RAW_CLEANED_CSV, index=False)

    print(f"\n  Saved scaled features: features_{{train,val,test}}.csv "
          f"({len(feat_train)}/{len(feat_val)}/{len(feat_test)} rows)")
    print(f"  Saved raw splits:      raw_{{train,val,test}}.csv")
    print(f"  Saved: {SCALER_PATH}")
    print(f"  Features ({len(available)}): {available}")


if __name__ == "__main__":
    main()
