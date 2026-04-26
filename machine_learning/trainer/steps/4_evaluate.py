"""
Step 4: Evaluate the model (simple v0).

Current project state:
- Step 2 writes `data/features.csv`
- Step 3 writes `models/model.pkl`

Slides alignment (Regression + Validation/Performance Metrics):
- Regression performance metrics: MSE, RMSE, MAE, R2
- Validation reminder: compare against a simple baseline
- Preprocessing reminder: split test out before preprocessing

Predictions are converted to a winrate in [0..100]:
  winrate = clip(round(pred * 100), 0, 100)

TODO (future improvements):
- Split test out before preprocessing (current pipeline does not do this yet)
- Add classification-style metrics (confusion matrix, ROC/PR, log loss)
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def main() -> None:
    # Load inputs produced by earlier pipeline steps.
    data_path = os.getenv("EVAL_DATA_PATH", "data/features.csv")
    model_path = os.getenv("MODEL_PATH", "models/model.pkl")
    out_path = os.getenv("EVAL_METRICS_PATH", "models/eval_metrics.json")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing evaluation data: {data_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing model artifact: {model_path}")

    # Load dataset.
    df = pd.read_csv(data_path)
    if "target" not in df.columns:
        raise ValueError("Expected a 'target' column in data/features.csv")

    X = df.drop(columns=["target"])
    y_true = df["target"].astype(float).to_numpy()

    # Load model.
    model = joblib.load(model_path)

    y_pred = np.asarray(model.predict(X), dtype=float)

    # Convert predictions to winrate 0..100.
    y_true_winrate = np.clip(y_true * 100.0, 0.0, 100.0)
    y_pred_winrate = np.clip(y_pred * 100.0, 0.0, 100.0)
    y_pred_winrate_int = np.clip(np.rint(y_pred * 100.0), 0.0, 100.0).astype(int)

    # Regression metrics.
    mae = float(mean_absolute_error(y_true_winrate, y_pred_winrate))
    mse = float(mean_squared_error(y_true_winrate, y_pred_winrate))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true_winrate, y_pred_winrate))

    # Baseline: predict the mean winrate.
    baseline_pred = np.full_like(y_true_winrate, fill_value=float(np.mean(y_true_winrate)))
    baseline_mse = float(mean_squared_error(y_true_winrate, baseline_pred))
    baseline = {
        "mae": float(mean_absolute_error(y_true_winrate, baseline_pred)),
        "mse": baseline_mse,
        "rmse": float(np.sqrt(baseline_mse)),
        "r2": float(r2_score(y_true_winrate, baseline_pred)),
    }

    # Small JSON report
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    report = {
        "data_path": data_path,
        "model_path": model_path,
        "n_rows": int(len(df)),
        "features": list(X.columns),
        "winrate_output_rule": "winrate = clip(round(pred*100), 0, 100)",
        "winrate_preview_first_10": y_pred_winrate_int[:10].tolist(),
        "regression": {"mae": mae, "mse": mse, "rmse": rmse, "r2": r2},
        "baseline_regression": baseline,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Evaluation complete.")
    print(f"- Saved metrics: {out_path}")
    print(f"- Regression: MAE={mae:.3f}, MSE={mse:.3f}, RMSE={rmse:.3f}, R2={r2:.3f}")
    print(
        f"- Baseline:  MAE={baseline['mae']:.3f}, MSE={baseline['mse']:.3f}, "
        f"RMSE={baseline['rmse']:.3f}, R2={baseline['r2']:.3f}"
    )


if __name__ == "__main__":
    main()
