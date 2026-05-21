"""
Step 1: Exploratory Data Analysis for Angriness (Tilt) Predictor.

Loads the dataset, prints summary statistics, checks for nulls/duplicates,
and shows feature distributions and correlations. Outputs are printed to
stdout and plots saved to steps/init/plots/.

Run from trainer-angriness-predictor/:
    python steps/init/1_eda.py
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
LEGACY_DIR = ROOT / "data" / "legacy"
PLOT_DIR = Path(__file__).resolve().parent / "plots"
PLOT_DIR.mkdir(exist_ok=True)

DIVERSE_CSV = RAW_DIR / "angriness_dataset_diverse.csv"
ORIGINAL_CSV = LEGACY_DIR / "angriness_dataset.csv"
CSV_PATH = DIVERSE_CSV if DIVERSE_CSV.exists() else ORIGINAL_CSV

IDENTIFIER_COLS = ["game_id", "username", "created_at", "last_move_at"]

FEATURE_COLS = [
    "sleep_duration",
    "consecutive_losses",
    "awaken_duration",
    "avg_tpm",
    "move_cnt",
    "inaccuracy_cnt_player",
    "mistake_cnt_player",
    "blunder_cnt_player",
    "elo",
    "elo_diff",
    "player_color",
    "time_control_initial",
    "time_control_increment",
    "opponent_elo",
    "elo_gap",
    "move_cnt_player",
    "avg_tpm_seconds_player",
    "consecutive_losses_pregame",
    "acpl_player",
    "accuracy_player",
    "avg_ppm",
    "avg_celsius",
    "water_intake_ml",
    "avg_lux",
]


def main():
    print(f"Loading: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Shape: {df.shape}")
    print(f"Unique players: {df['username'].nunique()}")

    # --- Basic stats ---
    print("\n=== Describe (numeric) ===")
    print(df.describe().T.to_string())

    # --- Nulls ---
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls) > 0:
        print(f"\n=== Null counts ===\n{nulls.to_string()}")
    else:
        print("\nNo nulls found.")

    # --- Duplicates ---
    dupes = df.duplicated(subset=["game_id", "username"]).sum()
    print(f"\nDuplicate (game_id, username) rows: {dupes}")

    # --- ELO distribution ---
    if "elo" in df.columns:
        bins = [0, 1200, 1600, 2000, 2400, 5000]
        labels = ["800-1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]
        df["_bracket"] = pd.cut(df["elo"], bins=bins, labels=labels)
        print(f"\n=== Rows per ELO bracket ===\n{df['_bracket'].value_counts().sort_index().to_string()}")
        df.drop(columns=["_bracket"], inplace=True)

    # --- Feature distributions ---
    numeric_features = [c for c in FEATURE_COLS if c in df.columns and c != "player_color"]
    available = df[numeric_features].select_dtypes(include=[np.number]).columns.tolist()

    ncols = 4
    nrows = (len(available) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows))
    axes = axes.flatten()

    for i, col in enumerate(available):
        df[col].dropna().hist(bins=50, ax=axes[i], edgecolor="white", alpha=0.8)
        axes[i].set_title(col, fontsize=9)
        axes[i].tick_params(labelsize=7)

    for j in range(len(available), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Feature Distributions", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(PLOT_DIR / "distributions.png", dpi=150)
    print(f"\nSaved: {PLOT_DIR / 'distributions.png'}")
    plt.close(fig)

    # --- Correlation matrix ---
    corr = df[available].corr()
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                annot_kws={"size": 6}, linewidths=0.5)
    ax.set_title("Feature Correlation Matrix")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "correlation_matrix.png", dpi=150)
    print(f"Saved: {PLOT_DIR / 'correlation_matrix.png'}")
    plt.close(fig)

    # --- Highly correlated pairs ---
    print("\n=== Highly correlated pairs (|r| > 0.8) ===")
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    pairs = [(col, row, upper.loc[row, col])
             for col in upper.columns for row in upper.index
             if abs(upper.loc[row, col]) > 0.8]
    if pairs:
        for c1, c2, r in sorted(pairs, key=lambda x: -abs(x[2])):
            print(f"  {c1:30s} vs {c2:30s}  r={r:.3f}")
    else:
        print("  None found.")

    # --- IoT feature stats ---
    iot_cols = [c for c in ["avg_ppm", "avg_celsius", "water_intake_ml", "avg_lux"] if c in df.columns]
    if iot_cols:
        print(f"\n=== IoT feature stats ===\n{df[iot_cols].describe().T.to_string()}")

    print("\nEDA complete.")


if __name__ == "__main__":
    main()
