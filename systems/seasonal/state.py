from datetime import date
from .storage import load_season, save_season


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
