import json
import os

import joblib
import pandas as pd


MODEL_PATH = "../trainer-winrate/models/model_pipeline.pkl"
INPUT_PATH = "data/factor_candidates.csv"
OUT_PATH = "models/factor_impact_report.json"
FEATURES = ["minutes_slept", "minutes_awake", "env_score", "light"]
RECOMMENDABLE_FACTORS = ["temperature_celsius", "co2", "light"]


def predict_candidates(model, candidates: pd.DataFrame) -> pd.DataFrame:
    X = candidates[FEATURES]
    predictions = candidates.copy()
    predictions["win_probability"] = model.predict_proba(X)[:, 1]
    return predictions


def summarize_example(example_name: str, group: pd.DataFrame) -> dict:
    current_rows = group[group["candidate_factor"] == "current"]
    if len(current_rows) != 1:
        raise ValueError(f"Expected exactly one current row for {example_name}")

    current = current_rows.iloc[0]
    current_probability = float(current["win_probability"])

    candidate_rows = group[group["candidate_factor"].isin(RECOMMENDABLE_FACTORS)]
    all_candidates = []
    for _, row in candidate_rows.iterrows():
        factor = row["candidate_factor"]
        increase = float(row["win_probability"] - current_probability)
        all_candidates.append(
            {
                "factor": factor,
                "current_value": float(current[factor]),
                "recommended_value": float(row["recommended_value"]),
                "win_probability": float(row["win_probability"]),
                "increase": increase,
                "increase_percentage_points": increase * 100,
            }
        )

    positive_candidates = [candidate for candidate in all_candidates if candidate["increase"] > 0]
    best_candidate = None
    if positive_candidates:
        best_candidate = max(positive_candidates, key=lambda candidate: candidate["increase"])

    result = {
        "example_name": example_name,
        "input": {
            "minutes_slept": float(current["minutes_slept"]),
            "minutes_awake": float(current["minutes_awake"]),
            "temperature_celsius": float(current["temperature_celsius"]),
            "co2": float(current["co2"]),
            "light": float(current["light"]),
            "env_score": float(current["env_score"]),
        },
        "current_win_probability": current_probability,
        "recommended_factor": best_candidate["factor"] if best_candidate else None,
        "best_recommendation": best_candidate,
        "all_candidates": all_candidates,
    }

    if "target" in current.index and not pd.isna(current["target"]):
        result["target"] = int(current["target"])

    return result


def main() -> None:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Missing production win-rate model: {MODEL_PATH}")
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError("Missing factor candidates. Run steps/2_features.py first.")

    model = joblib.load(MODEL_PATH)
    if not hasattr(model, "predict_proba"):
        raise TypeError("Production win-rate model must support predict_proba.")

    candidates = pd.read_csv(INPUT_PATH)
    missing = [column for column in ["example_name", "candidate_factor", *FEATURES] if column not in candidates.columns]
    if missing:
        raise ValueError(f"Missing required columns in {INPUT_PATH}: {missing}")

    predictions = predict_candidates(model, candidates)
    examples = [
        summarize_example(example_name, group)
        for example_name, group in predictions.groupby("example_name", sort=False)
    ]

    report = {
        "model_path": MODEL_PATH,
        "source_candidates": INPUT_PATH,
        "features": FEATURES,
        "candidate_targets": {
            "temperature_celsius": 20,
            "co2": 500,
            "light": 1500,
        },
        "n_examples": len(examples),
        "examples": examples,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Analysis step complete.")
    print(f"- Examples analyzed: {len(examples)}")
    print(f"- Saved: {OUT_PATH}")

    for result in examples[:5]:
        print(f"\n{result['example_name']}")
        print(f"- Current win probability: {result['current_win_probability']:.3f}")
        if result["best_recommendation"] is None:
            print("- Recommendation: no positive environmental change found")
        else:
            best = result["best_recommendation"]
            print(
                f"- Recommendation: change {best['factor']} "
                f"from {best['current_value']:.2f} to {best['recommended_value']:.2f}"
            )
            print(f"- Increase: {best['increase_percentage_points']:.2f} percentage points")


if __name__ == "__main__":
    main()
