"""
Build a diverse angriness predictor training CSV from two local datasets:

  1. data/raw/processed_player_data_v2.csv — 37,274 rows (2 per game, per-player
     perspective), 22,431 unique players, ELO 780-2997, has ACPL but no
     inaccuracy/mistake/blunder breakdown.
  2. data/raw/Chess games stats.csv — 18,637 rows (1 per game), same games,
     has per-side inaccuracy/mistake/blunder counts.

Joins them, maps to the angriness 28-column CSV schema, adds synthetic IoT
features, balances across ELO brackets, and merges with the existing
DrNykterstein dataset.

IoT distributions from:
  cannyboizs-notes/angriness-predictor-feature-recommendation.md

Usage:
    python scripts/fetch_huggingface_dataset.py
    python scripts/fetch_huggingface_dataset.py --rows-per-bracket 8000
    python scripts/fetch_huggingface_dataset.py --no-downsample
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RAW_DIR = DATA_DIR / "raw"
LEGACY_DIR = DATA_DIR / "legacy"

OUTPUT_CSV = RAW_DIR / "angriness_dataset_diverse.csv"
EXISTING_CSV = LEGACY_DIR / "angriness_dataset.csv"

PLAYER_CSV = RAW_DIR / "processed_player_data_v2.csv"
STATS_CSV = RAW_DIR / "Chess games stats.csv"

SEED = 42
ROWS_PER_BRACKET = 6000

BRACKETS = {
    "beginner": (800, 1200),
    "intermediate": (1200, 1600),
    "advanced": (1600, 2000),
    "expert": (2000, 2400),
    "master": (2400, 5000),
}

CSV_COLUMNS = [
    "sleep_duration", "consecutive_losses", "awaken_duration", "avg_tpm",
    "move_cnt", "inaccuracy_cnt_player", "mistake_cnt_player",
    "blunder_cnt_player", "elo", "elo_diff", "game_id", "username",
    "created_at", "last_move_at", "player_color", "time_control_initial",
    "time_control_increment", "opponent_elo", "elo_gap", "move_cnt_player",
    "avg_tpm_seconds_player", "consecutive_losses_pregame", "acpl_player",
    "accuracy_player", "avg_ppm", "avg_celsius", "water_intake_ml", "avg_lux",
]


# ---------------------------------------------------------------------------
# Load & join
# ---------------------------------------------------------------------------

def load_and_join() -> pd.DataFrame:
    print("Loading datasets...")

    players = pd.read_csv(PLAYER_CSV)
    stats = pd.read_csv(STATS_CSV)
    print(f"  processed_player_data_v2: {len(players)} rows, {players['player_username'].nunique()} players")
    print(f"  Chess games stats:        {len(stats)} rows")

    # Build a lookup from stats: Game ID → per-side analysis
    stats_white = stats[["Game ID",
                         "White's Number of Inaccuracies",
                         "White's Number of Mistakes",
                         "White's Number of Blunders"]].copy()
    stats_white.columns = ["Game ID", "inaccuracy_cnt", "mistake_cnt", "blunder_cnt"]
    stats_white["_side"] = 1  # player_white=1

    stats_black = stats[["Game ID",
                         "Black's Number of Inaccuracies",
                         "Black's Number of Mistakes",
                         "Black's Number of Blunders"]].copy()
    stats_black.columns = ["Game ID", "inaccuracy_cnt", "mistake_cnt", "blunder_cnt"]
    stats_black["_side"] = 0  # player_white=0

    stats_combined = pd.concat([stats_white, stats_black], ignore_index=True)

    # Join on Game ID + side
    merged = players.merge(
        stats_combined,
        left_on=["Game ID", "player_white"],
        right_on=["Game ID", "_side"],
        how="left",
    )
    merged = merged.drop(columns=["_side"])

    nulls = merged["inaccuracy_cnt"].isnull().sum()
    print(f"  After join: {len(merged)} rows, {nulls} missing analysis")

    return merged


# ---------------------------------------------------------------------------
# Consecutive losses per player
# ---------------------------------------------------------------------------

def compute_consecutive_losses(df: pd.DataFrame) -> pd.DataFrame:
    print("Computing consecutive losses per player...")

    # Determine loss: opponent CPL is lower = opponent played better = likely loss
    # Actually we don't have win/loss result directly.
    # Use a heuristic: if player CPL > opponent CPL by a margin, likely a loss.
    # Better: use rating_diff — negative rating_diff means rating went down = loss.
    # But some draws also lose rating. This is the best approximation available.
    # elo_delta_ratio < 0 means the player lost rating.
    is_loss = (df["elo_delta_ratio"] < -0.01).values

    df = df.sort_values(["player_username", "Game ID"]).reset_index(drop=True)
    usernames = df["player_username"].values
    consec = np.zeros(len(df), dtype=int)
    streak = 0
    prev_user = None

    for i in range(len(df)):
        if usernames[i] != prev_user:
            prev_user = usernames[i]
            streak = 0
        consec[i] = streak
        streak = streak + 1 if is_loss[i] else 0

    df["consecutive_losses"] = consec
    df["consecutive_losses_pregame"] = consec
    print(f"  Max streak found: {consec.max()}")
    return df


# ---------------------------------------------------------------------------
# Compute accuracy from ACPL (approximate)
# ---------------------------------------------------------------------------

def acpl_to_accuracy(acpl: pd.Series) -> pd.Series:
    """
    Approximate accuracy from ACPL using the Lichess formula:
    accuracy ≈ 103.1668 * exp(-0.04354 * acpl) - 3.1668
    Clipped to [0, 100].
    """
    accuracy = 103.1668 * np.exp(-0.04354 * acpl) - 3.1668
    return accuracy.clip(0, 100).round(1)


# ---------------------------------------------------------------------------
# Build CSV-schema DataFrame
# ---------------------------------------------------------------------------

def build_csv_dataframe(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    print("Building CSV-schema DataFrame...")
    n = len(df)

    # Time control: all games are rapid. Lichess rapid = typically 600+0 or 900+0.
    # time_control_encoded=3 likely means rapid. Use 600s (10min) as default.
    tc_initial = 600
    tc_increment = 0

    # No real timestamps available — generate synthetic ones spread over a year
    base_ts = int(pd.Timestamp("2024-01-01").timestamp() * 1000)
    offsets = rng.integers(0, 365 * 24 * 3600 * 1000, size=n)
    created_at = base_ts + offsets

    # Approximate move count from opening_ply (only partial info available)
    # Rapid games average ~60-80 total ply. Use a realistic distribution.
    move_cnt = rng.integers(40, 120, size=n)
    is_white = df["player_white"].values == 1
    move_cnt_player = np.where(is_white, (move_cnt + 1) // 2, move_cnt // 2)

    # Approximate avg_tpm: rapid games last ~10-20min for ~60-80 moves
    game_duration_s = rng.uniform(300, 1200, size=n)
    avg_tpm = game_duration_s / move_cnt
    avg_tpm_seconds_player = game_duration_s / move_cnt_player
    last_move_at = created_at + (game_duration_s * 1000).astype(np.int64)

    # Synthetic IoT features
    # Source: cannyboizs-notes/angriness-predictor-feature-recommendation.md
    #
    # CO2 (avg_ppm): μ=1549, σ=326.60, range 1179-2393
    #   >1000ppm impairs vigilance, >1500ppm decision-making impairment
    #
    # Temperature (avg_celsius): μ=25.17, σ=2.12, range 22.10-28.75
    #   >23°C causes irritability, 24-26°C triggers "hope chess"
    #
    # Water intake (water_intake_ml): μ=700, σ=300, range 300-1500
    #   Dehydration raises cortisol, lowers frustration threshold
    #
    # Light (avg_lux): μ=400, σ=200, range 50-1000
    #   <100 = drowsiness, 750-1000 = peak cognitive performance
    #
    # Sleep (sleep_duration): μ=7.0, σ=1.5, range 3-12
    #   Sleep deprivation impairs emotional regulation
    #
    # Awaken duration: μ=4.0, σ=2.0, range 0.5-16

    result = pd.DataFrame({
        "sleep_duration": np.round(np.clip(rng.normal(7.0, 1.5, n), 3.0, 12.0), 2),
        "consecutive_losses": df["consecutive_losses"].values,
        "awaken_duration": np.round(np.clip(rng.normal(4.0, 2.0, n), 0.5, 16.0), 2),
        "avg_tpm": np.round(avg_tpm, 4),
        "move_cnt": move_cnt,
        "inaccuracy_cnt_player": df["inaccuracy_cnt"].fillna(0).astype(int).values,
        "mistake_cnt_player": df["mistake_cnt"].fillna(0).astype(int).values,
        "blunder_cnt_player": df["blunder_cnt"].fillna(0).astype(int).values,
        "elo": df["player_rating"].values,
        "elo_diff": np.round(df["elo_delta_ratio"].fillna(0).values * df["player_rating"].values).astype(int),
        "game_id": df["Game ID"].values,
        "username": df["player_username"].values,
        "created_at": created_at,
        "last_move_at": last_move_at,
        "player_color": np.where(is_white, "white", "black"),
        "time_control_initial": tc_initial,
        "time_control_increment": tc_increment,
        "opponent_elo": df["opponent_rating"].values,
        "elo_gap": (df["player_rating"] - df["opponent_rating"]).values,
        "move_cnt_player": move_cnt_player,
        "avg_tpm_seconds_player": np.round(avg_tpm_seconds_player, 4),
        "consecutive_losses_pregame": df["consecutive_losses_pregame"].values,
        "acpl_player": df["player_centipawn_loss"].values,
        "accuracy_player": acpl_to_accuracy(df["player_centipawn_loss"]).values,
        "avg_ppm": np.round(np.clip(rng.normal(1549, 326.60, n), 1179, 2393), 2),
        "avg_celsius": np.round(np.clip(rng.normal(25.17, 2.12, n), 22.10, 28.75), 2),
        "water_intake_ml": np.clip(rng.normal(700, 300, n), 300, 1500).astype(int),
        "avg_lux": np.round(np.clip(rng.normal(400, 200, n), 50, 1000), 2),
    })

    print(f"  Built {len(result)} rows, {len(result.columns)} columns")
    return result


# ---------------------------------------------------------------------------
# Balance across ELO brackets
# ---------------------------------------------------------------------------

def balance_brackets(df: pd.DataFrame, rows_per_bracket: int,
                     rng: np.random.Generator) -> pd.DataFrame:
    print(f"\nBalancing ELO brackets ({rows_per_bracket} rows each)...")
    frames = []
    for name, (lo, hi) in BRACKETS.items():
        bracket = df[(df["elo"] >= lo) & (df["elo"] < hi)]
        n = min(rows_per_bracket, len(bracket))
        if n == 0:
            print(f"  [!] No rows for {name} ({lo}-{hi})")
            continue
        sampled = bracket.sample(n=n, random_state=rng)
        frames.append(sampled)
        print(f"  {name:15s} ({lo:4d}-{hi:4d}): {n:,} rows sampled from {len(bracket):,}")

    balanced = pd.concat(frames, ignore_index=True)
    print(f"  Total: {len(balanced):,} rows")
    return balanced


# ---------------------------------------------------------------------------
# Merge with existing CSV
# ---------------------------------------------------------------------------

def merge_with_existing(new_df: pd.DataFrame,
                        downsample_magnus: int = 6000) -> pd.DataFrame:
    if not EXISTING_CSV.exists():
        return new_df

    existing = pd.read_csv(EXISTING_CSV)
    print(f"\n  Existing CSV: {len(existing):,} rows ({existing['username'].nunique()} player(s))")

    # Drop rows missing critical analysis data
    analysis_cols = ["acpl_player", "blunder_cnt_player", "mistake_cnt_player",
                     "inaccuracy_cnt_player"]
    available_cols = [c for c in analysis_cols if c in existing.columns]
    if available_cols:
        before = len(existing)
        existing = existing.dropna(subset=available_cols)
        dropped = before - len(existing)
        if dropped > 0:
            print(f"  Dropped {dropped:,} rows missing analysis -> {len(existing):,} remaining")

    # Fill remaining nulls in existing data
    fill_rng = np.random.default_rng(SEED + 1)
    n_ex = len(existing)
    if "awaken_duration" in existing.columns:
        mask = existing["awaken_duration"].isna()
        n_fill = mask.sum()
        if n_fill > 0:
            existing.loc[mask, "awaken_duration"] = np.round(
                np.clip(fill_rng.normal(4.0, 2.0, n_fill), 0.5, 16.0), 2)

    for col in ["avg_tpm", "avg_tpm_seconds_player"]:
        if col in existing.columns:
            existing[col] = existing[col].fillna(existing[col].median())

    for col in ["elo_diff"]:
        if col in existing.columns:
            existing[col] = existing[col].fillna(0)

    if "opponent_elo" in existing.columns and "elo" in existing.columns:
        mask = existing["opponent_elo"].isna()
        existing.loc[mask, "opponent_elo"] = existing.loc[mask, "elo"]
        existing["elo_gap"] = existing["elo"] - existing["opponent_elo"]

    if downsample_magnus > 0:
        magnus_mask = existing["username"] == "DrNykterstein"
        magnus_rows = existing[magnus_mask]
        other_rows = existing[~magnus_mask]

        if len(magnus_rows) > downsample_magnus:
            magnus_sampled = magnus_rows.sample(n=downsample_magnus, random_state=SEED)
            existing = pd.concat([magnus_sampled, other_rows], ignore_index=True)
            print(f"  Downsampled DrNykterstein: {len(magnus_rows):,} -> {downsample_magnus:,}")
        else:
            print(f"  DrNykterstein: {len(magnus_rows):,} rows (under cap, keeping all)")

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["game_id", "username"], keep="first")
    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build angriness training CSV from local Lichess datasets")
    parser.add_argument("--no-downsample", action="store_true",
                        help="Keep all existing DrNykterstein rows")
    parser.add_argument("--rows-per-bracket", type=int, default=ROWS_PER_BRACKET,
                        help=f"Rows per ELO bracket (default: {ROWS_PER_BRACKET})")
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)

    # 1. Load & join
    df = load_and_join()

    # 2. Consecutive losses
    df = compute_consecutive_losses(df)

    # 3. Build CSV
    result = build_csv_dataframe(df, rng)

    # 4. Balance
    balanced = balance_brackets(result, args.rows_per_bracket, rng)

    # 5. Merge
    print("\n=== Merging ===")
    downsample = 0 if args.no_downsample else 2000
    final = merge_with_existing(balanced, downsample_magnus=downsample)

    # 6. Final bracket cap — prevent any bracket from dominating
    print("\n=== Final bracket cap ===")
    bins = [0, 1200, 1600, 2000, 2400, 5000]
    labels_list = ["800-1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]
    final["_bracket"] = pd.cut(final["elo"], bins=bins, labels=labels_list)
    capped_frames = []
    for label in labels_list:
        bracket = final[final["_bracket"] == label]
        n = min(args.rows_per_bracket, len(bracket))
        if n < len(bracket):
            bracket = bracket.sample(n=n, random_state=SEED)
            print(f"  {label}: capped {len(final[final['_bracket'] == label]):,} -> {n:,}")
        capped_frames.append(bracket)
    final = pd.concat(capped_frames, ignore_index=True)
    final = final.drop(columns=["_bracket"])

    # 7. Save
    final.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Output: {OUTPUT_CSV}")
    print(f"  Total rows: {len(final):,}")
    print(f"  Unique players: {final['username'].nunique():,}")

    # Summary
    bins = [0, 1200, 1600, 2000, 2400, 5000]
    labels = ["800-1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]
    final["_bracket"] = pd.cut(final["elo"], bins=bins, labels=labels)
    print("\n  Rows per ELO bracket:")
    print(final["_bracket"].value_counts().sort_index().to_string())

    print("\n  ACPL by bracket (median):")
    print(final.groupby("_bracket", observed=True)["acpl_player"].median().to_string())

    nulls = final[CSV_COLUMNS].isnull().sum()
    nulls = nulls[nulls > 0]
    print("\n  Null counts:")
    if len(nulls) > 0:
        print(nulls.to_string())
    else:
        print("  None — all columns populated!")

    print("\nDone.")


if __name__ == "__main__":
    main()
