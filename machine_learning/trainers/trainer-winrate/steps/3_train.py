import pandas as pd
import os
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


df = pd.read_csv("data/train_val.csv")

X = df.drop("target", axis="columns")
y = (df['target'] == 1).astype(int)

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(max_iter=1000))
])

pipeline.fit(X_train, y_train)

# check sanity
y_pred = pipeline.predict(X_val)
accuracy = accuracy_score(y_val, y_pred)


os.makedirs("models", exist_ok=True)
joblib.dump(pipeline, "models/model.pkl")

metrics = {
    "model_type": "Logistic Regression",
    "accuracy": f"{accuracy:.4f}",
    "classes": ["Not Win (Loss/Draw)", "Win"]
}

with open("models/metrics.json", "w") as f:
    json.dump(metrics, f)

print(f"Model saved accuracy: {accuracy:.2%}")
