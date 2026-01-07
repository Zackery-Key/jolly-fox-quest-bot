from datetime import date
from .storage import load_season, save_season

# ========= Seasonal Combat Constants =========
BASE_ATTACK_DAMAGE = 10
BASE_DEFENSE_REDUCTION = 6
BASE_HEAL = 8

# Passive faction identity bonuses (only when that faction votes that action)
SHIELDBORNE_DEFENSE_BONUS = 4      # per Shieldborne defend vote
SPELLFIRE_ATTACK_BONUS = 6         # per Spellfire attack vote
VERDANT_HEAL_BONUS = 6             # per Verdant heal vote

# Boss retaliation model
BASE_RETALIATION = 30              # always hurts, even with low votes
RETALIATION_PER_5_ATTACKS = 10     # spike pressure for aggression
DEFEND_REDUCTION = 4               # per defend vote


# One-time power effects
SPELLFIRE_GLOBAL_MULTIPLIER = 1.75   # multiplies ALL damage for the day
VERDANT_MASS_HEAL_PCT = 0.25         # heal all factions 25% max


def get_season_state():
    state = load_season()
    if not state:
        raise RuntimeError("Seasonal event file missing")
    return state


def reset_votes_for_new_day(state: dict, force: bool = False):
    """
    Reset all faction votes.
    - Normal mode: once per UTC day
    - force=True: always reset (admin/manual resolve)
    """
    today = str(date.today())

    if not force and state.get("date") == today:
        return

    state["date"] = today

    for faction in state.get("votes", {}):
        for action in state["votes"][faction]:
            state["votes"][faction][action].clear()


def register_vote(state: dict, user_id: int, faction: str, action: str):
    if faction not in state["votes"]:
        return False

    if action not in state["votes"][faction]:
        return False

    # 🔒 Remove existing vote for this faction
    for a in state["votes"][faction]:
        state["votes"][faction][a].discard(user_id)

    # ✅ Add new vote
    state["votes"][faction][action].add(user_id)

    save_season(state)
    return True

def _faction_majority_voted_power(state: dict, faction_id: str) -> bool:
    """
    Majority within that faction's votes (attack/defend/heal/power) chooses power.
    """
    fv = state["votes"].get(faction_id, {})
    if not fv:
        return False

    power_votes = len(fv.get("power", []))
    total_votes = (
        len(fv.get("attack", [])) +
        len(fv.get("defend", [])) +
        len(fv.get("heal", [])) +
        len(fv.get("power", []))
    )

    return total_votes > 0 and power_votes > (total_votes / 2)

import random

