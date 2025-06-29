import pandas as pd
import os
from engine.effects import parse_effect_column

def load_data():
    pokemon_df = pd.read_csv("./db/mons.csv")
    moves_df = pd.read_csv("./db/moves.csv")
    pokemon_df.fillna("-", inplace=True)

    move_info_df = moves_df[['Name', 'Type', 'Power', 'Dice', 'Boni 1', 'Boni 2', 'Boni 3']].copy()
    move_info_df.columns = ['Move Name', 'Type', 'Power', 'Dice', 'Bonus 1', 'Bonus 2', 'Bonus 3']
    move_info_df['Effect'] = move_info_df.apply(parse_effect_column, axis=1)

    # Include 'Move Name' in the final dictionary entries
    move_info_df = move_info_df[['Move Name', 'Type', 'Power', 'Dice', 'Effect']].drop_duplicates(subset=['Move Name'])
    move_lookup = move_info_df.set_index('Move Name').to_dict(orient='index')
    for name in move_lookup:
        move_lookup[name]['Move Name'] = name  # <- inject key into the value

    return pokemon_df, move_lookup

def load_type_effectiveness_matrix(path="./db/type_chart.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Matrix file not found at: {path}")
    return pd.read_csv(path, sep=';', index_col=0)
