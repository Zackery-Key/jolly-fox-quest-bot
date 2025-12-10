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

    # -----------------------------------------------------
    # Inventory Helpers (needed for FETCH quests)
    # -----------------------------------------------------
    def has_item_for_quest(self, quest_id: str) -> bool:
        """Return True if the player has collected the item for the given quest."""
        return any(
            item.quest_id == quest_id and item.collected
            for item in self.inventory
        )

    def add_item(self, quest_id: str, item_name: str):
        """Add an item to the player's quest inventory."""
        self.inventory.append(
            InventoryItem(
                quest_id=quest_id,
                item_name=item_name,
                collected=True
            )
        )

    def consume_item_for_quest(self, quest_id: str):
        """Remove the quest item from inventory after turn-in."""
        self.inventory = [
            item for item in self.inventory
            if not (item.quest_id == quest_id and item.collected)
        ]

    # -----------------------------------------------------
    # Serialization → JSON
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # Load from JSON
    # -----------------------------------------------------
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
