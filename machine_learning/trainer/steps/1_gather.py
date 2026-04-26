import pandas as pd
import numpy as np
import os
import random

def generate_mock_chess_data(num_rows=100, output_path='data/mock_data.csv'):
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created 'data' folder.")

    data = []
    
    for _ in range(num_rows):
    
        temperature = random.randint(18, 22)
        
        co2 = random.randint(800, 2000)
        
        light = random.randint(1000, 2000)
        
        water = random.randint(0, 5)
        
        minutes_slept = random.randint(240, 600)

        minutes_awake = random.randint(10, 720)
        
        current_elo = random.randint(1750, 2750)
        opponent_elo = random.randint(1750, 2750)
        
        result_choice = random.choice(['black', 'white', 'draw'])
        win_black = 1 if result_choice == 'black' else 0
        win_white = 1 if result_choice == 'white' else 0
        draw = 1 if result_choice == 'draw' else 0
        
        data.append([
            temperature, co2, light, water, minutes_slept, minutes_awake,
            current_elo, opponent_elo, 
            win_black, win_white, draw
        ])

    columns = [
        'temperature', 'co2', 'light', 'water', 'minutes_slept',
        'minutes_awake', 
        'current ELO', 'opponent ELO', 'Win black ', 'win white', 'Draw '
    ]
    
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_rows} rows at: {output_path}")

if __name__ == "__main__":
    generate_mock_chess_data(num_rows=100)