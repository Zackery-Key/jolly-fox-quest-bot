from dataclasses import dataclass, field
from typing import List


@dataclass
class InventoryItem:
    quest_id: str
    item_name: str
    collected: bool = True


@dataclass
class PlayerState:
    user_id: int
    daily_quest: dict = field(default_factory=dict)
    inventory: List[InventoryItem] = field(default_factory=list)

    # NEW STATS
    lifetime_completed: int = 0
    season_completed: int = 0
    xp: int = 0
    level: int = 1

    def to_dict(self):
        """Convert PlayerState to JSON-compatible dict."""
        return {
            "user_id": self.user_id,
            "daily_quest": self.daily_quest,
            "inventory": [
                {
                    "quest_id": item.quest_id,
                    "item_name": item.item_name,
                    "collected": item.collected
                }
                for item in self.inventory
            ],
            "lifetime_completed": self.lifetime_completed,
            "season_completed": self.season_completed,
            "xp": self.xp,
            "level": self.level,
        }

    @staticmethod
    def from_dict(data: dict):
        ps = PlayerState(
            user_id=data.get("user_id", 0),
            daily_quest=data.get("daily_quest", {})
        )

        # Load stats safely
        ps.lifetime_completed = data.get("lifetime_completed", 0)
        ps.season_completed = data.get("season_completed", 0)
        ps.xp = data.get("xp", 0)
        ps.level = data.get("level", 1)

        # Load inventory
        for item in data.get("inventory", []):
            ps.inventory.append(
                InventoryItem(
                    quest_id=item.get("quest_id"),
                    item_name=item.get("item_name"),
                    collected=item.get("collected", True)
                )
            )

        return ps
