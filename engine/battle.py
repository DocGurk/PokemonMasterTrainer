import random
from engine.damage import calculate_move_damage
from engine.effects import decide_effects, apply_effects, apply_status_to_move
from engine.effect_library import EFFECT_LIBRARY

MAX_HP = 3

class Pokemon:
    def __init__(self, row):
        self.data = row
        self.name = row["Name"]
        self.hp = MAX_HP
        self.max_hp = MAX_HP
        self.moves = [row["Move 1"], row["Move 2"], row["Mega Move"]]
        self.status = None
        self.effects = []
        self.attach = None
        self.active_modifiers = {}        # turn-specific
        self.next_turn_modifiers = {}     # queued for next
        self.types = [t for t in [row["Type 1"], row["Type 2"]] if t]
        self.counters = {} 


    def is_fainted(self):
        return self.hp <= 0

class Party:
    def __init__(self, pokemons):
        self.pokemons = [Pokemon(row) for row in pokemons]
        self.active_index = 0

    @property
    def active(self):
        return self.pokemons[self.active_index]

    def has_available(self):
        return any(not mon.is_fainted() for mon in self.pokemons)

    def switch_to_next(self):
        for i, mon in enumerate(self.pokemons):
            if not mon.is_fainted():
                self.active_index = i
                return True
        return False
def trigger_upkeep_effects(player_party, ai_party, effect_library, log):
    """
    Triggers upkeep effects for both active Pokémon at the start of a round.

    Args:
        player_party: Party object
        ai_party: Party object
        effect_library: global EFFECT_LIBRARY dict
        log: list to append log messages
    """
    for party, label in [(player_party, "You"), (ai_party, "Foe")]:
        mon = party.active
        if not mon.status:
            continue

        effect = mon.status
        effect_def = EFFECT_LIBRARY.get(effect, {})
        if "upkeep" in effect_def:
            log.append(f"🔁 {label}'s {mon.name} is affected by {effect}!")
            try:
                effect_def["upkeep"](mon, log)
            except Exception as e:
                log.append(f"⚠️ Error during {effect} upkeep on {mon.name}: {e}")

def battle_round(player_party, ai_party, move_lookup, type_chart, player_move):
    log = []
    player_mon = player_party.active
    ai_mon = ai_party.active

    # Choose AI move
    ai_move = random.choice([m for m in ai_mon.moves if m != "-"])

    # Get move data
    player_data = move_lookup.get(player_move)
    ai_data = move_lookup.get(ai_move)

    # Trigger effects from player move → apply to AI mon
    if player_data["Effect"]:
        triggered = decide_effects(player_data["Effect"], log)
    for effect in triggered:
        apply_status_to_move(ai_mon, effect, log, player_data)
    if player_data["Effect"]:
        triggered = decide_effects(ai_data["Effect"], log)
    for effect in triggered:
        apply_status_to_move(player_mon, effect, log, ai_data)

    # Calculate damage
    player_dmg, player_log = calculate_move_damage(player_data, ai_mon.types, type_chart, player_mon.active_modifiers)
    ai_dmg, ai_log = calculate_move_damage(ai_data, player_mon.types, type_chart, ai_mon.active_modifiers)

    # Resolve outcome
    if player_dmg > ai_dmg:
        ai_mon.hp -= 1
        result = f"{ai_mon.name} loses 1 HP!"
    elif ai_dmg > player_dmg:
        player_mon.hp -= 1
        result = f"{player_mon.name} loses 1 HP!"
    else:
        result = "It's a tie!"

    # Log everything
    log.extend([
        f"{player_mon.name} used {player_move} → {player_log}",
        f"{ai_mon.name} used {ai_move} → {ai_log}",
        result
    ])

    return log

def is_battle_over(player_party, ai_party):
    return not player_party.has_available() or not ai_party.has_available()


def prepare_battle(player_party, ai_party):
    """Returns log intro + info needed to show party selection."""
    log = []
    log.append("🎮 A wild battle begins!")
    log.append("Both teams reveal their lineups!")
    log.append(f"🧠 Opponent sends out {ai_party.active.name}!")

    # Don't auto-send player mon — let UI decide
    return log
def start_battle(player_party, ai_party):
    """Returns who goes first and a log message list for the intro."""
    log = []
    log.append("🎮 A wild battle begins!")
    log.append(f"🧠 Opponent sends out {ai_party.active.name}!")
    log.append(f"➡️ You send out {player_party.active.name}!")

    # Random for now — you could later make this a GUI selection
    #player_first = random.choice([True, False])
    player_first = False
    starter = "You" if player_first else "Opponent"
    log.append(f"{starter} will go first!")

    return player_first, log

