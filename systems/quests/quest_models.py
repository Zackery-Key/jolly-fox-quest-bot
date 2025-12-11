from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class QuestType(str, Enum):
    SKILL = "SKILL"
    SOCIAL = "SOCIAL"
    FETCH = "FETCH"
    TRAVEL = "TRAVEL"


@dataclass
class QuestTemplate:
    quest_id: str
    name: str
    type: QuestType
    points: int

    required_channel_id: Optional[int] = None
    source_channel_id: Optional[int] = None
    turnin_channel_id: Optional[int] = None

    dc: Optional[int] = None
    points_on_success: Optional[int] = None
    points_on_fail: Optional[int] = None

    npc_id: Optional[str] = None
    item_name: Optional[str] = None

    summary: str = ""
    details: str = ""

    tags: List[str] = field(default_factory=list)
    allowed_roles: List[int] = field(default_factory=list)

    # ---------------------------
    # SERIALIZATION
    # ---------------------------
    def to_dict(self):
        return {
            "quest_id": self.quest_id,
            "name": self.name,
            "type": self.type.value,
            "points": self.points,

            "required_channel_id": self.required_channel_id,
            "source_channel_id": self.source_channel_id,
            "turnin_channel_id": self.turnin_channel_id,

            "dc": self.dc,
            "points_on_success": self.points_on_success,
            "points_on_fail": self.points_on_fail,

            "npc_id": self.npc_id,
            "item_name": self.item_name,

            "summary": self.summary,
            "details": self.details,
            "tags": self.tags,
            "allowed_roles": self.allowed_roles,
        }

    @staticmethod
    def from_dict(data: dict):
        # Normalize allowed_roles into a list[int]
        raw_allowed = data.get("allowed_roles", []) or []
        allowed_roles: List[int] = []
        for r in raw_allowed:
            try:
                allowed_roles.append(int(r))
            except Exception:
                # Ignore junk values
                continue
            
        return QuestTemplate(
            quest_id=data.get("quest_id"),
            name=data.get("name"),
            type=QuestType(data.get("type")),
            points=data.get("points", 0),

            required_channel_id=data.get("required_channel_id"),
            source_channel_id=data.get("source_channel_id"),
            turnin_channel_id=data.get("turnin_channel_id"),

            dc=data.get("dc"),
            points_on_success=data.get("points_on_success"),
            points_on_fail=data.get("points_on_fail"),

            npc_id=data.get("npc_id"),
            item_name=data.get("item_name"),

            summary=data.get("summary", ""),
            details=data.get("details", ""),
            tags=data.get("tags", [])
        )
