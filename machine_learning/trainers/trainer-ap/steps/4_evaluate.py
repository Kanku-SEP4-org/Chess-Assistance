import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def main() -> None:
    data_path  = os.getenv("EVAL_DATA_PATH",    "data/test.csv")
    model_path = os.getenv("MODEL_PATH",         "models/model_pipeline.pkl")
    out_path   = os.getenv("EVAL_METRICS_PATH",  "models/eval_metrics.json")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing evaluation data: {data_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing model artifact: {model_path}")

    df = pd.read_csv(data_path)
    if "player_centipawn_loss" not in df.columns:
        raise ValueError("Expected a 'player_centipawn_loss' column in the test file.")

    X      = df.drop(columns=["player_centipawn_loss"])
    y_true = df["player_centipawn_loss"].to_numpy()

    model  = joblib.load(model_path)
    y_pred = model.predict(X)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))

    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X, y_true)
    y_dummy      = dummy.predict(X)
    dummy_rmse   = float(np.sqrt(mean_squared_error(y_true, y_dummy)))
    dummy_mae    = float(mean_absolute_error(y_true, y_dummy))
    dummy_r2     = float(r2_score(y_true, y_dummy))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    report = {
        "data_path":  data_path,
        "model_path": model_path,
        "n_test_rows": int(len(df)),
        "features": list(X.columns),
        "model": {
            "rmse": round(rmse, 4),
            "mae":  round(mae,  4),
            "r2":   round(r2,   4),
        },
        "baseline_dummy_mean": {
            "rmse": round(dummy_rmse, 4),
            "mae":  round(dummy_mae,  4),
            "r2":   round(dummy_r2,   4),
        },
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Evaluation complete.")
    print(f"- Saved metrics : {out_path}")
    print(f"- Model   : RMSE={rmse:.2f}, MAE={mae:.2f}, R²={r2:.4f}")
    print(f"- Baseline: RMSE={dummy_rmse:.2f}, MAE={dummy_mae:.2f}, R²={dummy_r2:.4f}")


if __name__ == "__main__":
    main()
