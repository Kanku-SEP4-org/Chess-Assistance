import os
import joblib
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

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
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features_to_encode)
    ],
    remainder='passthrough'
)
os.makedirs("models", exist_ok=True)
joblib.dump({
    'model': model_pipeline, 
    'km_env': kmeans_env, 
    'km_game': kmeans_game,
    'scaler_env': scaler_env,
    'scaler_game': scaler_game
}, 'models_v2/chess_ai_v2.pkl')