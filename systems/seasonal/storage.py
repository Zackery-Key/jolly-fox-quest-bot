import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

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