def resolve_daily_boss(state: dict) -> dict:
    votes = state.get("votes", {})
    boss = state.get("boss", {})
    faction_health = state.get("faction_health", {})
    powers = state.get("faction_powers", {})

    # -----------------------------
    # Tally votes
    # -----------------------------
    total_attack = 0
    total_defend = 0
    total_heal = 0

    bonus_attack = 0
    bonus_defense = 0
    bonus_heal = 0

    per_faction_counts = {}

    for faction_id, actions in votes.items():
        atk = len(actions.get("attack", []))
        dfn = len(actions.get("defend", []))
        heal = len(actions.get("heal", []))
        pwr = len(actions.get("power", []))

        per_faction_counts[faction_id] = {
            "attack": atk, "defend": dfn, "heal": heal, "power": pwr
        }

        total_attack += atk
        total_defend += dfn
        total_heal += heal

        if faction_id == "spellfire":
            bonus_attack += atk * SPELLFIRE_ATTACK_BONUS
        if faction_id == "shieldborne":
            bonus_defense += dfn * SHIELDBORNE_DEFENSE_BONUS
        if faction_id == "verdant":
            bonus_heal += heal * VERDANT_HEAL_BONUS

    # -----------------------------
    # Power activation
    # -----------------------------
    used_today = []

    def can_use(fid: str) -> bool:
        return powers.get(fid, {}).get("unlocked") and not powers.get(fid, {}).get("used")

    shieldborne_blocks = False
    verdant_mass_heal = False
    spellfire_amp = False

    if can_use("shieldborne") and _faction_majority_voted_power(state, "shieldborne"):
        shieldborne_blocks = True
        powers["shieldborne"]["used"] = True
        used_today.append("shieldborne")

    if can_use("verdant") and _faction_majority_voted_power(state, "verdant"):
        verdant_mass_heal = True
        powers["verdant"]["used"] = True
        used_today.append("verdant")

    if can_use("spellfire") and _faction_majority_voted_power(state, "spellfire"):
        spellfire_amp = True
        powers["spellfire"]["used"] = True
        used_today.append("spellfire")

    # -----------------------------
    # Boss damage
    # -----------------------------
    raw_damage = (total_attack * BASE_ATTACK_DAMAGE) + bonus_attack
    defense = (total_defend * BASE_DEFENSE_REDUCTION) + bonus_defense

    if spellfire_amp:
        raw_damage = int(raw_damage * SPELLFIRE_GLOBAL_MULTIPLIER)

    net_damage = max(0, raw_damage - defense)

    boss_hp_before = int(boss.get("hp", 0))
    boss["hp"] = max(0, boss_hp_before - net_damage)

    # -----------------------------
    # Boss retaliation (FIXED)
    # -----------------------------
    retaliation = BASE_RETALIATION
    retaliation += (total_attack // 5) * RETALIATION_PER_5_ATTACKS
    retaliation -= total_defend * DEFEND_REDUCTION
    retaliation = max(0, retaliation)

    retaliation_target = None
    retaliation_applied = 0

    if not shieldborne_blocks and retaliation > 0 and faction_health:
        # Weighted toward lowest HP faction
        targets = list(faction_health.items())
        targets.sort(key=lambda x: x[1]["hp"])

        weights = [len(targets) - i for i in range(len(targets))]
        retaliation_target, fh = random.choices(targets, weights=weights, k=1)[0]

        fh["hp"] = max(0, fh["hp"] - retaliation)
        retaliation_applied = retaliation

    # -----------------------------
    # Healing (SMART)
    # -----------------------------
    healing_pool = (total_heal * BASE_HEAL) + bonus_heal

    for _, fh in sorted(faction_health.items(), key=lambda x: x[1]["hp"]):
        if healing_pool <= 0:
            break

        missing = fh["max_hp"] - fh["hp"]
        if missing <= 0:
            continue

        applied = min(missing, healing_pool)
        fh["hp"] += applied
        healing_pool -= applied

    if verdant_mass_heal:
        for fh in faction_health.values():
            fh["hp"] = min(
                fh["max_hp"],
                fh["hp"] + int(fh["max_hp"] * VERDANT_MASS_HEAL_PCT)
            )

    # -----------------------------
    # END CONDITIONS
    # -----------------------------

    all_factions_defeated = all(
        fh["hp"] <= 0 for fh in faction_health.values()
    )

    boss_defeated = boss["hp"] <= 0

    if all_factions_defeated:
        state["active"] = False
        state["ended_reason"] = "factions_defeated"

    elif boss_defeated:
        state["active"] = False
        state["ended_reason"] = "boss_defeated"

    return {
        "boss_hp_before": boss_hp_before,
        "boss_hp_after": boss["hp"],
        "retaliation_target": retaliation_target,
        "powers_used": used_today,
        "ended": not state.get("active"),
        "ended_reason": state.get("ended_reason"),
    }

def reset_season_state(state: dict):
    """
    Safely reset the seasonal state without deleting the file.
    """
    state["active"] = False
    state["day"] = 1
    state["date"] = ""

    # Reset boss
    boss = state.get("boss", {})
    boss["hp"] = boss.get("max_hp", 1)
    boss["phase"] = 1

    # Clear votes
    for faction in state.get("votes", {}):
        for action in state["votes"][faction]:
            state["votes"][faction][action].clear()

    # Reset faction health
    for fh in state.get("faction_health", {}).values():
        fh["hp"] = fh.get("max_hp", fh.get("hp", 1))

    # Reset power usage (unlock stays!)
    for fp in state.get("faction_powers", {}).values():
        fp["used"] = False


