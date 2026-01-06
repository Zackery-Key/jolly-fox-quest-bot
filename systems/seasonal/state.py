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
BOSS_RETALIATION_PER_ATTACK = 5
DEFENSE_RETALIATION_REDUCTION = 4

# One-time power effects
SPELLFIRE_GLOBAL_MULTIPLIER = 1.75   # multiplies ALL damage for the day
VERDANT_MASS_HEAL_PCT = 0.25         # heal all factions 25% max


def get_season_state():
    state = load_season()
    if not state:
        raise RuntimeError("Seasonal event file missing")
    return state


def reset_votes_for_new_day(state: dict):
    today = str(date.today())

    if state["date"] == today:
        return

    state["date"] = today

    for faction in state["votes"]:
        for action in state["votes"][faction]:
            state["votes"][faction][action].clear()

    save_season(state)


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

def resolve_daily_boss(state: dict) -> dict:
    """
    Resolve one day's votes into:
    - boss HP damage (attack - defense)
    - boss retaliation damage to faction health
    - healing to faction health
    - optional one-time faction powers (if majority voted and unlocked+unused)

    Returns a summary dict (useful for logging).
    """
    votes = state.get("votes", {})
    boss = state.get("boss", {})
    faction_health = state.get("faction_health", {})
    powers = state.get("faction_powers", {})

    # -----------------------------
    # Tally votes (global + per faction)
    # -----------------------------
    total_attack = 0
    total_defend = 0
    total_heal = 0

    bonus_attack = 0
    bonus_defense = 0
    bonus_heal = 0

    per_faction_counts: dict[str, dict[str, int]] = {}

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

        # Passive bonuses only for that faction’s matching action
        if faction_id == "spellfire":
            bonus_attack += atk * SPELLFIRE_ATTACK_BONUS
        if faction_id == "shieldborne":
            bonus_defense += dfn * SHIELDBORNE_DEFENSE_BONUS
        if faction_id == "verdant":
            bonus_heal += heal * VERDANT_HEAL_BONUS

    # -----------------------------
    # Determine power activations (majority vote)
    # -----------------------------
    used_today: list[str] = []

    def can_use(fid: str) -> bool:
        fp = powers.get(fid, {})
        return bool(fp.get("unlocked")) and not bool(fp.get("used"))

    shieldborne_blocks_retaliation = False
    verdant_mass_heal = False
    spellfire_global_amp = False

    # Shieldborne
    if can_use("shieldborne") and _faction_majority_voted_power(state, "shieldborne"):
        shieldborne_blocks_retaliation = True
        powers["shieldborne"]["used"] = True
        used_today.append("shieldborne")

    # Verdant
    if can_use("verdant") and _faction_majority_voted_power(state, "verdant"):
        verdant_mass_heal = True
        powers["verdant"]["used"] = True
        used_today.append("verdant")

    # Spellfire
    if can_use("spellfire") and _faction_majority_voted_power(state, "spellfire"):
        spellfire_global_amp = True
        powers["spellfire"]["used"] = True
        used_today.append("spellfire")

    # -----------------------------
    # Compute combat values
    # -----------------------------
    raw_damage = (total_attack * BASE_ATTACK_DAMAGE) + bonus_attack
    defense = (total_defend * BASE_DEFENSE_REDUCTION) + bonus_defense
    healing_total = (total_heal * BASE_HEAL) + bonus_heal

    if spellfire_global_amp:
        raw_damage = int(raw_damage * SPELLFIRE_GLOBAL_MULTIPLIER)

    net_damage = max(0, raw_damage - defense)

    # Apply boss damage
    boss_hp_before = int(boss.get("hp", 0))
    boss["hp"] = max(0, boss_hp_before - net_damage)

    # Boss retaliation (hurts faction health)
    retaliation = max(
        0,
        (total_attack * BOSS_RETALIATION_PER_ATTACK)
        - (total_defend * DEFENSE_RETALIATION_REDUCTION)
    )

    if shieldborne_blocks_retaliation:
        retaliation_applied = 0
    else:
        retaliation_applied = retaliation
        for fid, fh in faction_health.items():
            fh["hp"] = max(0, int(fh.get("hp", 0)) - retaliation_applied)

    # Healing distributes evenly to all factions
    healed_each = 0
    if faction_health:
        healed_each = healing_total // len(faction_health)
        for fid, fh in faction_health.items():
            fh["hp"] = min(int(fh.get("max_hp", 0)), int(fh.get("hp", 0)) + healed_each)

    # Verdant mass heal: +25% max to all factions
    if verdant_mass_heal:
        for fid, fh in faction_health.items():
            add = int(int(fh.get("max_hp", 0)) * VERDANT_MASS_HEAL_PCT)
            fh["hp"] = min(int(fh.get("max_hp", 0)), int(fh.get("hp", 0)) + add)

    return {
        "boss_hp_before": boss_hp_before,
        "boss_hp_after": boss["hp"],
        "raw_damage": raw_damage,
        "defense": defense,
        "net_damage": net_damage,
        "retaliation": retaliation_applied,
        "healing_total": healing_total,
        "healed_each": healed_each,
        "powers_used": used_today,
        "per_faction": per_faction_counts,
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


