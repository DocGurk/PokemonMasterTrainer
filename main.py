from data.loader import load_data, load_type_effectiveness_matrix
from ui.game_ui import start_game
import pygame

if __name__ == "__main__":
    pygame.init()
    pokemon_df, move_lookup = load_data()
    type_chart = load_type_effectiveness_matrix()
    start_game(pokemon_df, move_lookup, type_chart)
