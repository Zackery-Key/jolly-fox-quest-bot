from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class QuestBoard:
    season_id: str = "default_season"
    global_points: int = 0

    # NEW — per-faction scoring
    faction_points: Dict[str, int] = field(default_factory=dict)

    # Where the scoreboard message lives (for refresh)
    display_channel_id: Optional[int] = None
    message_id: Optional[int] = None

    def add_points(self, amount: int):
        self.global_points += amount

    def add_faction_points(self, faction_id: str, amount: int):
        """Increase points for a specific faction."""
        if not faction_id:
            return  # no faction → no faction bucket
        self.faction_points[faction_id] = self.faction_points.get(faction_id, 0) + amount

    def reset_season(self, new_season_id: str):
        self.season_id = new_season_id
        self.global_points = 0
        self.faction_points = {}
