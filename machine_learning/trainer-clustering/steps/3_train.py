import os
import joblib
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

def main() -> None:
    train_path = os.getenv("TRAIN_DATA_PATH", "data/train.csv")
    test_path = os.getenv("TEST_DATA_PATH", "data/test.csv")
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Missing train split: {train_path}")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Missing test split: {test_path}")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Define feature groups (must match step 2)
    env_cols = ['avg_lumen', 'avg_celsius', 'avg_ppm', 'avg_ml']
    game_cols = [
        'rating_diff',
        'total_ply',
        'opening_ply',
        'player_move_count',
        'opponent_move_count',
        'duration_min',
        'player_opening_win_rate',
        'player_opening_game_count',
        'sleep_hours',
    ]
    cat_cols = ['eco_code', 'time_control', 'is_berserk', 'is_player_piece_black']

    if "target" not in train_df.columns or "target" not in test_df.columns:
        raise ValueError("Expected a 'target' column in train/test splits.")

    X_train = train_df.drop(columns=["target"])
    y_train = train_df["target"].astype(int)
    X_test = test_df.drop(columns=["target"])
    y_test = test_df["target"].astype(int)

    # Fit Scalers & Clusters on training data
    scaler_env = StandardScaler().fit(X_train[env_cols])
    scaler_game = StandardScaler().fit(X_train[game_cols])

    # Cluster Environment (Room state)
    env_train_scaled = scaler_env.transform(X_train[env_cols])
    kmeans_env = KMeans(n_clusters=3, random_state=42, n_init=10).fit(env_train_scaled)

    # Cluster Game Parameters (Performance state)
    game_train_scaled = scaler_game.transform(X_train[game_cols])
    kmeans_game = KMeans(n_clusters=4, random_state=42, n_init=10).fit(game_train_scaled)

    # Add Cluster Labels to features
    X_train_final = X_train.copy()
    X_train_final['env_cluster'] = kmeans_env.labels_
    X_train_final['game_cluster'] = kmeans_game.labels_

    # Apply to Test Set
    X_test_final = X_test.copy()
    X_test_final['env_cluster'] = kmeans_env.predict(scaler_env.transform(X_test[env_cols]))
    X_test_final['game_cluster'] = kmeans_game.predict(scaler_game.transform(X_test[game_cols]))

    # One-Hot Encode Categorical features + Clusters
    # Note: Treat cluster IDs as categorical
    cat_features_to_encode = cat_cols + ['env_cluster', 'game_cluster']
    preprocessor = ColumnTransformer(
        transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), cat_features_to_encode)],
        remainder='passthrough',
    )

    model_pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]
    )
    model_pipeline.fit(X_train_final, y_train)

    os.makedirs("models_v2", exist_ok=True)
    artifact_path = os.getenv("MODEL_V2_PATH", "models_v2/chess_ai_v2.pkl")
    joblib.dump(
        {
            "model": model_pipeline,
            "km_env": kmeans_env,
            "km_game": kmeans_game,
            "scaler_env": scaler_env,
            "scaler_game": scaler_game,
            "env_cols": env_cols,
            "game_cols": game_cols,
            "cat_cols": cat_cols,
        },
        artifact_path,
    )
    print(f"Saved model artifact: {artifact_path}")


if __name__ == "__main__":
    main()
