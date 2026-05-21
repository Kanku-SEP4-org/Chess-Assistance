import pandas as pd
import numpy as np
from sklearn.metrics import classification_report
import os
import joblib

def main() -> None:
    test_path = os.getenv("TEST_DATA_PATH", "data/test.csv")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Missing test split: {test_path}")

    artifact_path = os.getenv("MODEL_V2_PATH", "models_v2/chess_ai_v2.pkl")
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Missing model artifact: {artifact_path}")

    artifacts = joblib.load(artifact_path)
    model = artifacts["model"]
    km_env = artifacts["km_env"]
    km_game = artifacts["km_game"]
    scaler_env = artifacts["scaler_env"]
    scaler_game = artifacts["scaler_game"]
    env_cols = artifacts["env_cols"]
    game_cols = artifacts["game_cols"]

    test_df = pd.read_csv(test_path)
    if "target" not in test_df.columns:
        raise ValueError("Expected a 'target' column in test split.")

    X_test = test_df.drop(columns=["target"])
    y_test = test_df["target"].astype(int)

    X_test_final = X_test.copy()
    X_test_final["env_cluster"] = km_env.predict(scaler_env.transform(X_test[env_cols]))
    X_test_final["game_cluster"] = km_game.predict(scaler_game.transform(X_test[game_cols]))

    y_pred = model.predict(X_test_final)
    print("Classification Report (trainer-clustering):")
    print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    main()
