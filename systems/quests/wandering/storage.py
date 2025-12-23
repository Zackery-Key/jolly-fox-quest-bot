import os
import json
from typing import Optional
from datetime import datetime

from .models import WanderingEvent

# -------------------------------------------------
# Base paths (Persistent on Railway)
# -------------------------------------------------
DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

WANDERING_FILE = os.path.join(DATA_DIR, "wandering_event.json")

DEFAULT_WANDERING_STATE = {
    "active": None
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _ensure_file_exists():
    if not os.path.exists(WANDERING_FILE):
        with open(WANDERING_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_WANDERING_STATE, f, indent=4)


def _dt_to_str(dt: datetime) -> str:
    return dt.isoformat()


def _str_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


# -------------------------------------------------
# Load / Save
# -------------------------------------------------
def load_active_event() -> Optional[WanderingEvent]:
    _ensure_file_exists()

    with open(WANDERING_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    active = raw.get("active")
    if not active:
        return None

    return WanderingEvent(
        event_id=active["event_id"],
        channel_id=active["channel_id"],
        message_id=active.get("message_id"),
        ends_at=_str_to_dt(active["ends_at"]),
        title=active["title"],
        description=active["description"],
        difficulty=active["difficulty"],
        required_participants=active["required_participants"],
        faction_reward=active["faction_reward"],
        global_reward=active["global_reward"],
        player_reward=active["player_reward"],
        participants=set(active.get("participants", [])),
        participating_factions=set(active.get("participating_factions", [])),
        resolved=active.get("resolved", False),
    )


def save_active_event(event: Optional[WanderingEvent]) -> None:
    _ensure_file_exists()

    if event is None:
        with open(WANDERING_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_WANDERING_STATE, f, indent=4)
        return

    data = {
        "active": {
            "event_id": event.event_id,
            "channel_id": event.channel_id,
            "message_id": event.message_id,
            "ends_at": _dt_to_str(event.ends_at),
            "title": event.title,
            "description": event.description,
            "difficulty": event.difficulty,
            "required_participants": event.required_participants,
            "faction_reward": event.faction_reward,
            "global_reward": event.global_reward,
            "player_reward": event.player_reward,
            "participants": list(event.participants),
            "participating_factions": list(event.participating_factions),
            "resolved": event.resolved,
        }
    }

    with open(WANDERING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
