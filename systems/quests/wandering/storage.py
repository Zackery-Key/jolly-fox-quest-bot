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
def load_active_event():
    if not os.path.exists(WANDERING_FILE):
        return None

    try:
        with open(WANDERING_FILE, "r") as f:
            data = json.load(f)

        # ⛑️ Normalize old / partial schemas
        return WanderingEvent(
            event_id=data.get("event_id"),
            channel_id=data.get("channel_id"),
            message_id=data.get("message_id"),
            duration_minutes=data.get("duration_minutes", 0),
            ends_at=datetime.fromisoformat(data["ends_at"]),
            title=data.get("title", "Unknown Threat"),
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "minor"),
            required_participants=data.get("required_participants", 1),
            faction_reward=data.get("faction_reward", 0),
            global_reward=data.get("global_reward", 0),
            xp_reward=data.get("xp_reward", 0),
            participants=set(data.get("participants", [])),
            participating_factions=set(data.get("participating_factions", [])),
            resolved=data.get("resolved", False),
            image=data.get("image"),
        )

    except Exception as e:
        # 🚨 Corrupt or incompatible save → self-heal
        print(f"[WANDERING] Failed to load active event, clearing: {e}")
        save_active_event(None)
        return None




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
            "participants": list(event.participants),
            "participating_factions": list(event.participating_factions),
            "resolved": event.resolved,
            "image": event.image,
        }
    }

    with open(WANDERING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
