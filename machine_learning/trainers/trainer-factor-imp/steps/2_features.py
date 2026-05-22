import os

import pandas as pd


INPUT_PATH = "data/factor_examples.csv"
OUT_PATH = "data/factor_candidates.csv"


def calculate_env_score(temperature_celsius: float, co2: float) -> float:
    temp_dist = abs(temperature_celsius - 20)
    co2_norm = (co2 - 400) / 1600
    return 1 - (co2_norm * 0.7 + (temp_dist / 5) * 0.3)


def main() -> None:
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError("Missing factor examples. Run steps/1_gather.py first.")

    df = pd.read_csv(INPUT_PATH)
    required_columns = [
        "example_name",
        "minutes_slept",
        "minutes_awake",
        "temperature_celsius",
        "co2",
        "light",
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {INPUT_PATH}: {missing}")

    rows = []
    for _, example in df.iterrows():
        base = example.to_dict()
        candidates = [
            ("current", None, None),
            ("temperature_celsius", "temperature_celsius", 20),
            ("co2", "co2", 500),
            ("light", "light", 1500),
        ]

        for candidate_name, factor, recommended_value in candidates:
            candidate = dict(base)
            if factor is not None:
                candidate[factor] = recommended_value

            candidate["candidate_factor"] = candidate_name
            candidate["recommended_value"] = recommended_value
            candidate["env_score"] = calculate_env_score(
                candidate["temperature_celsius"],
                candidate["co2"],
            )
            rows.append(candidate)

    factor_candidates = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    factor_candidates.to_csv(OUT_PATH, index=False)

    print("Feature step complete.")
    print(f"- Source examples: {len(df)}")
    print(f"- Candidate rows: {len(factor_candidates)}")
    print(f"- Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
