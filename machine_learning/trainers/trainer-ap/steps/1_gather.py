import os
import pandas as pd

DATA_PATH = "data/processed_player_data_v2.csv"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Raw data not found at '{DATA_PATH}'. "
        "Download processed_player_data_v2.csv and place it in the data/ directory."
    )

df = pd.read_csv(DATA_PATH)

print(f"Loaded: {DATA_PATH}")
print(f"Shape:  {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"\nTarget (player_centipawn_loss) stats:")
print(df["player_centipawn_loss"].describe().to_string())
print(f"\nMissing values per column:")
missing = df.isnull().sum()
missing = missing[missing > 0]
if missing.empty:
    print("  None")
else:
    print(missing.to_string())
