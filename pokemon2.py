import tkinter as tk  # You can remove this if not using it
import random
import pandas as pd
import os
import pygame
import re
import numpy as np

# ---------- Data Loading ----------
import re
RED_DICE = 6
BONI_COLS = ['Bonus 1', 'Bonus 2', 'Bonus 3']
keywords = {}
def load_data():
    pokemon_df = pd.read_csv("./db/mons/mons.csv")
    moves_df = pd.read_csv("./db/moves/moves.csv")
    pokemon_df.fillna("-", inplace=True)

    move_info_df = moves_df[['Name', 'Type', 'Power', 'Dice', 'Boni 1', 'Boni 2', 'Boni 3']].copy()
    move_info_df['Effect'] = None
    pattern = r'([a-zA-Z]+) on (\d+)'

    move_info_df = moves_df[['Name', 'Type', 'Power', 'Dice', 'Boni 1', 'Boni 2', 'Boni 3']].copy()
    move_info_df.columns = ['Move Name', 'Type', 'Power', 'Dice', 'Bonus 1', 'Bonus 2', 'Bonus 3']
    # Patterns

    regex_on = re.compile(r"(.+?)\s+on\s+(\d+)\+")
    regex_plus = re.compile(r"(.+?)\s*\+\s*(\d+)")
    def split_effects(cell):
        # Split by common separators
        return re.split(r'[;,·]', cell)

    def parse_effects(row):
        effects = {}
        for col in BONI_COLS:
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '-':
                continue

            entries = split_effects(str(cell))
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                # Match "Confuse on 3+" or similar
                match_on = regex_on.match(entry)
                if match_on:
                    status, num = match_on.groups()
                    effects[status.strip()] = int(num)
                    continue

                # Match "Power + 2"
                match_plus = regex_plus.match(entry)
                if match_plus:
                    status, num = match_plus.groups()
                    effects[status.strip()] = int(num)
                    continue

                # Default catch-all
                effects[entry] = RED_DICE + 1

        return effects if effects else np.nan

    # Apply vectorized logic
    move_info_df['Effect'] = move_info_df.apply(parse_effects, axis=1)

    # Now reduce to relevant columns and build lookup
    move_info_df = move_info_df[['Move Name', 'Type', 'Power', 'Dice', 'Effect']].drop_duplicates(subset=['Move Name'])
    move_lookup = move_info_df.set_index('Move Name').to_dict(orient='index')

    return pokemon_df, move_lookup

def load_type_effectiveness_matrix(path="./db/type_effectiveness_matrix.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Matrix file not found at: {path}")
    return pd.read_csv(path, sep=';', index_col=0)


# ---------- Utility Functions ----------

def format_move(move_name):
    if move_name == "-" or not move_name.strip():
        return f"{move_name} (No data)"
    info = move_lookup.get(move_name.strip(), {})
    if not info:
        return f"{move_name} (No details found)"
    return (f"{move_name}\n"
            f"Type: {info['Type']} | Power: {info['Power']} | Dice: {info['Dice']}\n")

def roll_dice(dice_str):
    match = re.match(r"(\d+)D(\d+)", dice_str.upper())
    if not match:
        return 0
    num, sides = map(int, match.groups())
    return sum(random.randint(1, sides) for _ in range(num))


# ---------- Battle Logic ----------

def calculate_move_damage(move_name, target_type1, target_type2=None, effectiveness_matrix=None):
    move = move_lookup.get(move_name, {})
    if not move:
        return 0, "Invalid move"

    power = int(move['Power']) if pd.notna(move['Power']) and str(move['Power']).isdigit() else 0
    dice = move['Dice'] if pd.notna(move['Dice']) else '0D0'
    damage_roll = roll_dice(dice)
    move_type = move['Type']
    eff1 = eff2 = 0

    if effectiveness_matrix is not None:
        try:
            eff1 = effectiveness_matrix.loc[move_type, target_type1] if target_type1 in effectiveness_matrix.columns else 0
            eff2 = effectiveness_matrix.loc[move_type, target_type2] if target_type2 and target_type2 in effectiveness_matrix.columns else 0
        except KeyError:
            pass

    effectiveness = eff1 + eff2
    total_output = power + damage_roll + effectiveness
    breakdown = (f"{move_name} → Power: {power} + Roll({dice}) = {power}+{damage_roll}+{effectiveness} = {total_output}\n"
                 f"Type: {move_type} vs {target_type1}" + (f"/{target_type2}" if target_type2 else "") +
                 f" → Effectiveness: {eff1} + {eff2} = {effectiveness}")
    return total_output, breakdown
