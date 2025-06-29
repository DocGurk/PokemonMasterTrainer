import re
import random

def roll_dice(dice_str):
    match = re.match(r"(\d+)D(\d+)", dice_str.upper())
    if not match:
        return 0
    num, sides = map(int, match.groups())
    return sum(random.randint(1, sides) for _ in range(num))

def calculate_move_damage(move, target_types, effectiveness_matrix, effects):
    try:
        power = int(move['Power']) if move['Power'] and str(move['Power']).isdigit() else 0
    except:
        power = 0
    dice = move.get('Dice', '0D0')
    damage_roll = roll_dice(dice)
    move_type = move['Type']

    # Sum effectiveness against all target types
    effectiveness_total = sum(
        effectiveness_matrix.get(move_type.strip(), {}).get(t, 0)
        for t in target_types if t
    )

    total = power + damage_roll + effectiveness_total
    eff_details = '+'.join(str(effectiveness_matrix.get(move_type, {}).get(t, 0)) for t in target_types if t)

    log = f"{move['Move Name']} → Power: {power} + Roll({dice}) + Eff({eff_details}) = {total}"
    return total, log

