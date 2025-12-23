from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import os

from .models import WanderingEvent

DATA_DIR = "/mnt/data"
os.makedirs(DATA_DIR, exist_ok=True)

WANDERING_FILE = os.path.join(DATA_DIR, "wandering_event.json")

DEFAULT_WANDERING_STATE = {
    "active": None
}

def _ensure_file_exists():
    WANDERING_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not WANDERING_FILE.exists():
        WANDERING_FILE.write_text(
            json.dumps(DEFAULT_WANDERING_STATE, indent=2),
            encoding="utf-8",
        )

def save_active_event(event: Optional[WanderingEvent]) -> None:
    _ensure_file_exists()


def _dt_to_str(dt: datetime) -> str:
    # store UTC ISO
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _str_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def save_active_event(event: Optional[WanderingEvent]) -> None:
    WANDERING_FILE.parent.mkdir(parents=True, exist_ok=True)
    if event is None:
        WANDERING_FILE.write_text(json.dumps({"active": None}, indent=2), encoding="utf-8")
        return

    payload = {
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
    WANDERING_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_active_event() -> Optional[WanderingEvent]:
    if not WANDERING_FILE.exists():
        return None
    raw = json.loads(WANDERING_FILE.read_text(encoding="utf-8"))
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
        required_participants=int(active["required_participants"]),
        faction_reward=int(active["faction_reward"]),
        global_reward=int(active["global_reward"]),
        player_reward=int(active["player_reward"]),
        participants=set(active.get("participants", [])),
        participating_factions=set(active.get("participating_factions", [])),
        resolved=bool(active.get("resolved", False)),
    )
