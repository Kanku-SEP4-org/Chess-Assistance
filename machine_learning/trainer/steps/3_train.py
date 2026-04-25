import pandas as pd
import os
import joblib
import json
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, accuracy_score

#load features
df = pd.read_csv("data/features.csv")
X =  df.drop("target", axis = "columns")
y = df['target']

#slip/train 80/20
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

print("Model Exploration")

#model 1
lr = LinearRegression()
lr.fit(X_train, y_train)
lr_mse = mean_squared_error(y_val, lr.predict(X_val))
print(f"Linear regression MSE: {lr_mse:.4f}")

#model 2
y_train_bin = (y_train == 1).astype(int)
y_val_bin = (y_val == 1).astype(int)
log_reg = LogisticRegression()
log_reg.fit(X_train, y_train_bin)
log_acc = accuracy_score(y_val_bin, log_reg.predict(X_val))
print(f"Logistic Regr. Accuracy: {log_acc:.4f}")

#model 3 with hyperparameters
rf = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20]
}
grid_search = GridSearchCV(rf, param_grid, cv=3)
grid_search.fit(X_train, y_train)
best_rf = grid_search.best_estimator_
rf_mse = mean_squared_error(y_val, best_rf.predict(X_val))
print(f" Best RF MSE: {rf_mse:.4f}")
print(f" Best Settings Found: {grid_search.best_params_}")

# 5save the best one
os.makedirs("models", exist_ok=True)
#
if lr_mse <= rf_mse:
    print(f"Linear Regression won (MSE: {lr_mse:.4f}). Saving LR...")
    joblib.dump(lr, "models/model.pkl")
    winner_name = "Linear Regression"
else:
    print(f"Random Forest won (MSE: {rf_mse:.4f}). Saving RF...")
    joblib.dump(best_rf, "models/model.pkl")
    winner_name = "Random Forest"

# save some data on the reporst to check future difference between models
metrics = {
  "winning_model": winner_name,
    "linear_regression_mse": lr_mse,
    "logistic_accuracy": log_acc,
    "random_forest_best_params": grid_search.best_params_,
    "random_forest_mse": rf_mse
}
with open("models/metrics.json", "w") as f:
    json.dump(metrics, f)

print("\n DONE! Model and metrics saved in /models")