import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split

# 2. PREPROCESSING FUNCTIONS
def preprocess_chess_data(df):
    # Convert sleep_duration (INTERVAL) to float hours
    # This is a simple regex/split approach for the mock format
    def parse_sleep(s):
        parts = s.split()
        return float(parts[0]) + float(parts[2])/60.0
    
    df_proc = df.copy()
    df_proc['sleep_hours'] = df_proc['sleep_duration'].apply(parse_sleep)
    
    # Target: 1 for Win, 0 for everything else
    df_proc['target'] = (df_proc['result'] == 'Win').astype(int)
    
    return df_proc

def main() -> None:
    raw_path = os.getenv("RAW_DATA_PATH", "data/raw.csv")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Missing raw dataset: {raw_path}")

    df = pd.read_csv(raw_path)
    df_cleaned = preprocess_chess_data(df)

    # Define feature groups
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

    X = df_cleaned[env_cols + game_cols + cat_cols]
    y = df_cleaned['target']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    os.makedirs("data", exist_ok=True)
    train_path = os.getenv("TRAIN_DATA_PATH", "data/train.csv")
    test_path = os.getenv("TEST_DATA_PATH", "data/test.csv")

    train_df = X_train.copy()
    train_df["target"] = y_train.values
    test_df = X_test.copy()
    test_df["target"] = y_test.values

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    print(f"Saved train split: {train_path} ({len(train_df)} rows)")
    print(f"Saved test split:  {test_path} ({len(test_df)} rows)")


if __name__ == "__main__":
    main()

