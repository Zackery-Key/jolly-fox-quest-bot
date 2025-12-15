import os
import json

DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

SEASON_FILE = os.path.join(DATA_DIR, "seasonal_event.json")


def load_season():
    if not os.path.exists(SEASON_FILE):
        raise FileNotFoundError(f"Missing seasonal file: {SEASON_FILE}")

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
