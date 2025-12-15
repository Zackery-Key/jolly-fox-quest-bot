import os
import json

DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

SEASON_FILE = os.path.join(DATA_DIR, "seasonal_event.json")

DEFAULT_SEASON_STATE = {
    "active": False,
    "day": 1,
    "date": "",
    "boss": {
        "name": "Doom Fox",
        "hp": 5000,
        "max_hp": 5000,
        "phase": 1,
        "avatar_url": "https://media.discordapp.net/attachments/1446565189142052945/1450232045044367513/658f559f6a24dd96c89aa09030a41b48.png?ex=6941c957&is=694077d7&hm=a3a48b6a696f5cce060e294da6f1fc3c780c806bd27fc34d62e45057f610ff31&=&format=webp&quality=lossless&width=839&height=839"
    },
    "votes": {
        "shieldborne": {
            "attack": [],
            "defend": [],
            "heal": []
        },
        "spellfire": {
            "attack": [],
            "defend": [],
            "heal": []
        },
        "verdant": {
            "attack": [],
            "defend": [],
            "heal": []
        }
    },
    "embed": {
        "channel_id": None,
        "message_id": None
    }
}


def load_season():
    if not os.path.exists(SEASON_FILE):
        # 🔹 First run: create the file
        with open(SEASON_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SEASON_STATE, f, indent=4)

    with open(SEASON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert vote lists → sets
    for faction in data["votes"]:
        for action in data["votes"][faction]:
            data["votes"][faction][action] = set(
                data["votes"][faction][action]
            )

    return data


def save_season(state: dict):
    serializable = state.copy()

    serializable["votes"] = {
        faction: {
            action: list(users)
            for action, users in actions.items()
        }
        for faction, actions in state["votes"].items()
    }

    with open(SEASON_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=4)