# Add an 'Effect' column based on pattern matching
def roll_status_effects(effects: dict, target: pd.Series) -> dict:
    """
    Applies status effects based on d6 rolls. Returns a dict of applied effects.

    Args:
        effects (dict): status → threshold (e.g., {'Burn': 3})
        target (pd.Series): Pokémon to apply effects to

    Returns:
        dict: applied_effects (e.g., {'Burn': True, 'Flinch': True})
    """
    applied_effects = {}
    if not effects or not isinstance(effects, dict):
        return applied_effects

    # Ensure status_effects exists
    if 'status_effects' not in target or not isinstance(target.get('status_effects'), dict):
        target['status_effects'] = {}

    for status, threshold in effects.items():
        try:
            threshold = int(threshold)
            roll = random.randint(1, 6)
            if roll >= threshold:
                target['status_effects'][status] = True
                applied_effects[status] = True
        except (ValueError, TypeError):
            continue
    print(applied_effects)
    return applied_effects
def run_single_exchange_battle(player_row, pokemon_df, move_lookup):
    move_buttons = []
    battle_log = []
    move_selected = False
    outcome = 0  # Default to tie

    screen = pygame.display.get_surface()
    WIDTH, HEIGHT = screen.get_size()
    FONT = pygame.font.SysFont('Arial', 20)
    WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
    clock = pygame.time.Clock()
    active = True

    while active:
        screen.fill(WHITE)
        title = FONT.render(f"{player_row['Name']} vs {ai_row['Name']}", True, BLACK)
        screen.blit(title, (20, 20))

        if not move_selected:
            move_buttons.clear()
            for i, col in enumerate(['Move 1', 'Move 2', 'Mega Move']):
                move_name = player_row[col]
                if move_name == "-":
                    continue
                rect = pygame.Rect(20, 60 + i * 60, 200, 50)
                pygame.draw.rect(screen, GRAY, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)
                text = FONT.render(move_name, True, BLACK)
                screen.blit(text, (rect.x + 10, rect.y + 15))
                move_buttons.append((rect, move_name))
        else:
            for i, line in enumerate(battle_log):
                log_text = FONT.render(line, True, BLACK)
                screen.blit(log_text, (20, 120 + i * 30))
            done_text = FONT.render("Click anywhere to return", True, (100, 0, 0))
            screen.blit(done_text, (20, 280))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not move_selected:
                    mx, my = event.pos
                    for rect, move_name in move_buttons:
                        if rect.collidepoint(mx, my):
                            ai_type1 = ai_row['Type 1']
                            ai_type2 = ai_row['Type 2']
                            player_type1 = player_row['Type 1']
                            player_type2 = player_row['Type 2']

                            # Player move
                            player_roll, player_log = calculate_move_damage(move_name, ai_type1, ai_type2, type_chart)

                            # AI move
                            ai_move = random.choice([m for m in [ai_row['Move 1'], ai_row['Move 2'], ai_row['Mega Move']] if m != "-"])
                            ai_roll, ai_log = calculate_move_damage(ai_move, player_type1, player_type2, type_chart)

                            # Determine outcome
                            if player_roll > ai_roll:
                                outcome = 1
                            elif player_roll < ai_roll:
                                outcome = -1
                            else:
                                outcome = 0

                            battle_log = [
                                f"You used {player_log}",
                                f"Foe used {ai_log}"
                            ]
                            move_selected = True
                            break
                else:
                    active = False
        roll_status_effects()
        pygame.display.flip()
        clock.tick(30)

    return outcome, status

