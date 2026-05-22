import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

df = pd.read_csv("data/train_val.csv")

X = df.drop(columns=["player_centipawn_loss"])
y = df["player_centipawn_loss"]

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42
)

#Best params found in Grid Search
#learning_rate=0.027, max_depth=8, max_iter=210
pipeline = Pipeline([
    ("model", HistGradientBoostingRegressor(
        learning_rate=0.027,
        max_depth=8,
        max_iter=210,
        random_state=42,
    )),
])

pipeline.fit(X_train, y_train)
y_pred_val = pipeline.predict(X_val)
val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))

# I train model on the entire train_val set 
pipeline.fit(X, y)

os.makedirs("models", exist_ok=True)
# save the model pipeline into pkl file so that it can be used in the api
joblib.dump(pipeline, "models/model_pipeline.pkl")

metrics = {
    "model_type": "HistGradientBoostingRegressor",
    "hyperparameters": {"learning_rate": 0.027, "max_depth": 8, "max_iter": 210},
    "val_rmse": round(float(val_rmse), 4),
}

with open("models/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"Model saved to models/model_pipeline.pkl")
print(f"Validation RMSE: {val_rmse:.2f}")
