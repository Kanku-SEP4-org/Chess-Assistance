import os
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("data/processed_player_data_v2.csv")

# Drop the same columns as in AP_02
df = df.drop(columns=[
    "Game ID",
    "player_username",
    "opponent_username",
    "time_control",
    "time_control_encoded",
    "opponent_centipawn_loss",
])

# Flag players whose rating profile is partially missing
rating_cols          = ["player_rapid_rating",   "player_blitz_rating",   "player_bullet_rating"]
opponent_rating_cols = ["opponent_rapid_rating", "opponent_blitz_rating", "opponent_bullet_rating"]

df["player_profile_disabled"]   = df[rating_cols].isnull().any(axis=1).astype(int)
df["opponent_profile_disabled"] = df[opponent_rating_cols].isnull().any(axis=1).astype(int)

X = df.drop(columns=["player_centipawn_loss"])
y = df["player_centipawn_loss"]

X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

train_val = X_train_val.copy()
train_val["player_centipawn_loss"] = y_train_val.values

test = X_test.copy()
test["player_centipawn_loss"] = y_test.values

os.makedirs("data", exist_ok=True)
train_val.to_csv("data/train_val.csv", index=False)
test.to_csv("data/test.csv", index=False)

print(f"train_val saved to data/train_val.csv. Shape: {train_val.shape}")
print(f"test saved to data/test.csv. Shape: {test.shape}")
