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

def decide_effects(effect_dict, red_roll, modifiers=None):
    """
    Args:
        effect_dict: {str: list[int]} — multiple thresholds per effect
        red_roll: int
        modifiers: {str: int}, optional

    Returns:
        set of triggered effect names
    """
    triggered = set()
    modifiers = modifiers or {}

    for effect, thresholds in effect_dict.items():
        mod = modifiers.get(effect, 0)
        for t in thresholds:
            if red_roll >= t + mod:
                triggered.add(effect)
                break  # one trigger is enough

    return triggered
