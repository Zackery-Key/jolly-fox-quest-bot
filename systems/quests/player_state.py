from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PlayerState:
    user_id: int
    daily_quest: dict = field(default_factory=dict)

    # Inventory is a dict: {item_name: quantity}
    inventory: Dict[str, int] = field(default_factory=dict)

    faction_id: str | None = None
    lifetime_completed: int = 0
    season_completed: int = 0
    xp: int = 0
    level: int = 1
    badges: set[str] = field(default_factory=set)
    season_victories: set[str] = field(default_factory=set)
    title: str | None = None

    # -----------------------------------------------------
    # Inventory Helpers (FETCH quest support)
    # -----------------------------------------------------
    def has_item_for_quest(self, item_name: str) -> bool:
        """Return True if player has at least 1 of the item."""
        return self.inventory.get(item_name, 0) > 0

    def add_item(self, item_name: str):
        """Give the player 1 copy of an item."""
        self.inventory[item_name] = self.inventory.get(item_name, 0) + 1

    def consume_item(self, item_name: str):
        """Remove 1 copy of an item."""
        if item_name in self.inventory:
            self.inventory[item_name] -= 1
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]


    # -----------------------------------------------------
    # Leveling System
    # -----------------------------------------------------
    @property
    def next_level_xp(self) -> int:
        return 100 + (self.level - 1) * 50

    @property
    def xp_progress(self) -> float:
        needed = self.next_level_xp
        return min(self.xp / needed, 1.0) if needed > 0 else 0.0

    def add_xp(self, amount: int):
        old_level = self.level
        self.xp += amount

        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1

        self.last_level_up = self.level if self.level > old_level else None


    # -----------------------------------------------------
    # Serialization → JSON
    # -----------------------------------------------------
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "daily_quest": self.daily_quest,
            "inventory": self.inventory,        # dict saved cleanly
            "faction_id": self.faction_id,
            "lifetime_completed": self.lifetime_completed,
            "season_completed": self.season_completed,
            "xp": self.xp,
            "level": self.level,
            "badges": list(self.badges),
            "season_victories": list(self.season_victories),
            "title": self.title,
        }


    # -----------------------------------------------------
    # Load from JSON
    # -----------------------------------------------------
    @staticmethod
    def from_dict(data: dict):
        return PlayerState(
            user_id=data.get("user_id", 0),
            daily_quest=data.get("daily_quest", {}),
            inventory=data.get("inventory", {}),  # dict loads cleanly
            faction_id=data.get("faction_id"),
            lifetime_completed=data.get("lifetime_completed", 0),
            season_completed=data.get("season_completed", 0),
            xp=data.get("xp", 0),
            level=data.get("level", 1),
            badges=set(data.get("badges", [])),
            season_victories=set(data.get("season_victories", [])),
            title=data.get("title"),
        )
