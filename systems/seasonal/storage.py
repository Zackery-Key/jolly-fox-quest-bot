import os
import json

DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

SEASON_FILE = os.path.join(DATA_DIR, "seasonal_event.json")

DEFAULT_SEASON_STATE = {
    "active": False,
    "day": 1,
    "date": "",
    "difficulty": "normal",
    "boss_type": "seasonal",
    "boss": {
        "name": "Doom Fox",
        "hp": 1,
        "max_hp": 1,
        "avatar_url": "..."
    },
    "votes": {
        "shieldborne": {
            "attack": [],
            "defend": [],
            "heal": [],
            "power": []   
        },
        "spellfire": {
            "attack": [],
            "defend": [],
            "heal": [],
            "power": []   
        },
        "verdant": {
            "attack": [],
            "defend": [],
            "heal": [],
            "power": []   
        }
    },

    "faction_health": {          
        "shieldborne": {"hp": 1000, "max_hp": 1000},
        "spellfire":   {"hp": 1000, "max_hp": 1000},
        "verdant":     {"hp": 1000, "max_hp": 1000},
    },

    "faction_powers": {
        "shieldborne": {"unlocked": False, "used": False},
        "spellfire":   {"unlocked": False, "used": False},
        "verdant":     {"unlocked": False, "used": False}
    },

    "embed": {"channel_id": None, "message_id": None}
}



def load_season():
    if not os.path.exists(SEASON_FILE):
        # 🔹 First run: create the file
        with open(SEASON_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SEASON_STATE, f, indent=4)

    with open(SEASON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
            # -----------------------------
    # 🔧 Auto-migrate missing keys
    # -----------------------------
    data.setdefault("faction_powers", DEFAULT_SEASON_STATE["faction_powers"])
    data.setdefault("faction_health", DEFAULT_SEASON_STATE["faction_health"])
    data.setdefault("boss", DEFAULT_SEASON_STATE["boss"])
    data.setdefault("votes", DEFAULT_SEASON_STATE["votes"])
    data.setdefault("embed", DEFAULT_SEASON_STATE["embed"])
    data.setdefault("alive_factions", [])
    data["alive_factions"] = set(data["alive_factions"])


    # Ensure each faction has expected vote buckets (including "power")
    for faction_id, default_actions in DEFAULT_SEASON_STATE["votes"].items():
        data["votes"].setdefault(faction_id, {})
        for action in default_actions.keys():
            data["votes"][faction_id].setdefault(action, [])

    # Convert vote lists → sets
    for faction in data["votes"]:
        for action in data["votes"][faction]:
            data["votes"][faction][action] = set(
                data["votes"][faction][action]
            )

    return data


def save_season(state: dict):
    serializable = state.copy()
    serializable["alive_factions"] = list(state.get("alive_factions", []))

    serializable["votes"] = {
        faction: {
            action: list(users)
            for action, users in actions.items()
        }
        for faction, actions in state["votes"].items()
    }

    with open(SEASON_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=4)
