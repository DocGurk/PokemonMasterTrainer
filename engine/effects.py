import re
import numpy as np
import pandas as pd
import random
from collections import defaultdict

RED_DICE = 6
BONI_COLS = ['Bonus 1', 'Bonus 2', 'Bonus 3']

regex_on = re.compile(r"(.+?)\s+on\s+(\d+)\+")
regex_plus = re.compile(r"(.+?)\s*\+\s*(\d+)")

def split_effects(cell):
    return re.split(r'[;,·]', cell)

def translate_super_effect(effect_name: str) -> list:
    """
    Translates 'Super Something' into [Something, Something].
    All other names return as-is in a 1-item list.
    """
    if effect_name.lower().startswith("super "):
        base = effect_name[6:].strip()
        return [base, base]
    return [effect_name]

def parse_effect_column(row):
    effects = defaultdict(list)

    for col in BONI_COLS:
        cell = row[col]
        if pd.isna(cell) or str(cell).strip() == '-':
            continue

        for entry in split_effects(str(cell)):
            entry = entry.strip()
            if not entry:
                continue

            if match := regex_on.match(entry):
                status, num = match.groups()
                for translated in translate_super_effect(status.strip()):
                    effects[translated].append(int(num))
            elif match := regex_plus.match(entry):
                status, num = match.groups()
                for translated in translate_super_effect(status.strip()):
                    effects[translated].append(int(num))
            else:
                for translated in translate_super_effect(entry):
                    effects[translated].append(0)

    return dict(effects) if effects else np.nan

def decide_effects(effect_dict, log, modifiers=None):
    """
    Rolls 1dRED_DICE and checks which effects are triggered.

    Args:
        effect_dict: {str: list[int]} — thresholds per effect
        log: list — receives battle log messages
        modifiers: {str: int}, optional — additive modifiers per effect

    Returns:
        set of triggered effect names
    """
    triggered = []

    for effect, thresholds in effect_dict.items():
        for t in thresholds:
            red_roll = random.randint(1, RED_DICE)
            threshold = t
            if red_roll >= threshold:
                log.append(f"🎲 {effect.upper()} roll: {red_roll} ≥ {threshold} → ✅ Triggered!")
                triggered.append(effect)
                break  # One trigger is enough
            else:
                log.append(f"🎲 {effect.upper()} roll: {red_roll} < {threshold} → ❌ Failed")

    return triggered

def apply_status_to_move(pokemon, effect, log, move_data):
    """
    Applies a status to the target Pokémon using the effect name and move context.

    Args:
        pokemon: the target Pokémon
        effect: string, e.g. 'sleep', 'paralyze', 'burn'
        log: list to append logs
        move_data: dict containing the move's properties
    """
    if pokemon.status:
        log.append(f"{pokemon.name} is already affected by {pokemon.status}.")
        return False

    pokemon.status = effect
    pokemon.counters[effect] = 0  # always initialize

    move_name = move_data.get("Name", "Unknown Move")

    if effect == "sleep":
        roll = random.randint(1, 4)
        duration = max(1, roll - 1)
        pokemon.counters["sleep"] = duration
        log.append(f"{pokemon.name} is put to sleep for {duration} turns by {move_name}!")

    elif effect == "paralyze":
        log.append(f"{pokemon.name} is paralyzed by {move_name}!")
        # No counters needed unless you want advanced stacking

    elif effect == "burn":
        log.append(f"{pokemon.name} is burned by {move_name}!")
        # Maybe reduce burn severity if move power is low

    elif effect == "poison":
        log.append(f"{pokemon.name} is poisoned by {move_name}!")
        # Counter starts at 0; will grow via upkeep

    else:
        pokemon.status = None
        log.append(f"{pokemon.name} is affected by {effect} from {move_name}.")

    return True

def apply_effects(pokemon, log, effect_library):
    """
    Apply status effects to a Pokémon.

    Args:
        pokemon: the active Pokémon object
        log: list to append battle log messages
        effect_library: dict mapping effect names to behavior dicts

    Effects may include:
        - upkeep: function(mon, log)
        - mod_current_turn: {stat: value}
        - mod_next_turn: {stat: value}
    """
    pokemon.active_modifiers = {}  # Reset current modifiers

    for effect in pokemon.status_effects:
        effect_def = effect_library.get(effect, {})

        # 🔁 Upkeep effects (e.g. take damage)
        if "upkeep" in effect_def:
            try:
                effect_def["upkeep"](pokemon, log)
            except Exception as e:
                log.append(f"⚠️ Error in {effect} upkeep: {e}")

        # 🎯 Modifiers for current turn
        mod_now = effect_def.get("mod_current_turn", {})
        for stat, val in mod_now.items():
            pokemon.active_modifiers[stat] = pokemon.active_modifiers.get(stat, 0) + val
            log.append(f"{pokemon.name} gets {stat:+} this turn from {effect}!")

        # 🧠 Modifiers queued for next turn
        mod_next = effect_def.get("mod_next_turn", {})
        for stat, val in mod_next.items():
            pokemon.next_turn_modifiers[stat] = pokemon.next_turn_modifiers.get(stat, 0) + val
            log.append(f"{pokemon.name} will get {stat:+} next turn from {effect}.")

    # Apply next turn modifiers to this turn (carry-over)
    if pokemon.next_turn_modifiers:
        for stat, val in pokemon.next_turn_modifiers.items():
            pokemon.active_modifiers[stat] = pokemon.active_modifiers.get(stat, 0) + val
            log.append(f"{pokemon.name} gains {stat:+} from last turn carry-over.")
        pokemon.next_turn_modifiers = {}  # Clear carry-over
