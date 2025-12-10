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
            ]
        }

    @staticmethod
    def from_dict(data: dict):
        ps = PlayerState(
            user_id=data.get("user_id", 0),
            daily_quest=data.get("daily_quest", {})
        )

        for item in data.get("inventory", []):
            ps.inventory.append(
                InventoryItem(
                    quest_id=item["quest_id"],
                    item_name=item["item_name"],
                    collected=item.get("collected", True)
                )
            )

        return ps

    # --- inventory helpers for FETCH quests ---

    def add_item(self, quest_id: str, item_name: str):
        self.inventory.append(InventoryItem(quest_id=quest_id, item_name=item_name))

    def has_item_for_quest(self, quest_id: str) -> bool:
        return any(item.quest_id == quest_id for item in self.inventory)

    def consume_item_for_quest(self, quest_id: str) -> bool:
        for idx, item in enumerate(self.inventory):
            if item.quest_id == quest_id:
                del self.inventory[idx]
                return True
        return False
