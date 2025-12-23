from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set


@dataclass
class WanderingEvent:
    event_id: str
    channel_id: int
    message_id: Optional[int]
    ends_at: datetime
    duration_minutes: int

    title: str
    description: str
    difficulty: str
    required_participants: int

    faction_reward: int
    global_reward: int
    player_reward: int

    participants: Set[int] = field(default_factory=set)          # user_ids
    participating_factions: Set[str] = field(default_factory=set) # "shieldborne", etc.
    resolved: bool = False
