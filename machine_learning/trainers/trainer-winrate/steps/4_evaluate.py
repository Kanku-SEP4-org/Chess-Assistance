"""
- Classification performance metrics: accuracy, precision, recall, F1
- Baseline: majority-class classifier
- Winrate output uses predicted win probability (predict_proba), not hard labels
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def main() -> None:
    data_path = os.getenv("EVAL_DATA_PATH", "data/test.csv")
    model_path = os.getenv("MODEL_PATH", "models/model_pipeline.pkl")
    out_path = os.getenv("EVAL_METRICS_PATH", "models/eval_metrics.json")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing evaluation data: {data_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing model artifact: {model_path}")

    df = pd.read_csv(data_path)
    if "target" not in df.columns:
        raise ValueError("Expected a 'target' column in data/test.csv")

    X = df.drop(columns=["target"])
    y_true = df["target"].astype(int).to_numpy()

    model = joblib.load(model_path)

    y_pred = model.predict(X)
    # Probability of win — used for the winrate output (0..100)
    y_prob = model.predict_proba(X)[:, 1]
    y_pred_winrate_int = np.clip(np.rint(y_prob * 100.0), 0, 100).astype(int)

    # Classification metrics.
    accuracy  = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall    = float(recall_score(y_true, y_pred, zero_division=0))
    f1        = float(f1_score(y_true, y_pred, zero_division=0))

    # Baseline: always predict the majority class.
    majority_class = int(np.bincount(y_true).argmax())
    y_baseline = np.full_like(y_true, fill_value=majority_class)
    baseline = {
        "majority_class": majority_class,
        "accuracy":  float(accuracy_score(y_true, y_baseline)),
        "precision": float(precision_score(y_true, y_baseline, zero_division=0)),
        "recall":    float(recall_score(y_true, y_baseline, zero_division=0)),
        "f1":        float(f1_score(y_true, y_baseline, zero_division=0)),
    }

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    report = {
        "data_path": data_path,
        "model_path": model_path,
        "n_test_rows": int(len(df)),
        "features": list(X.columns),
        "winrate_output_rule": "winrate = clip(round(predict_proba * 100), 0, 100)",
        "winrate_preview_first_10": y_pred_winrate_int[:10].tolist(),
        "classification": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "baseline_classification": baseline,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Evaluation complete.")
    print(f"- Saved metrics : {out_path}")
    print(f"- Model    : Accuracy={accuracy:.3f}, Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
    print(f"- Baseline : Accuracy={baseline['accuracy']:.3f} (always predict class {majority_class})")


if __name__ == "__main__":
    main()