def run_multi_round_battle(player_row,ai_row, move_lookup):
    player_hp = ai_hp = 3
    battle_log = []
    round_num = 1

    screen = pygame.display.get_surface()
    WIDTH, HEIGHT = screen.get_size()
    FONT = pygame.font.SysFont('Arial', 20)
    WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
    clock = pygame.time.Clock()
    active = True
    game_over = False

    def get_effects(move_name):
        move = move_lookup.get(move_name, {})
        return move.get('Effect', {}) if move else {}

    def apply_effects(effects, target_name):
        effect_log = []
        if not effects or not isinstance(effects, dict):
            return effect_log  # Handle None or non-dict input gracefully

        for status, level in effects.items():
            try:
                level = int(level)
                chance = 100 // level if level != 0 else 0
                if random.randint(1, 100) <= chance:
                    effect_log.append(f"{target_name} is affected by {status}!")
            except (ValueError, TypeError):
                continue  # Skip malformed effects
        return effect_log

    while active:
        screen.fill(WHITE)
        title = FONT.render(f"{player_row['Name']} (HP: {player_hp}) vs {ai_row['Name']} (HP: {ai_hp})", True, BLACK)
        screen.blit(title, (20, 20))

        if game_over:
            for i, line in enumerate(battle_log[-10:]):
                log_text = FONT.render(line, True, BLACK)
                screen.blit(log_text, (20, 60 + i * 30))
            result = "YOU WIN!" if ai_hp <= 0 else "YOU LOSE!" if player_hp <= 0 else "DRAW!"
            result_text = FONT.render(result + " - Click to return", True, (100, 0, 0))
            screen.blit(result_text, (20, 400))
        else:
            # Draw move buttons
            for i, col in enumerate(['Move 1', 'Move 2', 'Mega Move']):
                move_name = player_row[col]
                if move_name == "-":
                    continue
                rect = pygame.Rect(20, 60 + i * 60, 200, 50)
                pygame.draw.rect(screen, GRAY, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)
                text = FONT.render(move_name, True, BLACK)
                screen.blit(text, (rect.x + 10, rect.y + 15))

            # Show battle log
            for i, line in enumerate(battle_log[-10:]):
                log_text = FONT.render(line, True, BLACK)
                screen.blit(log_text, (250, 60 + i * 25))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    active = False  # exit battle
                else:
                    mx, my = event.pos
                    for i, col in enumerate(['Move 1', 'Move 2', 'Mega Move']):
                        rect = pygame.Rect(20, 60 + i * 60, 200, 50)
                        if rect.collidepoint(mx, my):
                            move_name = player_row[col]
                            ai_move = random.choice([m for m in [ai_row['Move 1'], ai_row['Move 2'], ai_row['Mega Move']] if m != "-"])

                            # Damage rolls
                            ai_type1, ai_type2 = ai_row['Type 1'], ai_row['Type 2']
                            player_dmg, player_log = calculate_move_damage(move_name, ai_type1, ai_type2, type_chart)

                            player_type1, player_type2 = player_row['Type 1'], player_row['Type 2']
                            ai_dmg, ai_log = calculate_move_damage(ai_move, player_type1, player_type2, type_chart)

                            # Apply damage
                            if player_dmg > ai_dmg:
                                ai_hp -= 1
                                outcome = "You win the exchange!"
                            elif player_dmg < ai_dmg:
                                player_hp -= 1
                                outcome = "You lose the exchange!"
                            else:
                                outcome = "It's a tie!"

                            # Apply effects
                            effects_log = []
                            effects_log += apply_effects(get_effects(move_name), ai_row['Name'])
                            effects_log += apply_effects(get_effects(ai_move), player_row['Name'])

                            battle_log.append(f"--- Round {round_num} ---")
                            battle_log.append(f"You used {player_log}")
                            battle_log.append(f"Foe used {ai_log}")
                            battle_log.append(outcome)
                            battle_log.extend(effects_log)

                            round_num += 1
                            if player_hp <= 0 or ai_hp <= 0:
                                game_over = True
                            break

        pygame.display.flip()
        clock.tick(30)

    # Final result
    if player_hp > ai_hp:
        return 1
    elif player_hp < ai_hp:
        return -1
    else:
        return 0
# ---------- Main App ----------

# Load data
pokemon_df, move_lookup = load_data()
type_chart = load_type_effectiveness_matrix()

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokémon Team Viewer")

FONT = pygame.font.SysFont('Arial', 20)
BIGFONT = pygame.font.SysFont('Arial', 26)

WHITE, BLACK, GRAY, BLUE = (255, 255, 255), (0, 0, 0), (200, 200, 200), (100, 100, 255)

# Select 6 Pokémon
selected_pokemon = pokemon_df.sample(n=6).reset_index(drop=True)
chips = [ (pygame.Rect(50, 50 + i * 60, 200, 50), row['Name'], row) for i, row in selected_pokemon.iterrows() ]

# Main loop
running = True
selected_moves = ""
while running:
    screen.fill(WHITE)

    for rect, name, row in chips:
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        text = FONT.render(name, True, BLACK)
        screen.blit(text, (rect.x + 10, rect.y + 15))

    y_offset = 20
    for line in selected_moves.splitlines():
        rendered = FONT.render(line, True, BLUE)
        screen.blit(rendered, (300, y_offset))
        y_offset += 25

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for rect, name, row in chips:
                if rect.collidepoint(mx, my):
                    # Example: pick a random AI Pokémon and run the battle
                    ai_row = pokemon_df.sample(1).iloc[0]
                    result = run_multi_round_battle(row, ai_row, move_lookup)

    pygame.display.flip()

pygame.quit()
