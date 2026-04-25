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
    
        temp = random.randint(18, 22)
        
        co2 = random.randint(800, 2000)
        
        light = random.randint(1000, 2000)
        
        water = random.randint(0, 5)
        
        sleep = random.randint(240, 600)
        
        current_elo = random.randint(1750, 2750)
        opponent_elo = random.randint(1750, 2750)
        
        result_choice = random.choice(['black', 'white', 'draw'])
        win_black = 1 if result_choice == 'black' else 0
        win_white = 1 if result_choice == 'white' else 0
        draw = 1 if result_choice == 'draw' else 0
        
        data.append([
            temp, co2, light, water, sleep, 
            current_elo, opponent_elo, 
            win_black, win_white, draw
        ])

    columns = [
        'temperature ', 'CO2', 'Light', 'Water', 'Sleep', 
        'current ELO', 'opponent ELO', 'Win black ', 'win white', 'Draw '
    ]
    
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_rows} rows at: {output_path}")

if __name__ == "__main__":
    generate_mock_chess_data(num_rows=100)