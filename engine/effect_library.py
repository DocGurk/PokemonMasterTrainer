import random

def poison_upkeep(mon, log):
    mon.counters["poison"] = mon.counters.get("poison", 0) + 1
    log.append(f"{mon.name} gains a poison counter ({mon.counters['poison']} total).")

    # For every 3 poison counters, reduce max and current HP by 1 (min 1 HP)
    total = mon.counters["poison"]
    poison_damage = total // 3
    if poison_damage > 0:
        new_max_hp = max(1, mon.max_hp - poison_damage)
        hp_loss = mon.hp - new_max_hp
        mon.max_hp = new_max_hp
        mon.hp = min(mon.hp, mon.max_hp)
        log.append(f"{mon.name} is weakened by poison! Max HP reduced to {mon.max_hp}.")
        if hp_loss > 0:
            log.append(f"{mon.name} loses {hp_loss} HP due to poison strain.")

def burn_mod():
    return {"mod_current_turn": {"damage": -1}}

def sleep_upkeep(mon, log):
    if mon.counters.get("sleep", 0) > 0:
        mon.counters["sleep"] -= 1
        log.append(f"{mon.name} has {mon.counters['sleep']} sleep counters left.")
        if mon.counters["sleep"] == 0:
            log.append(f"{mon.name} wakes up!")

def sleep_mod(mon):
    if mon.counters.get("sleep", 0) > 0:
        return {"mod_current_turn": {"move_strength": -999}}  # Silences all attacks
    return {}

# EFFECT LIBRARY

EFFECT_LIBRARY = {
    "poison": {
        "upkeep": poison_upkeep
    },
    "burn": {
        **burn_mod()
    },
    "sleep": {
        "upkeep": sleep_upkeep,
        # mod_current_turn will be dynamic based on counter state
        # handled in apply_effects(pokemon, log, EFFECT_LIBRARY)
    }
}
