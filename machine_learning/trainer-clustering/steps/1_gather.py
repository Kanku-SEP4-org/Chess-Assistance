import pandas as pd
import numpy as np
import os

def generate_advanced_mock_data(n=200):
    np.random.seed(42)
    data = {
        'avg_lumen': np.random.uniform(200, 2000, n),
        'avg_celsius': np.random.uniform(18, 26, n),
        'avg_ppm': np.random.uniform(400, 2000, n),
        'avg_ml': np.random.uniform(0, 1000, n),
        'sleep_duration': [f"{np.random.randint(4, 10)} hours {np.random.randint(0, 60)} minutes" for _ in range(n)],
        'eco_code': np.random.choice(['A00', 'B20', 'C50', 'D30', 'E60'], n),
        'total_ply': np.random.randint(20, 120, n),
        'opening_ply': np.random.randint(5, 25, n),
        'player_move_count': np.random.randint(10, 60, n),
        'opponent_move_count': np.random.randint(10, 60, n),
        'time_control': np.random.choice(['blitz', 'rapid', 'classical'], n),
        'is_time_increase': np.random.choice([True, False], n),
        'time_increase_sec': np.random.randint(0, 30, n),
        'is_berserk': np.random.choice([True, False], n),
        'duration_min': np.random.randint(1, 30, n),
        'user_rating': np.random.randint(1200, 2800, n),
        'opp_rating': np.random.randint(1200, 2800, n),
        'rating_diff': np.random.randint(-300, 300, n),
        'is_player_piece_black': np.random.choice([True, False], n),
        'termination_type': np.random.choice(['Normal', 'Time Forfeit', 'Resignation'], n),
        'result': np.random.choice(['Win', 'Loss', 'Draw'], n, p=[0.45, 0.45, 0.1]),
        'player_opening_win_rate': np.random.uniform(0.3, 0.7, n),
        'player_opening_game_count': np.random.randint(1, 1000, n)
    }
    return pd.DataFrame(data)

df = generate_advanced_mock_data()