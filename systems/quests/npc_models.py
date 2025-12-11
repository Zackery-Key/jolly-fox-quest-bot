from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class NPC:
    npc_id: str
    name: str
    avatar_url: str = ""

    # NEW optional expanded dialogue features
    greetings: List[str] = field(default_factory=list)
    idle_lines: List[str] = field(default_factory=list)
    quest_dialogue: Dict[str, List[str]] = field(default_factory=dict)

    # Legacy fallback support
    default_reply: str = ""

    # Optional flavor
    personality: str = ""

    def to_dict(self):
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "greetings": self.greetings,
            "idle_lines": self.idle_lines,
            "quest_dialogue": self.quest_dialogue,
            "default_reply": self.default_reply,
            "personality": self.personality
        }

    @staticmethod
    def from_dict(data: dict):
        return NPC(
            npc_id=data.get("npc_id"),
            name=data.get("name"),
            avatar_url=data.get("avatar_url", ""),

            greetings=data.get("greetings", []),
            idle_lines=data.get("idle_lines", []),
            quest_dialogue=data.get("quest_dialogue", {}),

            default_reply=data.get("default_reply", ""),
            personality=data.get("personality", "")
        )
