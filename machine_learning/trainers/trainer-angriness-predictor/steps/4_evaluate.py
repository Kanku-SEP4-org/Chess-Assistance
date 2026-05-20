import json
import os

import joblib
import numpy as np
import pandas as pd

DATA_PATH = os.getenv("EVAL_DATA_PATH", "data/processed/features.csv")
RAW_DATA_PATH = os.getenv("EVAL_RAW_PATH", "data/processed/raw_validated.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
BINS_PATH = os.getenv("BINS_PATH", "models/angriness_bins.json")
OUT_PATH = os.getenv("EVAL_METRICS_PATH", "models/eval_metrics.json")

TILT_FEATURES = [
    "acpl_player", "blunder_cnt_player", "mistake_cnt_player",
    "inaccuracy_cnt_player", "consecutive_losses_pregame",
    "accuracy_player", "avg_tpm_seconds_player",
]


def score_to_angriness(score: float, bin_edges: list[float]) -> int:
    for i in range(len(bin_edges) - 1):
        if score <= bin_edges[i + 1]:
            return 5 - i
    return 1


def main():
    for path, name in [(DATA_PATH, "features"), (MODEL_PATH, "model"), (BINS_PATH, "bins")]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing {name}: {path}")

    df = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)
    with open(BINS_PATH) as f:
        bins_data = json.load(f)
    bin_edges = bins_data["bin_edges"]

    scores = model.decision_function(df.values)
    angriness_levels = np.array([score_to_angriness(s, bin_edges) for s in scores])

    # Per-level stats using unscaled data for interpretability
    per_level = {}
    raw = pd.read_csv(RAW_DATA_PATH) if os.path.exists(RAW_DATA_PATH) else None

    if raw is not None and len(raw) == len(df):
        available_tilt = [c for c in TILT_FEATURES if c in raw.columns]
        raw["_angriness"] = angriness_levels
        raw["_score"] = scores

        for level in range(1, 6):
            mask = raw["_angriness"] == level
            subset = raw.loc[mask]
            stats = {"count": int(mask.sum())}
            for col in available_tilt:
                stats[f"mean_{col}"] = round(float(subset[col].mean()), 2) if len(subset) > 0 else None
            stats["mean_score"] = round(float(subset["_score"].mean()), 4) if len(subset) > 0 else None
            per_level[str(level)] = stats

    # Validation: high angriness should correlate with worse play
    validations = {}
    if raw is not None and len(raw) == len(df):
        raw["_angriness"] = angriness_levels
        calm = raw[raw["_angriness"].isin([1, 2])]
        tilted = raw[raw["_angriness"].isin([4, 5])]

        checks = {
            "acpl_higher_when_tilted": (
                "acpl_player" in raw.columns and
                tilted["acpl_player"].mean() > calm["acpl_player"].mean()
            ),
            "blunders_higher_when_tilted": (
                "blunder_cnt_player" in raw.columns and
                tilted["blunder_cnt_player"].mean() > calm["blunder_cnt_player"].mean()
            ),
            "consecutive_losses_higher_when_tilted": (
                "consecutive_losses_pregame" in raw.columns and
                tilted["consecutive_losses_pregame"].mean() > calm["consecutive_losses_pregame"].mean()
            ),
        }
        validations = {k: bool(v) for k, v in checks.items()}
        all_pass = all(validations.values())
        validations["all_passed"] = all_pass

    report = {
        "data_path": DATA_PATH,
        "model_path": MODEL_PATH,
        "n_rows": len(df),
        "n_features": len(df.columns),
        "score_stats": {
            "min": round(float(scores.min()), 4),
            "max": round(float(scores.max()), 4),
            "mean": round(float(scores.mean()), 4),
            "std": round(float(scores.std()), 4),
        },
        "per_level": per_level,
        "validations": validations,
    }

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print("Evaluation complete.")
    print(f"  Saved: {OUT_PATH}")

    if validations:
        status = "PASS" if validations.get("all_passed") else "FAIL"
        print(f"\n  Validation: {status}")
        for check, result in validations.items():
            if check != "all_passed":
                print(f"    {check}: {'PASS' if result else 'FAIL'}")

    if per_level:
        print(f"\n  Key stats by angriness level:")
        print(f"  {'Level':>5}  {'Count':>6}  {'ACPL':>6}  {'Blunders':>8}  {'ConsLoss':>8}")
        for level in range(1, 6):
            s = per_level.get(str(level), {})
            acpl = s.get("mean_acpl_player", "-")
            blunders = s.get("mean_blunder_cnt_player", "-")
            cons = s.get("mean_consecutive_losses_pregame", "-")
            print(f"  {level:>5}  {s.get('count', 0):>6}  {acpl:>6}  {blunders:>8}  {cons:>8}")


if __name__ == "__main__":
    main()
