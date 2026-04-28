import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler

#load data
df = pd.read_csv("data/mock_data.csv")
#remove acidental spaces??
df.columns = df.columns.str.strip().str.lower()

#features
#debug for hidden carachters
if df.columns[0].endswith('temperature'):
    df.rename(columns={df.columns[0]: 'temperature'}, inplace=True)


# df['sleep_hours'] = df['sleep'] / 60

co2_norm = (df['co2'] - 400) / 1600
temp_dist = abs(df['temperature'] - 20)
df['env_score'] = 1 - (co2_norm * 0.7 + (temp_dist / 5)* 0.3)

# 1 is win, 0 is either draw or loss 
df['target'] = 0.0
df.loc[df['user_won'],  'target'] = 1.0


#Selecting and scaling
#I'm dropping elo_diff because this use case relies on before-game data
features = ['minutes_slept','minutes_awake','env_score', 'light']
X = df[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

df_final = pd.DataFrame(X_scaled, columns=features)
df_final['target'] = df['target'].values

os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)
df_final.to_csv("data/features.csv", index=False)
joblib.dump(scaler, "models/scaler.pkl")

print(f"Features saved to data/features.csv. Shape: {df_final.shape}")