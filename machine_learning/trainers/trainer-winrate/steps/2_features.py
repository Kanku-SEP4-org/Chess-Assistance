import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split

df = pd.read_csv("data/mock_data.csv")
df.columns = df.columns.str.strip().str.lower()

if df.columns[0].endswith('temperature'):
    df.rename(columns={df.columns[0]: 'temperature'}, inplace=True)

co2_norm = (df['co2'] - 400) / 1600
temp_dist = abs(df['temperature'] - 20)
df['env_score'] = 1 - (co2_norm * 0.7 + (temp_dist / 5) * 0.3)

# 1 is win, 0 is either draw or loss
df['target'] = df['user_won']

# I'm dropping elo_diff because this use case relies on before-game data
# Scaling is left to the training pipeline so the scaler is fit only on
# train data — fitting here would leak test statistics.
features = ['minutes_slept', 'minutes_awake', 'env_score', 'light']
df_final = df[features].copy()
df_final['target'] = df['target'].values

train_val, test = train_test_split(df_final, test_size=0.2, random_state=42, shuffle=True)

os.makedirs("data", exist_ok=True)
train_val.to_csv("data/train_val.csv", index=False)
test.to_csv("data/test.csv", index=False)

print(f"train_val saved to data/train_val.csv. Shape: {train_val.shape}")
print(f"test saved to data/test.csv.      Shape: {test.shape}")
