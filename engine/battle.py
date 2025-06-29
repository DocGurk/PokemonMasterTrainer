import random
from engine.damage import calculate_move_damage
from engine.effects import decide_effects

MAX_HP = 3

class Pokemon:
    def __init__(self, row):
        self.data = row
        self.name = row["Name"]
        self.hp = MAX_HP
        self.moves = [row["Move 1"], row["Move 2"], row["Mega Move"]]
        self.status_effects = []
        self.misc_effects = []
        self.attach = None
        self.types = [t for t in [row["Type 1"], row["Type 2"]] if t]


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

def battle_round(player_party, ai_party, move_lookup, type_chart):
    log = []
    player_mon = player_party.active
    ai_mon = ai_party.active

    # Choose moves
    player_move = random.choice([m for m in player_mon.moves if m != "-"])
    ai_move = random.choice([m for m in ai_mon.moves if m != "-"])

    # Damage
    player_data = move_lookup.get(player_move)
    ai_data = move_lookup.get(ai_move)

    player_dmg, player_log = calculate_move_damage(player_data, ai_mon.types, type_chart, None)
    ai_dmg, ai_log = calculate_move_damage(ai_data, player_mon.types, type_chart, None)

    if player_dmg > ai_dmg:
        ai_mon.hp -= 1
        result = f"{ai_mon.name} loses 1 HP!"
    elif ai_dmg > player_dmg:
        player_mon.hp -= 1
        result = f"{player_mon.name} loses 1 HP!"
    else:
        result = "It's a tie!"

    log.extend([
        f"{player_mon.name} used {player_move} → {player_log}",
        f"{ai_mon.name} used {ai_move} → {ai_log}",
        result
    ])

    return log

def is_battle_over(player_party, ai_party):
    return not player_party.has_available() or not ai_party.has_available()
