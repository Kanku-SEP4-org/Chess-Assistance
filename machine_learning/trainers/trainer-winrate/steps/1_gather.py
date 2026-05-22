import pandas as pd
import numpy as np
import os

def generate_mock_chess_data(num_rows=100, output_path='data/mock_data.csv'):
    if not os.path.exists('data'):
        os.makedirs('data')

    temp = np.random.normal(loc=20, scale=1.2, size=num_rows)
    temp = np.clip(temp, 18, 22).astype(int)

    co2 = np.random.normal(loc=1200, scale=300, size=num_rows)
    co2 = np.clip(co2, 400, 2100).astype(int)

    light = np.random.normal(loc=1500, scale=200, size=num_rows)
    light = np.clip(light, 800, 2000).astype(int)

    water = np.random.poisson(lam=2, size=num_rows)
    water = np.clip(water, 0, 6)

    minutes_slept = np.random.normal(loc=450, scale=60, size=num_rows)
    minutes_slept = np.clip(minutes_slept, 240, 600).astype(int)

    minutes_awake = np.random.normal(loc=450, scale=60, size=num_rows)
    minutes_awake = np.clip(minutes_awake, 1, 1020).astype(int)

    current_elo = np.random.normal(loc=2250, scale=200, size=num_rows).astype(int)
    opponent_elo = np.random.normal(loc=2250, scale=200, size=num_rows).astype(int)

    user_won = np.random.randint(0, 2, size=num_rows)


    df = pd.DataFrame({
        'temperature ': temp,
        'CO2': co2,
        'Light': light,
        'Water': water,
        'Minutes_Slept': minutes_slept,
        'Minutes_Awake': minutes_awake,
        'current ELO': current_elo,
        'opponent ELO': opponent_elo,
        'user_won': user_won
    })

    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_rows} rows at: {output_path}")

if __name__ == "__main__":
    generate_mock_chess_data(num_rows=100)