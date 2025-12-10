from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import date


@dataclass
class InventoryItem:
    quest_id: str
    item_name: str
    collected: bool = True     # mainly for FETCH quests


class PlayerState:
    """
    Holds a user's daily quest, completion status, and inventory.
    Traditional class is used because behavior & methods will expand over time.
    """
    def __init__(self, user_id: int):
        self.user_id = str(user_id)
        self.daily_quest: Optional[Dict] = None
        self.inventory: List[InventoryItem] = []

    # ---------------------
    # DAILY QUEST FUNCTIONS
    # ---------------------
    def assign_daily_quest(self, quest_id: str):
        self.daily_quest = {
            "quest_id": quest_id,
            "assigned_date": date.today().isoformat(),
            "completed": False
        }

    def is_daily_quest(self, quest_id: str) -> bool:
        return (
            self.daily_quest is not None
            and self.daily_quest.get("quest_id") == quest_id
        )

    def has_completed_today(self) -> bool:
        if not self.daily_quest:
            return False
        return self.daily_quest.get("assigned_date") == date.today().isoformat() \
               and self.daily_quest.get("completed") is True

    def complete_daily_quest(self):
        if self.daily_quest:
            self.daily_quest["completed"] = True

    # ---------------------
    # INVENTORY FUNCTIONS
    # ---------------------
    def add_item(self, item: InventoryItem):
        self.inventory.append(item)

    def get_item_for_quest(self, quest_id: str) -> Optional[InventoryItem]:
        for item in self.inventory:
            if item.quest_id == quest_id:
                return item
        return None

    def remove_item(self, quest_id: str):
        self.inventory = [i for i in self.inventory if i.quest_id != quest_id]
