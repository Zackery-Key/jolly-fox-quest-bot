from datetime import date
from .storage import load_season, save_season

# ========= Seasonal Combat Constants =========
BASE_ATTACK_DAMAGE = 10
BASE_DEFENSE_REDUCTION = 6
BASE_HEAL = 8
ESCULATION_PER_DAY = {
    "minor": 4,      # gentle ramp
    "seasonal": 7,   # sharper ramp
}

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

DIFFICULTY_PRESETS = {
    "easy": {
        "boss_hp_multiplier": 0.75,
        "base_retaliation": 20,
        "retaliation_per_5_attacks": 6,
        "faction_hp_multiplier": 1.2,
    },
    "normal": {
        "boss_hp_multiplier": 1.0,
        "base_retaliation": 30,
        "retaliation_per_5_attacks": 10,
        "faction_hp_multiplier": 1.0,
    },
    "hard": {
        "boss_hp_multiplier": 1.3,
        "base_retaliation": 40,
        "retaliation_per_5_attacks": 15,
        "faction_hp_multiplier": 0.85,
    },
}

def sync_power_unlocks_from_board(state, board):
    for faction_id in state["faction_powers"]:
        points = board.faction_points.get(faction_id, 0)
        state["faction_powers"][faction_id]["unlocked"] = (
            points >= board.faction_goal
        )

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

    # Snapshot which factions are alive at start of day
    state["alive_factions"] = {
        fid
        for fid, fh in state.get("faction_health", {}).items()
        if fh["hp"] > 0
    }



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
    total_votes = 0

    bonus_attack = 0
    bonus_defense = 0
    bonus_heal = 0

    per_faction_counts = {}

    for faction_id, actions in votes.items():
        atk = len(actions.get("attack", []))
        dfn = len(actions.get("defend", []))
        heal = len(actions.get("heal", []))
        pwr = len(actions.get("power", []))

        # Power votes also count as the faction's default action
        default_action = {
            "spellfire": "attack",
            "shieldborne": "defend",
            "verdant": "heal",
        }.get(faction_id)

        eff_atk, eff_dfn, eff_heal = atk, dfn, heal
        if default_action == "attack":
            eff_atk += pwr
        elif default_action == "defend":
            eff_dfn += pwr
        elif default_action == "heal":
            eff_heal += pwr

        total_votes += atk + dfn + heal + pwr

        per_faction_counts[faction_id] = {
            "attack": atk, "defend": dfn, "heal": heal, "power": pwr,
            "eff_attack": eff_atk, "eff_defend": eff_dfn, "eff_heal": eff_heal,
        }

        total_attack += eff_atk
        total_defend += eff_dfn
        total_heal += eff_heal

        # Passive bonuses apply to the effective action totals
        if faction_id == "spellfire":
            bonus_attack += eff_atk * SPELLFIRE_ATTACK_BONUS
        if faction_id == "shieldborne":
            bonus_defense += eff_dfn * SHIELDBORNE_DEFENSE_BONUS
        if faction_id == "verdant":
            bonus_heal += eff_heal * VERDANT_HEAL_BONUS


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
    difficulty = state.get("difficulty", "normal")
    preset = DIFFICULTY_PRESETS[difficulty]

    retaliation = preset["base_retaliation"]
    retaliation += (total_votes // 5) * preset["retaliation_per_5_attacks"]
    retaliation -= total_defend * DEFEND_REDUCTION
    retaliation = max(0, retaliation)
    boss_type = state.get("boss_type", "seasonal")
    day = int(state.get("day", 1))

    esculation = ESCULATION_PER_DAY.get(boss_type, 7) * max(0, day - 1)
    retaliation += esculation

    retaliation_target = None
    retaliation_applied = 0


    if not shieldborne_blocks and retaliation > 0:
        targets = [
            (fid, fh)
            for fid, fh in faction_health.items()
            if fh["hp"] > 0
        ]

        if not targets:
            retaliation_target = None
        else:
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
        "net_damage": net_damage,              # ✅ add
        "raw_damage": raw_damage,              # optional but helpful
        "defense": defense,                    # optional but helpful
        "retaliation_target": retaliation_target,
        "retaliation_applied": retaliation_applied,   # ✅ add
        "powers_used": used_today,
        "ended": not state.get("active"),
        "ended_reason": state.get("ended_reason"),
    }

def reset_season_state(state: dict):
    state["active"] = False
    state["day"] = 1
    state["date"] = ""

    # ✅ Clear season metadata / summary stats
    state["ended_reason"] = None
    state["started_on"] = ""
    state["last_net_damage"] = 0
    state["last_retaliation"] = 0

    # Reset boss
    boss = state.get("boss", {})
    boss["hp"] = boss.get("max_hp", 1)

    # Clear votes
    for faction in state.get("votes", {}):
        for action in state["votes"][faction]:
            state["votes"][faction][action].clear()

    # Reset faction health
    for fh in state.get("faction_health", {}).values():
        fh["hp"] = fh.get("max_hp", fh.get("hp", 1))

    # ✅ Everyone alive again (important for voting lockout)
    state["alive_factions"] = {
        fid for fid, fh in state.get("faction_health", {}).items() if fh["hp"] > 0
    }

    # Reset power usage (unlock stays!)
    for fp in state.get("faction_powers", {}).values():
        fp["used"] = False


