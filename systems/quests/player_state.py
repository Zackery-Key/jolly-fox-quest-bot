from dataclasses import dataclass, field

@dataclass
class InventoryItem:
    quest_id: str
    item_name: str
    collected: bool = True


@dataclass
class PlayerState:
    user_id: int
    daily_quest: dict = field(default_factory=dict)
    inventory: list = field(default_factory=list)

    # --------------------------
    # Convert PlayerState → dict
    # --------------------------
    def to_dict(self):
        return {
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

    # --------------------------
    # Convert dict → PlayerState
    # --------------------------
    @staticmethod
    def from_dict(data: dict):
        ps = PlayerState(
            user_id=data.get("user_id", 0),
            daily_quest=data.get("daily_quest", {})
        )

        inv_list = data.get("inventory", [])
        for item in inv_list:
            ps.inventory.append(
                InventoryItem(
                    quest_id=item["quest_id"],
                    item_name=item["item_name"],
                    collected=item.get("collected", True)
                )
            )

        return ps

    # --------------------------
    # Utilities
    # --------------------------
    def add_item(self, quest_id, item_name):
        self.inventory.append(InventoryItem(quest_id, item_name))
