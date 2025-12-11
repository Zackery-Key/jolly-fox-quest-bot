from dataclasses import dataclass, field
from typing import Dict


@dataclass
class QuestBoard:
    season_id: str = "default_season"
    global_points: int = 0

    # NEW — per-faction scoring bucket
    faction_points: Dict[str, int] = field(default_factory=dict)

    # For persistent board message
    display_channel_id: int | None = None
    message_id: int | None = None

    def add_points(self, amount: int):
        self.global_points += amount

    def add_faction_points(self, faction_id: str, amount: int):
        if faction_id is None:
            return  # skip users without a faction
        self.faction_points[faction_id] = self.faction_points.get(faction_id, 0) + amount

    def reset_season(self, new_season_id: str):
        self.season_id = new_season_id
        self.global_points = 0
        self.faction_points = {}  # Reset faction totals each season
