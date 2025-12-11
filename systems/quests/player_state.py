from dataclasses import dataclass, field
from typing import List, Dict


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

    # REQUIRED FIELD (needed for faction scoring, quest profile, scoreboard)
    faction_id: str | None = None

    # NEW STATS
    lifetime_completed: int = 0
    season_completed: int = 0
    xp: int = 0
    level: int = 1

    # -----------------------------------------------------
    # Inventory Helpers (FETCH quest support)
    # -----------------------------------------------------
    def has_item_for_quest(self, quest_id: str) -> bool:
        return any(item.quest_id == quest_id and item.collected for item in self.inventory)

    def add_item(self, quest_id: str, item_name: str):
        self.inventory.append(
            InventoryItem(
                quest_id=quest_id,
                item_name=item_name,
                collected=True
            )
        )

    def consume_item_for_quest(self, quest_id: str):
        self.inventory = [
            item for item in self.inventory
            if not (item.quest_id == quest_id and item.collected)
        ]

    # -----------------------------------------------------
    # Leveling System
    # -----------------------------------------------------
    @property
    def next_level_xp(self) -> int:
        return self.level * 20

    @property
    def xp_progress(self) -> float:
        needed = self.next_level_xp
        return min(self.xp / needed, 1.0) if needed > 0 else 0.0

    def add_xp(self, amount: int) -> bool:
        leveled = False
        self.xp += amount

        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            leveled = True

        return leveled

    # -----------------------------------------------------
    # Serialization → JSON
    # -----------------------------------------------------
    def to_dict(self):
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
            "faction_id": self.faction_id,
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
            daily_quest=data.get("daily_quest", {}),
        )

        # Load stats safely
        ps.faction_id = data.get("faction_id")  # <-- RESTORED
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
