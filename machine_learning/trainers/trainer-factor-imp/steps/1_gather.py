import os

import pandas as pd


RAW_DATA_PATH = "data/reworked_mock_data.csv"
OUT_PATH = "data/factor_examples.csv"
DEFAULT_MINUTES_AWAKE = 60


def main() -> None:
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Missing source data: {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    required_columns = ["avg_lumen", "avg_celsius", "avg_ppm", "sleep_hours"]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {RAW_DATA_PATH}: {missing}")

    factor_examples = pd.DataFrame(
        {
            "example_name": [f"example_{index + 1}" for index in range(len(df))],
            "minutes_slept": df["sleep_hours"].astype(float) * 60,
            "minutes_awake": DEFAULT_MINUTES_AWAKE,
            "temperature_celsius": df["avg_celsius"].astype(float),
            "co2": df["avg_ppm"].astype(float),
            "light": df["avg_lumen"].astype(float),
        }
    )

    if "target" in df.columns:
        factor_examples["target"] = df["target"]

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    factor_examples.to_csv(OUT_PATH, index=False)

    print("Gather step complete.")
    print(f"- Source rows: {len(df)}")
    print(f"- Default minutes_awake: {DEFAULT_MINUTES_AWAKE}")
    print(f"- Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
